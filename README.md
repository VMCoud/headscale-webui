<p align="center">
  <a href="https://github.com/juanfont/headscale">
    <img src="static/img/headscale3-dots.png" width="250">
  </a>
</p>

<h2 align="center">Headscale-WebUI</h3>

<p align="center">
  一个用于小规模部署的简易 Headscale Web UI。
</p>
<p align="center">
  <a href="#Screenshots">截图</a> | <a href="SETUP.md">安装</a> | <a href="https://github.com/iFargle/headscale-webui/issues">问题</a>
</p>

---

# 功能
1. 启用/禁用路由和出口节点
   * 同时管理故障转移路由
2. 添加、移动、重命名和删除机器
3. 添加和删除用户/命名空间
4. 添加和过期 PreAuth 密钥
5. 添加和删除机器标签
6. 查看机器详细信息
   * 主机名
   * 与机器关联的用户
   * Tailnet 中的 IP 地址
   * 最后一次与控制服务器的通信时间
   * 最后一次与控制服务器的更新时间
   * 创建日期
   * 过期日期（在接近过期时还会显示徽章）
   * 与机器关联的 PreAuth 密钥
   * 启用/禁用路由和出口节点
   * 添加和删除机器标签
7. 基本身份验证和 OIDC 身份验证
   * 使用 Authelia 和 Keycloak 进行了 OIDC 身份验证测试
8. 更改颜色主题！请参阅 MaterializeCSS 文档中的颜色示例。
9. 搜索机器和用户。
   * 机器具有可用于筛选搜索的标签：
     * `tag:标签名` 只搜索特定标签
     * `machine:机器名` 只搜索特定机器
     * `user:用户名` 只搜索特定用户

---

# 安装
* 请参阅 [SETUP.md](SETUP.md) 获取安装和配置说明。

---

# 截图:
![概览](screenshots/overview.png)
![路由](screenshots/routes.png)
![机器](screenshots/machines.png)
![用户](screenshots/users.png)
![设置](screenshots/settings.png)

---

# 使用的技术:
* Python - [链接](https://www.python.org/)
* Poetry - [链接](https://python-poetry.org/)
* MaterializeCSS - [链接](https://github.com/Dogfalo/materialize)
* jQuery - [链接](https://jquery.com/)

有关 Python 库，请参阅 [pyproject.toml](pyproject.toml)

如果您使用了这个项目，请与我联系！这将使我保持动力！谢谢！
