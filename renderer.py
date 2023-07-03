# pylint: disable=line-too-long, wrong-import-order

import headscale, helper, pytz, os, yaml, logging, json
from flask              import Flask, Markup, render_template
from datetime           import datetime
from dateutil           import parser
from concurrent.futures import ALL_COMPLETED, wait
from flask_executor     import Executor

LOG_LEVEL = os.environ["LOG_LEVEL"].replace('"', '').upper()
# 初始化 Flask 应用程序和日志记录：
app = Flask(__name__, static_url_path="/static")
match LOG_LEVEL:
    case "DEBUG"   : app.logger.setLevel(logging.DEBUG)
    case "INFO"    : app.logger.setLevel(logging.INFO)
    case "WARNING" : app.logger.setLevel(logging.WARNING)
    case "ERROR"   : app.logger.setLevel(logging.ERROR)
    case "CRITICAL": app.logger.setLevel(logging.CRITICAL)
executor = Executor(app)

def render_overview():
    app.logger.info("正在渲染概览页面")
    url           = headscale.get_url()
    api_key       = headscale.get_api_key()

    timezone         = pytz.timezone(os.environ["TZ"] if os.environ["TZ"] else "UTC")
    local_time       = timezone.localize(datetime.now())
    
    # 概览页面只需从配置文件中读取静态信息并显示
    # 打开 config.yaml 并解析它
    config_file = ""
    try:    
        config_file = open("/etc/headscale/config.yml",  "r")
        app.logger.info("打开 /etc/headscale/config.yml")
    except: 
        config_file = open("/etc/headscale/config.yaml", "r")
        app.logger.info("打开 /etc/headscale/config.yaml")
    config_yaml = yaml.safe_load(config_file)

    # 获取并显示以下信息：
    # 服务器的机器、用户、预授权密钥、API 密钥到期时间、服务器版本
    
    # 获取所有机器：
    machines = headscale.get_machines(url, api_key)
    machines_count = len(machines["machines"])

    # 需要检查路由是否附加到活动机器上：
    # 问题:  https://github.com/iFargle/headscale-webui/issues/36 
    # 问题:  https://github.com/juanfont/headscale/issues/1228 

    # 获取所有路由：
    routes = headscale.get_routes(url,api_key)

    total_routes = 0
    for route in routes["routes"]:
        if int(route['machine']['id']) != 0: 
            total_routes += 1

    enabled_routes = 0
    for route in routes["routes"]:
        if route["enabled"] and route['advertised'] and int(route['machine']['id']) != 0: 
            enabled_routes += 1

    # 获取所有启用的出口路由的计数
    exits_count = 0
    exits_enabled_count = 0
    for route in routes["routes"]:
        if route['advertised'] and int(route['machine']['id']) != 0:
            if route["prefix"] == "0.0.0.0/0" or route["prefix"] == "::/0":
                exits_count +=1
                if route["enabled"]:
                    exits_enabled_count += 1

    # 获取用户和预授权密钥计数
    user_count        = 0
    usable_keys_count = 0
    users = headscale.get_users(url, api_key)
    for user in users["users"]:
        user_count +=1
        preauth_keys = headscale.get_preauth_keys(url, api_key, user["name"])
        for key in preauth_keys["preAuthKeys"]:
            expiration_parse = parser.parse(key["expiration"])
            key_expired = True if expiration_parse < local_time else False
            if key["reusable"] and not key_expired: usable_keys_count += 1
            if not key["reusable"] and not key["used"] and not key_expired: usable_keys_count += 1

    # 一般内容变量：
    ip_prefixes, server_url, disable_check_updates, ephemeral_node_inactivity_timeout, node_update_check_interval = "N/A", "N/A", "N/A", "N/A", "N/A"
    if "ip_prefixes"                       in config_yaml:  ip_prefixes                       = str(config_yaml["ip_prefixes"])
    if "server_url"                        in config_yaml:  server_url                        = str(config_yaml["server_url"])
    if "disable_check_updates"             in config_yaml:  disable_check_updates             = str(config_yaml["disable_check_updates"])
    if "ephemeral_node_inactivity_timeout" in config_yaml:  ephemeral_node_inactivity_timeout = str(config_yaml["ephemeral_node_inactivity_timeout"])
    if "node_update_check_interval"        in config_yaml:  node_update_check_interval        = str(config_yaml["node_update_check_interval"])

    # OIDC 内容变量：
    issuer, client_id, scope, use_expiry_from_token, expiry = "N/A", "N/A", "N/A", "N/A", "N/A"
    if "oidc" in config_yaml:
        if "issuer"                in config_yaml["oidc"] : issuer                = str(config_yaml["oidc"]["issuer"])                
        if "client_id"             in config_yaml["oidc"] : client_id             = str(config_yaml["oidc"]["client_id"])             
        if "scope"                 in config_yaml["oidc"] : scope                 = str(config_yaml["oidc"]["scope"])                 
        if "use_expiry_from_token" in config_yaml["oidc"] : use_expiry_from_token = str(config_yaml["oidc"]["use_expiry_from_token"]) 
        if "expiry"                in config_yaml["oidc"] : expiry                = str(config_yaml["oidc"]["expiry"])   

    # 嵌入的 DERP 服务器信息。
    enabled, region_id, region_code, region_name, stun_listen_addr = "N/A", "N/A", "N/A", "N/A", "N/A"
    if "derp" in config_yaml:
        if "server" in config_yaml["derp"] and config_yaml["derp"]["server"]["enabled"]:
            if "enabled"          in config_yaml["derp"]["server"]: enabled          = str(config_yaml["derp"]["server"]["enabled"])          
            if "region_id"        in config_yaml["derp"]["server"]: region_id        = str(config_yaml["derp"]["server"]["region_id"])        
            if "region_code"      in config_yaml["derp"]["server"]: region_code      = str(config_yaml["derp"]["server"]["region_code"])      
            if "region_name"      in config_yaml["derp"]["server"]: region_name      = str(config_yaml["derp"]["server"]["region_name"])      
            if "stun_listen_addr" in config_yaml["derp"]["server"]: stun_listen_addr = str(config_yaml["derp"]["server"]["stun_listen_addr"]) 
    
    nameservers, magic_dns, domains, base_domain = "N/A", "N/A", "N/A", "N/A"
    if "dns_config" in config_yaml:
        if "nameservers" in config_yaml["dns_config"]: nameservers = str(config_yaml["dns_config"]["nameservers"]) 
        if "magic_dns"   in config_yaml["dns_config"]: magic_dns   = str(config_yaml["dns_config"]["magic_dns"])   
        if "domains"     in config_yaml["dns_config"]: domains     = str(config_yaml["dns_config"]["domains"])     
        if "base_domain" in config_yaml["dns_config"]: base_domain = str(config_yaml["dns_config"]["base_domain"]) 

    # 开始组合内容
    overview_content = """
    <div class="row">
        <div class="col s1"></div>
        <div class="col s10">
            <ul class="collection with-header z-depth-1">
                <li class="collection-header"><h4>服务器统计信息</h4></li>
                <li class="collection-item"><div>已添加的机器数       <div class="secondary-content overview-page">"""+ str(machines_count)                               +"""</div></div></li>
                <li class="collection-item"><div>已添加的用户数          <div class="secondary-content overview-page">"""+ str(user_count)                                   +"""</div></div></li>
                <li class="collection-item"><div>可用的预授权密钥数  <div class="secondary-content overview-page">"""+ str(usable_keys_count)                            +"""</div></div></li>
                <li class="collection-item"><div>已启用/总路由数 <div class="secondary-content overview-page">"""+ str(enabled_routes) +"""/"""+str(total_routes)    +"""</div></div></li>
                <li class="collection-item"><div>已启用/总出口路由数  <div class="secondary-content overview-page">"""+ str(exits_enabled_count) +"""/"""+str(exits_count)+"""</div></div></li>
            </ul>
        </div>
        <div class="col s1"></div>
    </div>
    """
    general_content = """
    <div class="row">
        <div class="col s1"></div>
        <div class="col s10">
            <ul class="collection with-header z-depth-1">
                <li class="collection-header"><h4>常规信息</h4></li>
                <li class="collection-item"><div>IP 前缀                       <div class="secondary-content overview-page">"""+ ip_prefixes                       +"""</div></div></li>
                <li class="collection-item"><div>服务器 URL                        <div class="secondary-content overview-page">"""+ server_url                        +"""</div></div></li>
                <li class="collection-item"><div>禁用更新检查                  <div class="secondary-content overview-page">"""+ disable_check_updates             +"""</div></div></li>
                <li class="collection-item"><div>短暂节点不活动超时时间 <div class="secondary-content overview-page">"""+ ephemeral_node_inactivity_timeout +"""</div></div></li>
                <li class="collection-item"><div>节点更新检查间隔        <div class="secondary-content overview-page">"""+ node_update_check_interval        +"""</div></div></li>
            </ul>
        </div>
        <div class="col s1"></div>
    </div>
    """
    oidc_content = """
    <div class="row">
        <div class="col s1"></div>
        <div class="col s10">
            <ul class="collection with-header z-depth-1">
                <li class="collection-header"><h4>Headscale OIDC</h4></li>
                <li class="collection-item"><div>颁发者                <div class="secondary-content overview-page">"""+ issuer                +"""</div></div></li>
                <li class="collection-item"><div>客户端 ID             <div class="secondary-content overview-page">"""+ client_id             +"""</div></div></li>
                <li class="collection-item"><div>范围                 <div class="secondary-content overview-page">"""+ scope                 +"""</div></div></li>
                <li class="collection-item"><div>使用 OIDC 令牌过期时间 <div class="secondary-content overview-page">"""+ use_expiry_from_token +"""</div></div></li>
                <li class="collection-item"><div>过期时间                <div class="secondary-content overview-page">"""+ expiry                +"""</div></div></li>
            </ul>
        </div>
        <div class="col s1"></div>
    </div>
    """
    derp_content = """
    <div class="row">
        <div class="col s1"></div>
        <div class="col s10">
            <ul class="collection with-header z-depth-1">
                <li class="collection-header"><h4>嵌入的 DERP</h4></li>
                <li class="collection-item"><div>已启用     <div class="secondary-content overview-page">"""+ enabled          +"""</div></div></li>
                <li class="collection-item"><div>区域 ID   <div class="secondary-content overview-page">"""+ region_id        +"""</div></div></li>
                <li class="collection-item"><div>区域代码 <div class="secondary-content overview-page">"""+ region_code      +"""</div></div></li>
                <li class="collection-item"><div>区域名称 <div class="secondary-content overview-page">"""+ region_name      +"""</div></div></li>
                <li class="collection-item"><div>STUN 地址<div class="secondary-content overview-page">"""+ stun_listen_addr +"""</div></div></li>
            </ul>
        </div>
        <div class="col s1"></div>
    </div>
    """
    dns_content = """
    <div class="row">
        <div class="col s1"></div>
        <div class="col s10">
            <ul class="collection with-header z-depth-1">
                <li class="collection-header"><h4>DNS</h4></li>
                <li class="collection-item"><div>DNS Nameservers <div class="secondary-content overview-page">"""+  nameservers  +"""</div></div></li>
                <li class="collection-item"><div>MagicDNS        <div class="secondary-content overview-page">"""+  magic_dns    +"""</div></div></li>
                <li class="collection-item"><div>Search Domains  <div class="secondary-content overview-page">"""+  domains      +"""</div></div></li>
                <li class="collection-item"><div>Base Domain     <div class="secondary-content overview-page">"""+  base_domain  +"""</div></div></li>
            </ul>
        </div>
        <div class="col s1"></div>
    </div>
    """

    # 移除不需要的内容：
    # 如果 OIDC 不可用，则移除 OIDC：
    if "oidc" not in config_yaml: oidc_content = ""
    # 如果 DERP 不可用或未启用，则移除 DERP：
    if "derp" not in config_yaml:  derp_content = ""
    if "derp" in config_yaml:
        if "server" in config_yaml["derp"]:
            if str(config_yaml["derp"]["server"]["enabled"]) == "False":
                derp_content = ""

    # TODO:  
    #     是否存在自定义 DERP 服务器
    #         如果存在自定义 DERP 服务器，则从配置文件中获取文件位置。假设映射相同。
    #     是否启用了内置 DERP 服务器 
    #     IP 前缀
    #     DNS 配置

    if config_yaml["derp"]["paths"]: pass
    #   # 打开路径：
    #   derp_file = 
    #   config_file = open("/etc/headscale/config.yaml", "r")
    #   config_yaml = yaml.safe_load(config_file)
    #     ACME 配置（如果不为空）
    #     是否正在运行更新
    #     是否启用了指标（以及其监听地址）
    #     日志级别
    #     驱动 headscale 的数据库类型

    content = "<br>" + overview_content + general_content + derp_content + oidc_content + dns_content + ""
    return Markup(content)

