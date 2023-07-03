# pylint: disable=wrong-import-order

import os, headscale, requests, logging
from flask import Flask

LOG_LEVEL = os.environ["LOG_LEVEL"].replace('"', '').upper()
DATA_DIRECTORY = os.environ["DATA_DIRECTORY"].replace('"', '') if os.environ["DATA_DIRECTORY"] else "/data"
# 初始化 Flask 应用和日志记录：
app = Flask(__name__, static_url_path="/static")
match LOG_LEVEL:
    case "DEBUG"   : app.logger.setLevel(logging.DEBUG)
    case "INFO"    : app.logger.setLevel(logging.INFO)
    case "WARNING" : app.logger.setLevel(logging.WARNING)
    case "ERROR"   : app.logger.setLevel(logging.ERROR)
    case "CRITICAL": app.logger.setLevel(logging.CRITICAL)

def pretty_print_duration(duration, delta_type=""):
    """ 以人类可读的格式打印持续时间 """
    days, seconds = duration.days, duration.seconds
    hours = (days * 24 + seconds // 3600)
    mins  = (seconds % 3600) // 60
    secs  = seconds % 60
    if delta_type == "expiry":
        if days  > 730: return "超过两年后"
        if days  > 365: return "超过一年后"
        if days  > 0  : return "在"+ str(days ) + "天后"     if days  >  1 else "在"+ str(days ) + "天后"
        if hours > 0  : return "在"+ str(hours) + "小时后"    if hours >  1 else "在"+ str(hours) + "小时后"
        if mins  > 0  : return "在"+ str(mins ) + "分钟后"  if mins  >  1 else "在"+ str(mins ) + "分钟后"
        return "在"+ str(secs ) + "秒后"     if secs  >= 1 or secs == 0 else "在"+ str(secs ) + "秒后"
    if days  > 730: return "超过两年前"
    if days  > 365: return "超过一年前"
    if days  > 0  : return str(days ) + "天前"     if days  >  1 else str(days ) + "天前"
    if hours > 0  : return str(hours) + "小时前"    if hours >  1 else str(hours) + "小时前"
    if mins  > 0  : return str(mins ) + "分钟前"  if mins  >  1 else str(mins ) + "分钟前"
    return str(secs ) + "秒前"     if secs  >= 1 or secs == 0 else str(secs ) + "秒前"

def text_color_duration(duration):
    """ 根据持续时间设置颜色（以秒为单位） """

    days, seconds = duration.days, duration.seconds
    hours = (days * 24 + seconds // 3600)
    mins  = ((seconds % 3600) // 60)
    secs  = (seconds % 60)
    if days  > 30: return "grey-text                      "
    if days  > 14: return "red-text         text-darken-2 "
    if days  >  5: return "deep-orange-text text-lighten-1"
    if days  >  1: return "deep-orange-text text-lighten-1"
    if hours > 12: return "orange-text                    "
    if hours >  1: return "orange-text      text-lighten-2"
    if hours == 1: return "yellow-text                    "
    if mins  > 15: return "yellow-text      text-lighten-2"
    if mins  >  5: return "green-text       text-lighten-3"
    if secs  > 30: return "green-text       text-lighten-2"
    return "green-text                     "

def key_check():
    """ 检查 Headscale API 密钥的有效性，并在接近到期时进行续订 """
    api_key    = headscale.get_api_key()
    url        = headscale.get_url()

    # 测试 API 密钥。如果测试失败，则返回失败。
    # 即，如果 headscale 返回未经授权，则失败：
    app.logger.info("测试 API 密钥的有效性。")
    status = headscale.test_api_key(url, api_key)
    if status != 200:
        app.logger.info("从 Headscale 得到非 200 响应。测试失败（响应：%i）", status)
        return False
    else:
        app.logger.info("密钥检查通过。")
        # 检查密钥是否需要续订
        headscale.renew_api_key(url, api_key)
        return True

def get_color(import_id, item_type = ""):
    """ 为用户/命名空间设置颜色 """
    # 定义颜色...从这个数量开始看起来不错
    if item_type == "failover":
        colors = [
            "teal        lighten-1",
            "blue        lighten-1",
            "blue-grey   lighten-1",
            "indigo      lighten-2",
            "brown       lighten-1",
            "grey        lighten-1",
            "indigo      lighten-2",
            "deep-orange lighten-1",
            "yellow      lighten-2",
            "purple      lighten-2",
        ]
        index = import_id % len(colors)
        return colors[index]
    if item_type == "text":
        colors = [
            "red-text         text-lighten-1",
            "teal-text        text-lighten-1",
            "blue-text        text-lighten-1",
            "blue-grey-text   text-lighten-1",
            "indigo-text      text-lighten-2",
            "green-text       text-lighten-1",
            "deep-orange-text text-lighten-1",
            "yellow-text      text-lighten-2",
            "purple-text      text-lighten-2",
            "indigo-text      text-lighten-2",
            "brown-text       text-lighten-1",
            "grey-text        text-lighten-1",
        ]
        index = import_id % len(colors)
        return colors[index]
    colors = [
        "red         lighten-1",
        "teal        lighten-1",
        "blue        lighten-1",
        "blue-grey   lighten-1",
        "indigo      lighten-2",
        "green       lighten-1",
        "deep-orange lighten-1",
        "yellow      lighten-2",
        "purple      lighten-2",
        "indigo      lighten-2",
        "brown       lighten-1",
        "grey        lighten-1",
    ]
    index = import_id % len(colors)
    return colors[index]

def format_message(error_type, title, message):
    """ 定义通用的错误/警告/信息消息的格式 """
    content = """
        <ul class="collection">
        <li class="collection-item avatar">
    """

    match error_type.lower():
        case "warning":
            icon  = """<i class="material-icons circle yellow">priority_high</i>"""
            title = """<span class="title">警告 - """+title+"""</span>"""
        case "success":
            icon  = """<i class="material-icons circle green">check</i>"""
            title = """<span class="title">成功 - """+title+"""</span>"""
        case "error":
            icon  = """<i class="material-icons circle red">warning</i>"""
            title = """<span class="title">错误 - """+title+"""</span>"""
        case "information":
            icon  = """<i class="material-icons circle grey">help</i>"""
            title = """<span class="title">信息 - """+title+"""</span>"""

    content = content+icon+title+message
    content = content+"""
            </li>
        </ul>
    """

    return content

def access_checks():
    """ 在每次页面加载之前检查各种项目，以确保权限正确 """
    url = headscale.get_url()

    # 如果发生故障，返回错误消息。
    # 为每个故障生成一个格式化的错误消息。
    checks_passed   = True # 默认为 true。当任何检查失败时设置为 false。
    data_readable   = False # 检查 DATA_DIRECTORY 的 R 权限
    data_writable   = False # 检查 DATA_DIRECTORY 的 W 权限
    data_executable = False # 执行目录允许文件访问
    file_readable   = False # 检查 DATA_DIRECTORY/key.txt 的 R 权限
    file_writable   = False # 检查 DATA_DIRECTORY/key.txt 的 W 权限
    file_exists     = False # 检查 DATA_DIRECTORY/key.txt 是否存在
    config_readable = False # 检查 headscale 配置文件是否可读


    # 检查 1：检查 Headscale 服务器是否可达：
    server_reachable = False
    response = requests.get(str(url)+"/health")
    if response.status_code == 200:
        server_reachable = True
    else:
        checks_passed = False
        app.logger.critical("Headscale URL：响应 200：失败")

    # 检查：DATA_DIRECTORY 对于 1000:1000 是 rwx 的：
    if os.access(DATA_DIRECTORY, os.R_OK):  data_readable = True
    else:
        app.logger.critical(f"{DATA_DIRECTORY} 读取：失败")
        checks_passed = False
    if os.access(DATA_DIRECTORY, os.W_OK):  data_writable = True
    else:
        app.logger.critical(f"{DATA_DIRECTORY} 写入：失败")
        checks_passed = False
    if os.access(DATA_DIRECTORY, os.X_OK):  data_executable = True
    else:
        app.logger.critical(f"{DATA_DIRECTORY} 执行：失败")
        checks_passed = False

    # 检查：DATA_DIRECTORY/key.txt 存在且可读写：
    if os.access(os.path.join(DATA_DIRECTORY, "key.txt"), os.F_OK):
        file_exists = True
        if os.access(os.path.join(DATA_DIRECTORY, "key.txt"), os.R_OK): file_readable = True
        else:
            app.logger.critical(f"{os.path.join(DATA_DIRECTORY, 'key.txt')} 读取：失败")
            checks_passed = False
        if os.access(os.path.join(DATA_DIRECTORY, "key.txt"), os.W_OK):  file_writable = True
        else:
            app.logger.critical(f"{os.path.join(DATA_DIRECTORY, 'key.txt')} 写入：失败")
            checks_passed = False
    else: app.logger.error(f"{os.path.join(DATA_DIRECTORY, 'key.txt')} 存在：失败 - 无错误")

    # 检查：/etc/headscale/config.yaml 可读：
    if os.access('/etc/headscale/config.yaml', os.R_OK):  config_readable = True
    elif os.access('/etc/headscale/config.yml', os.R_OK): config_readable = True
    else:
        app.logger.error("/etc/headscale/config.y(a)ml：读取：失败")
        checks_passed = False

    if checks_passed:
        app.logger.info("所有启动检查通过。")
        return "通过"

    message_html = ""
    # 生成消息：
    if not server_reachable:
        app.logger.critical("服务器无法访问")
        message = """
        <p>您的 headscale 服务器无法访问或配置不正确。
        请确保配置正确（检查"""+url+"""/api/v1 的状态码是否为 200 失败。响应："""+str(response.status_code)+"""）。</p>
        """

        message_html += format_message("错误", "无法访问 Headscale", message)

    if not config_readable:
        app.logger.critical("Headscale 配置文件不可读")
        message = """
        <p>/etc/headscale/config.yaml 不可读。请确保您的
        headscale 配置文件位于 /etc/headscale，并且
        名称为 "config.yaml" 或 "config.yml"</p>
        """

        message_html += format_message("错误", "/etc/headscale/config.yaml 不可读", message)

    if not data_writable:
        app.logger.critical(f"{DATA_DIRECTORY} 文件夹不可写")
        message = f"""
        <p>{DATA_DIRECTORY} 不可写。请确保您的
        权限设置正确。{DATA_DIRECTORY} 挂载点应该由 UID/GID 1000:1000 可写。</p>
        """

        message_html += format_message("错误", f"{DATA_DIRECTORY} 不可写", message)

    if not data_readable:
        app.logger.critical(f"{DATA_DIRECTORY} 文件夹不可读")
        message = f"""
        <p>{DATA_DIRECTORY} 不可读。请确保您的
        权限设置正确。{DATA_DIRECTORY} 挂载点应该由 UID/GID 1000:1000 可读。</p>
        """

        message_html += format_message("错误", f"{DATA_DIRECTORY} 不可读", message)

    if not data_executable:
        app.logger.critical(f"{DATA_DIRECTORY} 文件夹不可读")
        message = f"""
        <p>{DATA_DIRECTORY} 不可执行。请确保您的
        权限设置正确。{DATA_DIRECTORY} 挂载点应该由 UID/GID 1000:1000 可读。（chown 1000:1000 /path/to/data && chmod -R 755 /path/to/data）</p>
        """

        message_html += format_message("错误", f"{DATA_DIRECTORY} 不可执行", message)


    if file_exists:
        # 如果不存在，我们假设用户尚未创建它。
        # 只需重定向到设置页面输入 API 密钥
        if not file_writable:
            app.logger.critical(f"{os.path.join(DATA_DIRECTORY, 'key.txt')} 不可写")
            message = f"""
            <p>{os.path.join(DATA_DIRECTORY, 'key.txt')} 不可写。请确保您的
            权限设置正确。{DATA_DIRECTORY} 挂载点应该由 UID/GID 1000:1000 可写。</p>
            """

            message_html += format_message("错误", f"{os.path.join(DATA_DIRECTORY, 'key.txt')} 不可写", message)

        if not file_readable:
            app.logger.critical(f"{os.path.join(DATA_DIRECTORY, 'key.txt')} 不可读")
            message = f"""
            <p>{os.path.join(DATA_DIRECTORY, 'key.txt')} 不可读。请确保您的
            权限设置正确。{DATA_DIRECTORY} 挂载点应该由 UID/GID 1000:1000 可读。</p>
            """

            message_html += format_message("错误", f"{os.path.join(DATA_DIRECTORY, 'key.txt')} 不可读", message)

    return message_html

def load_checks():
    """ 将所有检查打包成一个函数以便更容易调用 """
    # 通用错误检查。有关更多信息，请参阅函数：
    if access_checks() != "通过": return '错误页面'
    # 如果 API 密钥失败，则重定向到设置页面：
    if not key_check(): return '设置页面'
    return "通过"
