# pylint: disable=wrong-import-order

import requests, json, os, logging, yaml
from cryptography.fernet import Fernet
from datetime import timedelta, date
from dateutil import parser
from flask import Flask
from dotenv import load_dotenv

load_dotenv()
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

##################################################################
# 与 HEADSCALE 和 API KEY 相关的函数
##################################################################
def get_url(inpage=False):
    if not inpage: 
        return os.environ['HS_SERVER']
    config_file = ""
    try:
        config_file = open("/etc/headscale/config.yml",  "r")
        app.logger.info("打开 /etc/headscale/config.yml")
    except: 
        config_file = open("/etc/headscale/config.yaml", "r")
        app.logger.info("打开 /etc/headscale/config.yaml")
    config_yaml = yaml.safe_load(config_file)
    if "server_url" in config_yaml: 
        return str(config_yaml["server_url"])
    app.logger.warning("在配置中找不到 server_url。回退到环境变量")
    return os.environ['HS_SERVER']

def set_api_key(api_key):
    # 用户设置的加密密钥
    encryption_key = os.environ['KEY']                      
    # 文件系统上的密钥文件，用于持久存储
    key_file = open(os.path.join(DATA_DIRECTORY, "key.txt"), "wb+")
    # 使用密钥准备 Fernet 类
    fernet = Fernet(encryption_key)                 
    # 加密密钥
    encrypted_key = fernet.encrypt(api_key.encode())       
    # 如果文件写入成功，则返回 True
    return True if key_file.write(encrypted_key) else False 

def get_api_key():
    if not os.path.exists(os.path.join(DATA_DIRECTORY, "key.txt")):
        return False
    # 用户设置的加密密钥
    encryption_key = os.environ['KEY']                      
    # 文件系统上的密钥文件
    key_file = open(os.path.join(DATA_DIRECTORY, "key.txt"), "rb+")           
    # 从文件中读取的加密密钥
    enc_api_key = key_file.read()                        
    if enc_api_key == b'':
        return "NULL"

    # 使用密钥准备 Fernet 类
    fernet = Fernet(encryption_key)                 
    # 解密密钥
    decrypted_key = fernet.decrypt(enc_api_key).decode()   

    return decrypted_key

def test_api_key(url, api_key):
    response = requests.get(
        str(url)+"/api/v1/apikey",
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    return response.status_code

# 过期 API 密钥
def expire_key(url, api_key):
    payload = {'prefix': str(api_key[0:10])}
    json_payload = json.dumps(payload)
    app.logger.debug("向 headscale 服务器发送负载 '" + str(json_payload) + "'")

    response = requests.post(
        str(url)+"/api/v1/apikey/expire",
        data=json_payload,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
            }
    )
    return response.status_code

# 检查密钥是否需要更新
# 如果需要，更新密钥，然后过期旧密钥
def renew_api_key(url, api_key):
    # 0 = 密钥已更新或密钥不需要更新
    # 1 = 密钥未通过有效性检查或未能写入 API 密钥
    # 检查密钥的过期时间并与今天的日期进行比较：
    key_info = get_api_key_info(url, api_key)
    expiration_time = key_info["expiration"]
    today_date = date.today()
    expire = parser.parse(expiration_time)
    expire_fmt = str(expire.year) + "-" + str(expire.month).zfill(2) + "-" + str(expire.day).zfill(2)
    expire_date = date.fromisoformat(expire_fmt)
    delta = expire_date - today_date
    tmp = today_date + timedelta(days=90) 
    new_expiration_date = str(tmp) + "T00:00:00.000000Z"

    # 如果 delta 小于 5 天，则更新密钥：
    if delta < timedelta(days=5):
        app.logger.warning("密钥即将过期。Delta 为" + str(delta))
        payload = {'expiration': str(new_expiration_date)}
        json_payload = json.dumps(payload)
        app.logger.debug("向 headscale 服务器发送负载 '" + str(json_payload) + "'")

        response = requests.post(
            str(url)+"/api/v1/apikey",
            data=json_payload,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer '+str(api_key)
                }
        )
        new_key = response.json()
        app.logger.debug("JSON:  " + json.dumps(new_key))
        app.logger.debug("新密钥为:  " + new_key["apiKey"])
        api_key_test = test_api_key(url, new_key["apiKey"])
        app.logger.debug("测试密钥:  " + str(api_key_test))
        # 测试新密钥是否有效：
        if api_key_test == 200:
            app.logger.info("新密钥有效，正在将其写入文件")
            if not set_api_key(new_key["apiKey"]):
                app.logger.error("写入新密钥失败！")
                return False  # 密钥写入失败
            app.logger.info("密钥验证并写入成功。继续过期旧密钥。")
            expire_key(url, api_key)
            return True  # 密钥已更新并验证成功
        else:
            app.logger.error("测试 API 密钥失败。")
            return False  # API 密钥测试失败
    else:
        return True  # 不需要进行任何工作