def thread_machine_content(machine, machine_content, idx, all_routes, failover_pair_prefixes):
    # machine      = 传入的机器信息
    # machine_content = 写入内容的位置

    # app.logger.debug("机器信息")
    # app.logger.debug(str(machine))
    app.logger.debug("机器信息 =================")
    app.logger.debug("名称:  %s, ID:  %s, 用户:  %s, 名称: %s, ", str(machine["name"]), str(machine["id"]), str(machine["user"]["name"]), str(machine["givenName"]))

    url           = headscale.get_url()
    api_key       = headscale.get_api_key()

    # 设置当前时区和本地时间
    timezone   = pytz.timezone(os.environ["TZ"] if os.environ["TZ"] else "UTC")
    local_time = timezone.localize(datetime.now())

    # 获取机器的路由
    pulled_routes = headscale.get_machine_routes(url, api_key, machine["id"])
    routes = ""

    # 测试机器是否为出口节点：
    exit_route_found = False
    exit_route_enabled = False
    # 如果设备启用了故障转移路由（高可用路由）
    ha_enabled = False

    # 如果 "routes" 的长度为 NULL/0，则没有路由，启用或禁用：
    if len(pulled_routes["routes"]) > 0:
        advertised_routes = False

        # 首先，检查是否有任何已启用和已发布的路由
        # 如果是这样，我们将输出路由的集合项。否则，它将不会显示。
        for route in pulled_routes["routes"]:
            if route["advertised"]: 
                advertised_routes = True
        if advertised_routes:
            routes = """
                <li class="collection-item avatar">
                    <i class="material-icons circle">directions</i>
                    <span class="title">路由</span>
                    <p>
            """
            # app.logger.debug("Pulled Routes Dump:  "+str(pulled_routes))
            # app.logger.debug("All    Routes Dump:  "+str(all_routes))

            # 找到所有出口并将其 ID 放入 exit_routes 数组中
            exit_routes  = []
            exit_enabled_color = "red"
            exit_tooltip = "启用"
            exit_route_enabled = False
            
            for route in pulled_routes["routes"]:
                if route["prefix"] == "0.0.0.0/0" or route["prefix"] == "::/0":
                    exit_routes.append(route["id"])
                    exit_route_found = True
                    # 检查是否已启用：
                    if route["enabled"]:
                        exit_enabled_color = "green"
                        exit_tooltip       = '禁用'
                        exit_route_enabled = True
                    app.logger.debug("找到出口路由 ID:  "+str(exit_routes))
                    app.logger.debug("出口路由信息:  ID:  %s | 启用:  %s | exit_route_enabled:  %s / Found:  %s", str(route["id"]), str(route["enabled"]), str(exit_route_enabled), str(exit_route_found))

            # 显示出口路由的按钮：
            if exit_route_found:
                routes = routes+""" <p 
                    class='waves-effect waves-light btn-small """+exit_enabled_color+""" lighten-2 tooltipped'
                    data-position='top' data-tooltip='点击以""" + exit_tooltip + """'
                    id='"""+machine["id"]+"""-exit'
                    onclick="toggle_exit("""+exit_routes[0]+""", """+exit_routes[1]+""", '"""+machine["id"]+"""-exit', '"""+str(exit_route_enabled)+"""', 'machines')">
                    出口路由
                </p>
                """

            # 检查路由是否具有另一个已启用的相同路由。  
            # 将当前机器的所有路由与所有机器的所有路由进行比较...
            for route in pulled_routes["routes"]:
                # ... 对比所有路由 ...
                for route_info in all_routes["routes"]:
                    app.logger.debug("比较路由 %s 和 %s", str(route["prefix"]), str(route_info["prefix"]))
                    # ... 如果路由前缀匹配且不是出口节点 ...
                    if str(route_info["prefix"]) == str(route["prefix"]) and (route["prefix"] != "0.0.0.0/0" and route["prefix"] != "::/0"):
                        # 检查路由 ID 是否匹配。如果不匹配 ...
                        app.logger.debug("找到匹配项:  %s 和 %s", str(route["prefix"]), str(route_info["prefix"]))
                        if route_info["id"] != route["id"]:
                            app.logger.debug("路由 ID 不匹配。它们位于不同的节点上。")
                            # ... 检查路由前缀是否已在数组中 ...
                            if route["prefix"] not in failover_pair_prefixes:
                                # 如果不在数组中，则将其添加到数组中。
                                app.logger.info("找到新的故障转移对:  %s", str(route["prefix"]))
                                failover_pair_prefixes.append(str(route["prefix"]))
                            if route["enabled"] and route_info["enabled"]:
                                # 如果已经在数组中 ...
                                # 仅当两个路由都已启用时显示为故障转移：
                                app.logger.debug("两个路由都已启用。将其设置为故障转移 [%s] (%s) ", str(machine["name"]), str(route["prefix"]))
                                ha_enabled = True
                # 如果路由是出口节点并且已计入故障转移路由，则显示它。
                if route["prefix"] != "0.0.0.0/0" and route["prefix"] != "::/0" and route["prefix"] in failover_pair_prefixes:
                    route_enabled = "red"
                    route_tooltip = '启用'
                    color_index   = failover_pair_prefixes.index(str(route["prefix"]))
                    route_enabled_color = helper.get_color(color_index, "failover")
                    if route["enabled"]:
                        color_index   = failover_pair_prefixes.index(str(route["prefix"]))
                        route_enabled = helper.get_color(color_index, "failover")
                        route_tooltip = '禁用'
                    routes = routes+""" <p 
                        class='waves-effect waves-light btn-small """+route_enabled+""" lighten-2 tooltipped'
                        data-position='top' data-tooltip='点击以""" + route_tooltip + """ (故障转移对)'
                        id='"""+route['id']+"""'
                        onclick="toggle_failover_route("""+route['id']+""", '"""+str(route['enabled'])+"""', '"""+str(route_enabled_color)+"""')">
                        """+route['prefix']+"""
                    </p>
                    """
                    
            # 获取剩余的路由：
            for route in pulled_routes["routes"]:
                # 获取剩余的路由 - 没有出口或故障转移对
                if route["prefix"] != "0.0.0.0/0" and route["prefix"] != "::/0" and route["prefix"] not in failover_pair_prefixes:
                    app.logger.debug("路由：["+str(route['machine']['name'])+"] id："+str(route['id'])+" / 前缀："+str(route['prefix'])+" 是否启用："+str(route['enabled']))
                    route_enabled = "red"
                    route_tooltip = '启用'
                    if route["enabled"]:
                        route_enabled = "green"
                        route_tooltip = '禁用'
                    routes = routes+""" <p 
                        class='waves-effect waves-light btn-small """+route_enabled+""" lighten-2 tooltipped'
                        data-position='top' data-tooltip='点击以"""+route_tooltip+"""'
                        id='"""+route['id']+"""'
                        onclick="toggle_route("""+route['id']+""", '"""+str(route['enabled'])+"""', 'machines')">
                        """+route['prefix']+"""
                    </p>
                    """
            routes = routes+"</p></li>"

    # 获取机器标签
    tag_array = ""
    for tag in machine["forcedTags"]: 
        tag_array = tag_array+"{tag: '"+tag[4:]+"'}, "
    tags = """
        <li class="collection-item avatar">
            <i class="material-icons circle tooltipped" data-position="right" data-tooltip="刷新页面后，空格将被替换为破折号(-)">label</i>
            <span class="title">标签</span>
            <p><div style='margin: 0px' class='chips' id='"""+machine["id"]+"""-tags'></div></p>
        </li>
        <script>
            window.addEventListener('load', 
                function() { 
                    var instances = M.Chips.init ( 
                        document.getElementById('"""+machine['id']+"""-tags'),  ({
                            data:["""+tag_array+"""], 
                            onChipDelete() { delete_chip("""+machine["id"]+""", this.chipsData) }, 
                            onChipAdd()    { add_chip("""+machine["id"]+""",    this.chipsData) }
                        }) 
                    );
                }, false
            )
        </script>
        """

    # 获取机器IP地址
    machine_ips = "<ul>"
    for ip_address in machine["ipAddresses"]:
        machine_ips = machine_ips+"<li>"+ip_address+"</li>"
    machine_ips = machine_ips+"</ul>"

    # 格式化日期以便易读
    last_seen_parse   = parser.parse(machine["lastSeen"])
    last_seen_local   = last_seen_parse.astimezone(timezone)
    last_seen_delta   = local_time - last_seen_local
    last_seen_print   = helper.pretty_print_duration(last_seen_delta)
    last_seen_time    = str(last_seen_local.strftime('%A %m/%d/%Y, %H:%M:%S'))+" "+str(timezone)+" ("+str(last_seen_print)+")"
    
    last_update_parse = local_time if machine["lastSuccessfulUpdate"] is None else parser.parse(machine["lastSuccessfulUpdate"])
    last_update_local = last_update_parse.astimezone(timezone)
    last_update_delta = local_time - last_update_local
    last_update_print = helper.pretty_print_duration(last_update_delta)
    last_update_time  = str(last_update_local.strftime('%A %m/%d/%Y, %H:%M:%S'))+" "+str(timezone)+" ("+str(last_update_print)+")"

    created_parse     = parser.parse(machine["createdAt"])
    created_local     = created_parse.astimezone(timezone)
    created_delta     = local_time - created_local
    created_print     = helper.pretty_print_duration(created_delta)
    created_time      = str(created_local.strftime('%A %m/%d/%Y, %H:%M:%S'))+" "+str(timezone)+" ("+str(created_print)+")"

    # 如果没有过期日期，不需要进行任何计算：
    if machine["expiry"] != "0001-01-01T00:00:00Z":
        expiry_parse     = parser.parse(machine["expiry"])
        expiry_local     = expiry_parse.astimezone(timezone)
        expiry_delta     = expiry_local - local_time
        expiry_print     = helper.pretty_print_duration(expiry_delta, "expiry")
        if str(expiry_local.strftime('%Y')) in ("0001",  "9999", "0000"):
            expiry_time  = "没有过期日期。"
        elif int(expiry_local.strftime('%Y')) > int(expiry_local.strftime('%Y'))+2:
            expiry_time  = str(expiry_local.strftime('%m/%Y'))+" "+str(timezone)+" ("+str(expiry_print)+")"
        else: 
            expiry_time  = str(expiry_local.strftime('%A %m/%d/%Y, %H:%M:%S'))+" "+str(timezone)+" ("+str(expiry_print)+")"

        expiring_soon = True if int(expiry_delta.days) < 14 and int(expiry_delta.days) > 0 else False
        app.logger.debug("机器："+machine["name"]+" 过期时间："+str(expiry_local.strftime('%Y'))+" / "+str(expiry_delta.days))
    else:
        expiry_time  = "没有过期日期。"
        expiring_soon = False
        app.logger.debug("机器："+machine["name"]+" 没有过期日期")


    # 获取PreAuth密钥的前10个字符：
    if machine["preAuthKey"]:
        preauth_key = str(machine["preAuthKey"]["key"])[0:10]
    else: preauth_key = "无"

    # 设置状态和用户徽章颜色：
    text_color = helper.text_color_duration(last_seen_delta)
    user_color = helper.get_color(int(machine["user"]["id"]))

    # 生成各种徽章：
    status_badge      = "<i class='material-icons left tooltipped " + text_color + "' data-position='top' data-tooltip='最后在线时间："+last_seen_print+"' id='"+machine["id"]+"-status'>fiber_manual_record</i>"
    user_badge        = "<span class='badge ipinfo " + user_color + " white-text hide-on-small-only' id='"+machine["id"]+"-ns-badge'>"+machine["user"]["name"]+"</span>"
    exit_node_badge   = "" if not exit_route_enabled else "<span class='badge grey white-text text-lighten-4 tooltipped' data-position='left' data-tooltip='该机器启用了出口路由。'>出口</span>"
    ha_route_badge    = "" if not ha_enabled         else "<span class='badge blue-grey white-text text-lighten-4 tooltipped' data-position='left' data-tooltip='该机器启用了高可用性（故障转移）路由。'>HA</span>"
    expiration_badge  = "" if not expiring_soon      else "<span class='badge red white-text text-lighten-4 tooltipped' data-position='left' data-tooltip='该机器即将过期。'>即将过期！</span>"

    machine_content[idx] = (str(render_template(
        'machines_card.html', 
        given_name        = machine["givenName"],
        machine_id        = machine["id"],
        hostname          = machine["name"],
        ns_name           = machine["user"]["name"],
        ns_id             = machine["user"]["id"],
        ns_created        = machine["user"]["createdAt"],
        last_seen         = str(last_seen_print),
        last_update       = str(last_update_print),
        machine_ips       = Markup(machine_ips),
        advertised_routes = Markup(routes),
        exit_node_badge   = Markup(exit_node_badge),
        ha_route_badge    = Markup(ha_route_badge),
        status_badge      = Markup(status_badge),
        user_badge        = Markup(user_badge),
        last_update_time  = str(last_update_time),
        last_seen_time    = str(last_seen_time),
        created_time      = str(created_time),
        expiry_time       = str(expiry_time),
        preauth_key       = str(preauth_key),
        expiration_badge  = Markup(expiration_badge),
        machine_tags      = Markup(tags),
        taglist           = machine["forcedTags"]
    )))
    app.logger.info("完成机器 "+machine["givenName"]+" 索引 "+str(idx)+" 的线程")

def render_machines_cards():
    app.logger.info("正在渲染机器卡片")
    url           = headscale.get_url()
    api_key       = headscale.get_api_key()
    machines_list = headscale.get_machines(url, api_key)

    #########################################
    # 线程化整个过程。  
    num_threads = len(machines_list["machines"])
    iterable = []
    machine_content = {}
    failover_pair_prefixes = []
    for i in range (0, num_threads):
        app.logger.debug("添加迭代项："+str(i))
        iterable.append(i)
    # Flask-Executor 方法：

    # 获取所有路由
    all_routes = headscale.get_routes(url, api_key)
    # app.logger.debug("找到的所有路由")
    # app.logger.debug(str(all_routes))

    if LOG_LEVEL == "DEBUG":
        # DEBUG: 逐个进行循环：
        for idx in iterable: thread_machine_content(machines_list["machines"][idx], machine_content, idx, all_routes, failover_pair_prefixes)
    else:
        app.logger.info("开始线程")
        futures = [executor.submit(thread_machine_content, machines_list["machines"][idx], machine_content, idx, all_routes, failover_pair_prefixes) for idx in iterable]
        # 等待执行器完成所有任务：
        wait(futures, return_when=ALL_COMPLETED)
        app.logger.info("完成线程")

    # 按机器ID对内容进行排序：
    sorted_machines = {key: val for key, val in sorted(machine_content.items(), key = lambda ele: ele[0])}

    content = "<ul class='collapsible expandable'>"
    # 打印内容

    for index in range(0, num_threads):
        content = content+str(sorted_machines[index])

    content = content+"</ul>"

    return Markup(content)