# 获取当前 API 密钥的信息
def get_api_key_info(url, api_key):
    app.logger.info("获取 API 密钥信息")
    response = requests.get(
        str(url)+"/api/v1/apikey",
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    json_response = response.json()
    # 在数组中查找当前密钥：
    key_prefix = str(api_key[0:10])
    app.logger.info("查找有效的 API 密钥...")
    for key in json_response["apiKeys"]:
        if key_prefix == key["prefix"]:
            app.logger.info("找到密钥。")
            return key
    app.logger.error("在 Headscale 中找不到有效的密钥。需要一个新的 API 密钥。")
    return "未找到密钥"

##################################################################
# 与 MACHINES 相关的函数
##################################################################

# 注册新的机器
def register_machine(url, api_key, machine_key, user):
    app.logger.info("注册机器 %s 到用户 %s", str(machine_key), str(user))
    response = requests.post(
        str(url)+"/api/v1/machine/register?user="+str(user)+"&key="+str(machine_key),
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    return response.json()


# 设置机器标签
def set_machine_tags(url, api_key, machine_id, tags_list):
    app.logger.info("设置 machine_id %s 的标签 %s", str(machine_id), str(tags_list))
    response = requests.post(
        str(url)+"/api/v1/machine/"+str(machine_id)+"/tags",
        data=tags_list,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
            }
    )
    return response.json()

# 将 machine_id 移动到用户 "new_user"
def move_user(url, api_key, machine_id, new_user):
    app.logger.info("将 machine_id %s 移动到用户 %s", str(machine_id), str(new_user))
    response = requests.post(
        str(url)+"/api/v1/machine/"+str(machine_id)+"/user?user="+str(new_user),
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    return response.json()

def update_route(url, api_key, route_id, current_state):
    action = "disable" if current_state == "True" else "enable"

    app.logger.info("更新路由 %s：操作：%s", str(route_id), str(action))

    # 调试信息
    app.logger.debug("URL：" + str(url))
    app.logger.debug("路由 ID：" + str(route_id))
    app.logger.debug("当前状态：" + str(current_state))
    app.logger.debug("要执行的操作：" + str(action))

    response = requests.post(
        str(url)+"/api/v1/routes/"+str(route_id)+"/"+str(action),
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    return response.json()

# 获取 Headscale 网络上的所有机器
def get_machines(url, api_key):
    app.logger.info("获取机器信息")
    response = requests.get(
        str(url)+"/api/v1/machine",
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    return response.json()

# 获取 Headscale 网络上的 machine_id 机器信息
def get_machine_info(url, api_key, machine_id):
    app.logger.info("获取 machine ID %s 的信息", str(machine_id))
    response = requests.get(
        str(url)+"/api/v1/machine/"+str(machine_id),
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    return response.json()

# 从 Headscale 中删除机器
def delete_machine(url, api_key, machine_id):
    app.logger.info("删除机器 %s", str(machine_id))
    response = requests.delete(
        str(url)+"/api/v1/machine/"+str(machine_id),
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    status = "True" if response.status_code == 200 else "False"
    if response.status_code == 200:
        app.logger.info("机器已删除。")
    else:
        app.logger.error("删除机器失败！" + str(response.json()))
    return {"status": status, "body": response.json()}

# 使用名称 "new_name" 重命名 "machine_id"
def rename_machine(url, api_key, machine_id, new_name):
    app.logger.info("重命名机器 %s", str(machine_id))
    response = requests.post(
        str(url)+"/api/v1/machine/"+str(machine_id)+"/rename/"+str(new_name),
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    status = "True" if response.status_code == 200 else "False"
    if response.status_code == 200:
        app.logger.info("机器已重命名。")
    else:
        app.logger.error("机器重命名失败！" + str(response.json()))
    return {"status": status, "body": response.json()}

# 获取传递的 machine_id 的路由
def get_machine_routes(url, api_key, machine_id):
    app.logger.info("获取机器 %s 的路由", str(machine_id))
    response = requests.get(
        str(url)+"/api/v1/machine/"+str(machine_id)+"/routes",
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    if response.status_code == 200:
        app.logger.info("已获取路由。")
    else:
        app.logger.error("获取路由失败：" + str(response.json()))
    return response.json()

# 获取整个 Tailnet 的路由
def get_routes(url, api_key):
    app.logger.info("获取路由")
    response = requests.get(
        str(url)+"/api/v1/routes",
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    return response.json()
##################################################################
# 与 USERS 相关的函数
##################################################################

# 获取所有正在使用的用户
def get_users(url, api_key):
    app.logger.info("获取用户")
    response = requests.get(
        str(url)+"/api/v1/user",
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    return response.json()

# 使用名称 "new_name" 重命名 "old_name"
def rename_user(url, api_key, old_name, new_name):
    app.logger.info("将用户 %s 重命名为 %s。", str(old_name), str(new_name))
    response = requests.post(
        str(url)+"/api/v1/user/"+str(old_name)+"/rename/"+str(new_name),
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    status = "True" if response.status_code == 200 else "False"
    if response.status_code == 200:
        app.logger.info("用户已重命名。")
    else:
        app.logger.error("重命名用户失败！")
    return {"status": status, "body": response.json()}

# 从 Headscale 中删除用户
def delete_user(url, api_key, user_name):
    app.logger.info("删除用户：%s", str(user_name))
    response = requests.delete(
        str(url)+"/api/v1/user/"+str(user_name),
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    status = "True" if response.status_code == 200 else "False"
    if response.status_code == 200:
        app.logger.info("用户已删除。")
    else:
        app.logger.error("删除用户失败！")
    return {"status": status, "body": response.json()}

# 向 Headscale 中添加用户
def add_user(url, api_key, data):
    app.logger.info("添加用户：%s", str(data))
    response = requests.post(
        str(url)+"/api/v1/user",
        data=data,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    status = "True" if response.status_code == 200 else "False"
    if response.status_code == 200:
        app.logger.info("用户已添加。")
    else:
        app.logger.error("添加用户失败！")
    return {"status": status, "body": response.json()}

##################################################################
# 与 USERS 中的预授权密钥相关的函数
##################################################################

# 获取与用户 "user_name" 关联的所有预授权密钥
def get_preauth_keys(url, api_key, user_name):
    app.logger.info("获取用户 %s 中的预授权密钥", str(user_name))
    response = requests.get(
        str(url)+"/api/v1/preauthkey?user="+str(user_name),
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    return response.json()

# 向用户 "user_name" 添加预授权密钥，给定布尔值 "ephemeral" 和 "reusable"，
# 以及 JSON 负载 "data" 中的到期日期 "date"
def add_preauth_key(url, api_key, data):
    app.logger.info("添加预授权密钥：%s", str(data))
    response = requests.post(
        str(url)+"/api/v1/preauthkey",
        data=data,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    status = "True" if response.status_code == 200 else "False"
    if response.status_code == 200:
        app.logger.info("预授权密钥已添加。")
    else:
        app.logger.error("添加预授权密钥失败！")
    return {"status": status, "body": response.json()}

# 过期预授权密钥。数据为 {"user": "string", "key": "string"}
def expire_preauth_key(url, api_key, data):
    app.logger.info("过期预授权密钥...")
    response = requests.post(
        str(url)+"/api/v1/preauthkey/expire",
        data=data,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    status = "True" if response.status_code == 200 else "False"
    app.logger.debug("expire_preauth_key - 返回：" + str(response.json()))
    app.logger.debug("expire_preauth_key - 状态：" + str(status))
    return {"status": status, "body": response.json()}