def render_users_cards():
    app.logger.info("正在渲染用户卡片")
    url       = headscale.get_url()
    api_key   = headscale.get_api_key()
    user_list = headscale.get_users(url, api_key)

    content = "<ul class='collapsible expandable'>"
    for user in user_list["users"]:
        # 获取用户中的所有PreAuth密钥，并仅在存在时显示：
        preauth_keys_collection = build_preauth_key_table(user["name"])

        # 设置用户徽章颜色：
        user_color = helper.get_color(int(user["id"]), "text")

        # 生成各种徽章：
        status_badge      = "<i class='material-icons left "+user_color+"' id='"+user["id"]+"-status'>fiber_manual_record</i>"

        content = content + render_template(
            'users_card.html', 
            status_badge            = Markup(status_badge),
            user_name               = user["name"],
            user_id                 = user["id"],
            preauth_keys_collection = Markup(preauth_keys_collection)
        ) 
    content = content+"</ul>"
    return Markup(content)

def build_preauth_key_table(user_name):
    app.logger.info("正在构建用户 "+str(user_name)+" 的PreAuth密钥表")
    url            = headscale.get_url()
    api_key        = headscale.get_api_key()

    preauth_keys = headscale.get_preauth_keys(url, api_key, user_name)
    preauth_keys_collection = """<li class="collection-item avatar">
            <span
                class='badge grey lighten-2 btn-small' 
                onclick='toggle_expired()'
            >切换已过期</span>
            <span 
                href="#card_modal" 
                class='badge grey lighten-2 btn-small modal-trigger' 
                onclick="load_modal_add_preauth_key('"""+user_name+"""')"
            >添加PreAuth密钥</span>
            <i class="material-icons circle">vpn_key</i>
            <span class="title">PreAuth密钥</span>
            """
    if len(preauth_keys["preAuthKeys"]) == 0: preauth_keys_collection += "<p>此用户未定义密钥</p>"
    if len(preauth_keys["preAuthKeys"]) > 0:
        preauth_keys_collection += """
                <table class="responsive-table striped" id='"""+user_name+"""-preauthkey-table'>
                    <thead>
                        <tr>
                            <td>ID</td>
                            <td class='tooltipped' data-tooltip='点击密钥前缀以将其复制到剪贴板'>密钥前缀</td>
                            <td><center>可重用</center></td>
                            <td><center>已使用</center></td>
                            <td><center>短暂</center></td>
                            <td><center>可用</center></td>
                            <td><center>操作</center></td>
                        </tr>
                    </thead>
                """
    for key in preauth_keys["preAuthKeys"]:
        # 获取密钥到期日期并与当前时间进行比较以检查是否已过期：
        # 设置当前时区和本地时间
        timezone         = pytz.timezone(os.environ["TZ"] if os.environ["TZ"] else "UTC")
        local_time       = timezone.localize(datetime.now())
        expiration_parse = parser.parse(key["expiration"])
        key_expired = True if expiration_parse < local_time else False
        expiration_time  = str(expiration_parse.strftime('%A %m/%d/%Y, %H:%M:%S'))+" "+str(timezone)

        key_usable = False
        if key["reusable"] and not key_expired: key_usable = True
        if not key["reusable"] and not key["used"] and not key_expired: key_usable = True
        
        # 用于javascript函数查找以切换隐藏功能的类
        hide_expired = "expired-row" if not key_usable else ""

        btn_reusable  = "<i class='pulse material-icons tiny blue-text text-darken-1'>fiber_manual_record</i>"   if key["reusable"]  else ""
        btn_ephemeral = "<i class='pulse material-icons tiny red-text text-darken-1'>fiber_manual_record</i>"    if key["ephemeral"] else ""
        btn_used      = "<i class='pulse material-icons tiny yellow-text text-darken-1'>fiber_manual_record</i>" if key["used"]      else ""
        btn_usable    = "<i class='pulse material-icons tiny green-text text-darken-1'>fiber_manual_record</i>"  if key_usable       else ""

        # 其他按钮：
        btn_delete    = "<span href='#card_modal' data-tooltip='使此PreAuth密钥过期' class='btn-small modal-trigger badge tooltipped white-text red' onclick='load_modal_expire_preauth_key(\""+user_name+"\", \""+str(key["key"])+"\")'>过期</span>" if key_usable else ""
        tooltip_data  = "到期时间："+expiration_time

        # TR ID将类似于“1-albert-tr”
        preauth_keys_collection = preauth_keys_collection+"""
            <tr id='"""+key["id"]+"""-"""+user_name+"""-tr' class='"""+hide_expired+"""'>
                <td>"""+str(key["id"])+"""</td>
                <td  onclick=copy_preauth_key('"""+str(key["key"])+"""') class='tooltipped' data-tooltip='"""+tooltip_data+"""'>"""+str(key["key"])[0:10]+"""</td>
                <td><center>"""+btn_reusable+"""</center></td>
                <td><center>"""+btn_used+"""</center></td>
                <td><center>"""+btn_ephemeral+"""</center></td>
                <td><center>"""+btn_usable+"""</center></td>
                <td><center>"""+btn_delete+"""</center></td>
            </tr>
        """

    preauth_keys_collection = preauth_keys_collection+"""</table>
        </li>
        """
    return preauth_keys_collection

def oidc_nav_dropdown(user_name, email_address, name):
    app.logger.info("启用了OIDC。正在构建OIDC导航下拉菜单")
    html_payload = """
        <!-- OIDC下拉菜单结构 -->
        <ul id="dropdown1" class="dropdown-content dropdown-oidc">
            <ul class="collection dropdown-oidc-collection">
                <li class="collection-item dropdown-oidc-avatar avatar">
                    <i class="material-icons circle">email</i>
                    <span class="dropdown-oidc-title title">电子邮件</span>
                    <p>"""+email_address+"""</p>
                </li>
                <li class="collection-item dropdown-oidc-avatar avatar">
                    <i class="material-icons circle">person_outline</i>
                    <span class="dropdown-oidc-title title">用户名</span>
                    <p>"""+user_name+"""</p>
                </li>
            </ul>
        <li class="divider"></li>
            <li><a href="logout"><i class="material-icons left">exit_to_app</i> 登出</a></li>
        </ul>
        <li>
            <a class="dropdown-trigger" href="#!" data-target="dropdown1">
                """+name+""" <i class="material-icons right">account_circle</i>
            </a>
        </li>
    """
    return Markup(html_payload)

def oidc_nav_mobile(user_name, email_address, name):
    html_payload = """
         <li><hr><a href="logout"><i class="material-icons left">exit_to_app</i>登出</a></li>
    """
    return Markup(html_payload)

def render_search():
    html_payload = """
    <li role="menu-item" class="tooltipped" data-position="bottom" data-tooltip="搜索" onclick="show_search()">
        <a href="#"><i class="material-icons">search</i></a>
    </li>
    """
    return Markup(html_payload)

def render_routes():
    app.logger.info("正在渲染路由页面")
    url           = headscale.get_url()
    api_key       = headscale.get_api_key()
    all_routes    = headscale.get_routes(url, api_key)

    # 如果没有路由，直接退出：
    if len(all_routes) == 0: return Markup("<br><br><br><center>没有要显示的路由！</center>")
    # 获取所有路由的ID列表以进行迭代：
    all_routes_id_list = []
    for route in all_routes["routes"]:
        all_routes_id_list.append(route["id"])
        if route["machine"]["name"]:
            app.logger.info("找到路由 %s / 机器：%s", str(route["id"]), route["machine"]["name"])
        else: 
            app.logger.info("路由id %s没有关联的机器。", str(route["id"]))


    route_content    = ""
    failover_content = ""
    exit_content     = ""

    route_title='<span class="card-title">路由</span>'
    failover_title='<span class="card-title">故障转移路由</span>'
    exit_title='<span class="card-title">出口路由</span>'

    markup_pre = """
    <div class="row">
        <div class="col m1"></div>
        <div class="col s12 m10">
            <div class="card">
                <div class="card-content">
    """
    markup_post = """ 
                </div>
            </div>
        </div>
        <div class="col m1"></div>
    </div>
    """

    ##############################################################################################
    # 步骤1：获取所有非出口和非故障转移路由：
    route_content = markup_pre+route_title
    route_content += """<p><table>
    <thead>
        <tr>
            <th>ID       </th>
            <th>机器     </th>
            <th>路由     </th>
            <th width="60px">启用</th>
        </tr>
    </thead>
    <tbody>
    """
    for route in all_routes["routes"]:
        # 获取相关信息：
        route_id    = route["id"]
        machine     = route["machine"]["givenName"]
        prefix      = route["prefix"]
        is_enabled  = route["enabled"]
        is_primary  = route["isPrimary"]
        is_failover = False
        is_exit     = False 

        enabled  = "<i id='"+route["id"]+"' onclick='toggle_route("+route["id"]+", \"True\", \"routes\")'  class='material-icons green-text text-lighten-2 tooltipped' data-tooltip='点击以禁用'>fiber_manual_record</i>"
        disabled = "<i id='"+route["id"]+"' onclick='toggle_route("+route["id"]+", \"False\", \"routes\")' class='material-icons red-text text-lighten-2 tooltipped' data-tooltip='点击以启用' >fiber_manual_record</i>"

        # 设置显示：
        enabled_display  = disabled

        if is_enabled:  enabled_display = enabled
        # 检查前缀是否为出口路由：
        if prefix == "0.0.0.0/0" or prefix == "::/0":  is_exit = True
        # 检查前缀是否是故障转移对的一部分：
        for route_check in all_routes["routes"]:
            if not is_exit:
                if route["prefix"] == route_check["prefix"]:
                    if route["id"] != route_check["id"]:
                        is_failover = True

        if not is_exit and not is_failover and machine != "":
        # 为所有非出口路由构建一个简单的表格：
            route_content += """
            <tr>
                <td>"""+str(route_id         )+"""</td>
                <td>"""+str(machine          )+"""</td>
                <td>"""+str(prefix           )+"""</td>
                <td><center>"""+str(enabled_display  )+"""</center></td>
            </tr>
            """
    route_content += "</tbody></table></p>"+markup_post

    ##############################################################################################
    # 步骤2：仅获取所有故障转移路由。每个故障转移前缀添加一个单独的表格
    failover_route_prefix = []
    failover_available = False

    for route in all_routes["routes"]:
        # 获取所有路由的前缀列表...
        for route_check in all_routes["routes"]:
            # ...不是出口路由的...
            if route["prefix"] !="0.0.0.0/0" and route["prefix"] != "::/0":
                # 如果当前路由与任何其他路由的前缀匹配...
                if route["prefix"] == route_check["prefix"]:
                    # 并且路由ID不同...
                    if route["id"] != route_check["id"]:
                        # ...并且前缀尚未在列表中...
                        if route["prefix"] not in failover_route_prefix:
                            # 将前缀添加到failover_route_prefix列表中
                            failover_route_prefix.append(route["prefix"])
                            failover_available = True

    if failover_available:
        # 设置显示代码：
        enabled  = "<i class='material-icons green-text text-lighten-2'>fiber_manual_record</i>"
        disabled = "<i class='material-icons red-text text-lighten-2'>fiber_manual_record</i>"

        failover_content = markup_pre+failover_title
        # 构建故障转移路由的显示：
        for route_prefix in failover_route_prefix:
            # 获取与route_prefix关联的所有路由ID：
            route_id_list = []
            for route in all_routes["routes"]:
                if route["prefix"] == route_prefix:
                    route_id_list.append(route["id"])

            # 设置显示代码：
            failover_enabled  = "<i id='"+str(route_prefix)+"' class='material-icons small left green-text text-lighten-2'>fiber_manual_record</i>"
            failover_disabled = "<i id='"+str(route_prefix)+"' class='material-icons small left red-text text-lighten-2'>fiber_manual_record</i>"

            failover_display = failover_disabled
            for route_id in route_id_list:
                # 获取路由的索引：
                current_route_index = all_routes_id_list.index(route_id)
                if all_routes["routes"][current_route_index]["enabled"]: failover_display = failover_enabled


            # 获取与前缀关联的所有route_id：
            failover_content += """<p>
            <h5>"""+failover_display+"""</h5><h5>"""+str(route_prefix)+"""</h5>
            <table>
                <thead>
                    <tr>
                        <th>机器</th>
                        <th width="60px">启用</th>
                        <th width="60px">主要</th>
                    </tr>
                </thead>
                <tbody>
            """

            # 构建显示：
            for route_id in route_id_list:
                idx = all_routes_id_list.index(route_id)

                machine    = all_routes["routes"][idx]["machine"]["givenName"]
                machine_id = all_routes["routes"][idx]["machine"]["id"]
                is_primary = all_routes["routes"][idx]["isPrimary"]
                is_enabled = all_routes["routes"][idx]["enabled"]

                payload = []
                for item in route_id_list: payload.append(int(item))
                 
                app.logger.debug("[%s] 机器：[%s]  %s : %s / %s", str(route_id), str(machine_id), str(machine), str(is_enabled), str(is_primary))
                app.logger.debug(str(all_routes["routes"][idx]))

                # 设置显示代码：
                enabled_display_enabled  = "<i id='"+str(route_id)+"' onclick='toggle_failover_route_routespage("+str(route_id)+", \"True\", \""+str(route_prefix)+"\", "+str(payload)+")'  class='material-icons green-text text-lighten-2 tooltipped' data-tooltip='点击以禁用'>fiber_manual_record</i>"
                enabled_display_disabled = "<i id='"+str(route_id)+"' onclick='toggle_failover_route_routespage("+str(route_id)+", \"False\", \""+str(route_prefix)+"\", "+str(payload)+")' class='material-icons red-text text-lighten-2 tooltipped' data-tooltip='点击以启用'>fiber_manual_record</i>"
                primary_display_enabled  = "<i id='"+str(route_id)+"-primary' class='material-icons green-text text-lighten-2'>fiber_manual_record</i>"
                primary_display_disabled = "<i id='"+str(route_id)+"-primary' class='material-icons red-text text-lighten-2'>fiber_manual_record</i>"
                
                # 设置显示：
                enabled_display = enabled_display_enabled if is_enabled else enabled_display_disabled
                primary_display = primary_display_enabled if is_primary else primary_display_disabled

                # 为所有非出口路由构建一个简单的表格：
                failover_content += """
                    <tr>
                        <td>"""+str(machine)+"""</td>
                        <td><center>"""+str(enabled_display)+"""</center></td>
                        <td><center>"""+str(primary_display)+"""</center></td>
                    </tr>
                    """
            failover_content += "</tbody></table></p>"
        failover_content += markup_post

    ##############################################################################################
    # 步骤3：仅获取出口节点：
    exit_node_list = []
    # 获取具有出口路由的节点列表：
    for route in all_routes["routes"]:
        # 对于每个找到的出口路由，将机器名称存储在数组中：
        if route["prefix"] == "0.0.0.0/0" or route["prefix"] == "::/0":
            if route["machine"]["givenName"] not in exit_node_list: 
                exit_node_list.append(route["machine"]["givenName"])

    # 出口节点显示构建：
    # 按机器而不是按路由显示
    exit_content = markup_pre+exit_title
    exit_content += """<p><table>
    <thead>
        <tr>
            <th>机器</th>
            <th>启用</th>
        </tr>
    </thead>
    <tbody>
    """
    # 获取列表中每个节点的出口路由ID： 
    for node in exit_node_list:
        node_exit_route_ids = []
        exit_enabled = False
        exit_available = False
        machine_id = 0
        for route in all_routes["routes"]:
            if route["prefix"] == "0.0.0.0/0" or route["prefix"] == "::/0":
                if route["machine"]["givenName"] == node:
                    node_exit_route_ids.append(route["id"])
                    machine_id = route["machine"]["id"]
                    exit_available = True
                    if route["enabled"]:
                        exit_enabled = True

        if exit_available:
            # 设置显示代码：
            enabled  = "<i id='"+machine_id+"-exit' onclick='toggle_exit("+node_exit_route_ids[0]+", "+node_exit_route_ids[1]+", \""+machine_id+"-exit\", \"True\",  \"routes\")' class='material-icons green-text text-lighten-2 tooltipped' data-tooltip='点击以禁用'>fiber_manual_record</i>"
            disabled = "<i id='"+machine_id+"-exit' onclick='toggle_exit("+node_exit_route_ids[0]+", "+node_exit_route_ids[1]+", \""+machine_id+"-exit\", \"False\", \"routes\")' class='material-icons red-text text-lighten-2 tooltipped' data-tooltip='点击以启用' >fiber_manual_record</i>"
            # 设置显示：
            enabled_display = enabled if exit_enabled else disabled

            exit_content += """
            <tr>
                <td>"""+str(node)+"""</td>
                <td width="60px"><center>"""+str(enabled_display)+"""</center></td>
            </tr>
            """
    exit_content += "</tbody></table></p>"+markup_post

    content = route_content + failover_content + exit_content
    return Markup(content)
