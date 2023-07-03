//-----------------------------------------------------------
// 在用户和机器页面上进行搜索
//-----------------------------------------------------------
function show_search() {
    $('#nav-search').removeClass('hidden');
    $('#nav-search').addClass('show');
    $('#nav-content').removeClass('show');
    $('#nav-content').addClass('hidden');
}

function hide_search() {
    $('#nav-content').removeClass('hidden');
    $('#nav-content').addClass('show');
    $('#nav-search').removeClass('show');
    $('#nav-search').addClass('hidden');

    // 同时清空搜索框中的内容：
    document.getElementById("search").value = "";
    let cards = document.querySelectorAll('.searchable');
    for (var i = 0; i < cards.length; i++) {
        cards[i].classList.remove("hide");
    }
}

function liveSearch() {
    let cards = document.querySelectorAll('.searchable');
    let search_query = document.getElementById("search").value;

    for (var i = 0; i < cards.length; i++) {
        if (cards[i].textContent.toLowerCase().includes(search_query.toLowerCase())) {
            cards[i].classList.remove("hide");
        } else {
            cards[i].classList.add("hide");
        }
    }
}
//-----------------------------------------------------------
// 通用辅助函数
//-----------------------------------------------------------
function loading() {
    return `<center>
                <div class="preloader-wrapper big active">
                    <div class="spinner-layer spinner-blue-only">
                        <div class="circle-clipper left">
                            <div class="circle">
                            </div>
                        </div>
                        <div class="gap-patch">
                            <div class="circle">
                            </div>
                        </div>
                        <div class="circle-clipper right">
                            <div class="circle"></div>
                        </div>
                    </div>
                </div>
            </center> `;
}

function get_color(id) {
    // 定义颜色...从这个数量开始似乎不错
    var colors = [
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
        "grey        lighten-1"
    ];
    index = id % colors.length;
    return colors[index];
}

// 通用模态框用于警告/问题
function load_modal_generic(type, title, message) {
    console.log("加载通用模态框");
    element = document.getElementById('generic_modal');
    content_element = document.getElementById('generic_modal_content');
    title_element = document.getElementById('generic_modal_title');

    content_element.innerHTML = loading();
    title_element.innerHTML = "加载中...";
    html = "";

    switch (type) {
        case "warning" || "Warning":
            title_html = "警告";
            content_html = `
            <ul class="collection">
                <li class="collection-item avatar">
                    <i class="material-icons circle yellow">priority_high</i>
                    <span class="title">${title}</span>
                    <p>${message}</p>
                </li>
            </ul>`;
            break;
        case "success" || "Success":
            title_html = "成功";
            content_html = `
            <ul class="collection">
                <li class="collection-item avatar">
                    <i class="material-icons circle green">check</i>
                    <span class="title">${title}</span>
                    <p>${message}</p>
                </li>
            </ul>`;
            break;
        case "error" || "Error":
            title_html = "错误";
            content_html = `
            <ul class="collection">
                <li class="collection-item avatar">
                    <i class="material-icons circle red">warning</i>
                    <span class="title">${title}</span>
                    <p>${message}</p>
                </li>
            </ul>`;
            break;
        case "information" || "Information":
            title_html = "信息";
            content_html = `
            <ul class="collection">
                <li class="collection-item avatar">
                    <i class="material-icons circle grey">help</i>
                    <span class="title">${title}</span>
                    <p>${message}</p>
                </li>
            </ul>`;
            break;
    }
    title_element.innerHTML = title_html;
    content_element.innerHTML = content_html;

    var instance = M.Modal.getInstance(element);
    instance.open();
}

// https://stackoverflow.com/questions/3043775/how-to-escape-html#22706073
function escapeHTML(str) {
    var p = document.createElement("p");
    p.appendChild(document.createTextNode(str));
    return p.innerHTML;
}

// 启用浮动操作按钮（FAB）以用于机器和用户页面
document.addEventListener('DOMContentLoaded', function () {
    var elems = document.querySelectorAll('.fixed-action-btn');
    var instances = M.FloatingActionButton.init(elems, { hoverEnabled: false });
});

// 在添加 PreAuth 密钥时初始化日期选择器
document.addEventListener('DOMContentLoaded', function () {
    var elems = document.querySelectorAll('.datepicker');
    var instances = M.Datepicker.init(elems);
});

//-----------------------------------------------------------
// 设置页面操作
//-----------------------------------------------------------
function test_key() {
    document.getElementById('test_modal_results').innerHTML = loading();
    var data = $.ajax({
        type: "GET",
        url: "api/test_key",
        success: function (response) {
            if (response == "Unauthenticated") {
                html = `
                <ul class="collection">
                    <li class="collection-item avatar">
                        <i class="material-icons circle red">warning</i>
                        <span class="title">错误</span>
                        <p>密钥验证失败。请检查您的密钥。</p>
                    </li>
                </ul>
                `;
                document.getElementById('test_modal_results').innerHTML = html;
            } else {
                json = JSON.parse(response);
                var html = `
                    <ul class="collection">
                        <li class="collection-item avatar">
                            <i class="material-icons circle green">check</i>
                            <span class="title">成功</span>
                            <p>密钥已通过 Headscale 服务器的验证。</p>
                        </li>
                    </ul>
                    <h6>密钥信息</h6>
                    <table class="highlight">
                        <tbody>
                            <tr>
                                <td><b>密钥 ID</b></td>
                                <td>${json['id']}</td>
                            </tr>
                            <tr>
                                <td><b>前缀</b></td>
                                <td>${json['prefix']}</td>
                            </tr>
                            <tr>
                                <td><b>过期日期</b></td>
                                <td>${json['expiration']}</td>
                            </tr>
                            <tr>
                                <td><b>创建日期</b></td>
                                <td>${json['createdAt']}</td>
                            </tr>
                        </tbody>
                    </table>
                    `;
                document.getElementById('test_modal_results').innerHTML = html;
            }
        }
    });
}

function save_key() {
    var api_key = document.getElementById('api_key').value;
    if (!api_key) {
        html = `
        <ul class="collection">
            <li class="collection-item avatar">
                <i class="material-icons circle red">warning</i>
                <span class="title">错误</span>
                <p>在保存之前必须输入 API 密钥。</p>
            </li>
        </ul>
        `;
        document.getElementById('test_modal_results').innerHTML = html;
        return;
    }
    var data = { "api_key": api_key };
    $.ajax({
        type: "POST",
        url: "api/save_key",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            M.toast({ html: '密钥已保存。正在测试...' });
            test_key();
        }
    });
}

//-----------------------------------------------------------
// Modal Loaders
//-----------------------------------------------------------
function load_modal_rename_user(user_id, old_name) {
    document.getElementById('modal_content').innerHTML = loading()
    document.getElementById('modal_title').innerHTML = "加载中..."
    document.getElementById('modal_confirm').className = "green btn-flat white-text"
    document.getElementById('modal_confirm').innerText = "重命名"

    modal = document.getElementById('card_modal');
    modal_title = document.getElementById('modal_title');
    modal_body = document.getElementById('modal_content');
    modal_confirm = document.getElementById('modal_confirm');

    modal_title.innerHTML = "重命名用户 '" + old_name + "'?"
    body_html = `
    <ul class="collection">
        <li class="collection-item avatar">
            <i class="material-icons circle">language</i>
            <span class="title">信息</span>
            <p>您即将重命名用户 '${old_name}'</p>
        </li>
    </ul>
    <h6>新名称</h6>
    <div class="input-field">
        <i class="material-icons prefix">language</i>
        <input value='${old_name}' id="new_user_name_form" type="text" data-length="32">
    </div>
    `

    modal_body.innerHTML = body_html
    $(document).ready(function () { $('input#new_user_name_form').characterCounter(); });

    modal_confirm.setAttribute('onclick', 'rename_user(' + user_id + ', "' + old_name + '")')
}

function load_modal_delete_user(user_id, user_name) {
    document.getElementById('modal_content').innerHTML = loading()
    document.getElementById('modal_title').innerHTML = "加载中..."
    document.getElementById('modal_confirm').className = "red btn-flat white-text"
    document.getElementById('modal_confirm').innerText = "删除"

    modal = document.getElementById('card_modal');
    modal_title = document.getElementById('modal_title');
    modal_body = document.getElementById('modal_content');
    modal_confirm = document.getElementById('modal_confirm');

    modal_title.innerHTML = "删除用户 '" + user_name + "'?"
    body_html = `
    <ul class="collection">
        <li class="collection-item avatar">
            <i class="material-icons circle red">warning</i>
            <span class="title">警告</span>
            <p>您确定要删除用户 '${user_name}' 吗？</p>
        </li>
    </ul>
    `
    modal_body.innerHTML = body_html
    modal_confirm.setAttribute('onclick', 'delete_user("' + user_id + '", "' + user_name + '")')
}

function load_modal_add_preauth_key(user_name) {
    document.getElementById('modal_content').innerHTML = loading()
    document.getElementById('modal_title').innerHTML = "加载中..."
    document.getElementById('modal_confirm').className = "green btn-flat white-text"
    document.getElementById('modal_confirm').innerText = "添加"

    modal = document.getElementById('card_modal');
    modal_title = document.getElementById('modal_title');
    modal_body = document.getElementById('modal_content');
    modal_confirm = document.getElementById('modal_confirm');

    modal_title.innerHTML = "向 '" + user_name + "' 添加 PreAuth 密钥"
    body_html = `
        <ul class="collection">
            <li class="collection-item avatar">
                <i class="material-icons circle">help</i>
                <span class="title">信息</span>
                <p>
                    <ul>
                        <li>Pre-Auth 密钥可用于在不手动注册机器的情况下进行 Headscale 的身份验证。使用标志 <code>--auth-key</code> 来实现。</li>
                        <li>"临时" 密钥可用于注册频繁上线和下线的设备（例如，Docker 容器）</li>
                        <li>可重复使用的密钥可多次使用。一次性使用的密钥将在第一次使用后过期。</li> 
                    </ul>
                </p>
            </li>
        </ul>
        <h4>PreAuth 密钥信息</h4>
        <br>
        <input type="text" class="datepicker" id="preauth_key_expiration_date">
        <p>
            <label>
                <input type="checkbox" class="filled-in" id="checkbox-reusable"/>
                <span>可重复使用</span>
            </label>
        </p>
        <p>
            <label>
                <input type="checkbox" class="filled-in" id="checkbox-ephemeral" />
                <span>临时</span>
            </label>
        </p>
    `

    modal_body.innerHTML = body_html

    // 初始化日期选择器
    M.Datepicker.init(document.querySelector('.datepicker'), { format: 'yyyy-mm-dd' });

    modal_confirm.setAttribute('onclick', 'add_preauth_key("' + user_name + '")')
}

function load_modal_expire_preauth_key(user_name, key) {
    document.getElementById('modal_content').innerHTML = loading()
    document.getElementById('modal_title').innerHTML = "加载中..."
    document.getElementById('modal_confirm').className = "red lighten-2 btn-flat white-text"
    document.getElementById('modal_confirm').innerText = "过期"

    modal = document.getElementById('card_modal');
    modal_title = document.getElementById('modal_title');
    modal_body = document.getElementById('modal_content');
    modal_confirm = document.getElementById('modal_confirm');

    modal_title.innerHTML = "过期 PreAuth 密钥?"
    body_html = `
    <ul class="collection">
        <li class="collection-item avatar">
            <i class="material-icons circle red">warning</i>
            <span class="title">警告</span>
            <p>您确定要过期此密钥吗？之后它将无法使用，并且当前使用它的任何机器都将断开连接。</p>
        </li>
    </ul>
    `
    modal_body.innerHTML = body_html
    modal_confirm.setAttribute('onclick', 'expire_preauth_key("' + user_name + '", "' + key + '")')
}

function load_modal_move_machine(machine_id) {
    document.getElementById('modal_content').innerHTML = loading()
    document.getElementById('modal_title').innerHTML = "加载中..."
    document.getElementById('modal_confirm').className = "green btn-flat white-text"
    document.getElementById('modal_confirm').innerText = "移动"

    var data = { "id": machine_id }
    $.ajax({
        type: "POST",
        url: "api/machine_information",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (headscale) {
            $.ajax({
                type: "POST",
                url: "api/get_users",
                success: function (response) {
                    modal = document.getElementById('card_modal');
                    modal_title = document.getElementById('modal_title');
                    modal_body = document.getElementById('modal_content');
                    modal_confirm = document.getElementById('modal_confirm');

                    modal_title.innerHTML = "移动机器 '" + headscale.machine.givenName + "'?"

                    select_html = `<h6>选择用户</h6><select id='move-select'>`
                    for (let i = 0; i < response.users.length; i++) {
                        var name = response["users"][i]["name"]
                        select_html = select_html + `<option value="${name}">${name}</option>`
                    }
                    select_html = select_html + `</select>`

                    body_html = `
                    <ul class="collection">
                        <li class="collection-item avatar">
                            <i class="material-icons circle">language</i>
                            <span class="title">信息</span>
                            <p>您即将将 ${headscale.machine.givenName} 移动到新用户。</p>
                        </li>
                    </ul>`
                    body_html = body_html + select_html
                    body_html = body_html + `<h6>机器信息</h6>
                    <table class="highlight">
                        <tbody>
                            <tr>
                                <td><b>机器 ID</b></td>
                                <td>${headscale.machine.id}</td>
                            </tr>
                            <tr>
                                <td><b>主机名</b></td>
                                <td>${headscale.machine.name}</td>
                            </tr>
                            <tr>
                                <td><b>用户</b></td>
                                <td>${headscale.machine.user.name}</td>
                            </tr>
                        </tbody>
                    </table>
                    `

                    modal_body.innerHTML = body_html
                    M.FormSelect.init(document.querySelectorAll('select'))
                }
            })
            modal_confirm.setAttribute('onclick', 'move_machine(' + machine_id + ')')
        }
    })
}

function load_modal_delete_machine(machine_id) {
    document.getElementById('modal_content').innerHTML = loading()
    document.getElementById('modal_title').innerHTML = "加载中..."
    document.getElementById('modal_confirm').className = "red btn-flat white-text"
    document.getElementById('modal_confirm').innerText = "删除"

    var data = { "id": machine_id }
    $.ajax({
        type: "POST",
        url: "api/machine_information",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            modal = document.getElementById('card_modal');
            modal_title = document.getElementById('modal_title');
            modal_body = document.getElementById('modal_content');
            modal_confirm = document.getElementById('modal_confirm');

            modal_title.innerHTML = "删除机器 '" + response.machine.givenName + "'?"
            body_html = `
            <ul class="collection">
                <li class="collection-item avatar">
                    <i class="material-icons circle red">warning</i>
                    <span class="title">警告</span>
                    <p>您确定要删除 ${response.machine.givenName} 吗？</p>
                </li>
            </ul>
            <h6>机器信息</h6>
            <table class="highlight">
                <tbody>
                    <tr>
                        <td><b>机器 ID</b></td>
                        <td>${response.machine.id}</td>
                    </tr>
                    <tr>
                        <td><b>主机名</b></td>
                        <td>${response.machine.name}</td>
                    </tr>
                    <tr>
                        <td><b>用户</b></td>
                        <td>${response.machine.user.name}</td>
                    </tr>
                </tbody>
            </table>
            `
            modal_body.innerHTML = body_html
            modal_confirm.setAttribute('onclick', 'delete_machine(' + machine_id + ')')
        }
    })
}

function load_modal_rename_machine(machine_id) {
    document.getElementById('modal_content').innerHTML = loading()
    document.getElementById('modal_title').innerHTML = "加载中..."
    document.getElementById('modal_confirm').className = "green btn-flat white-text"
    document.getElementById('modal_confirm').innerText = "重命名"
    var data = { "id": machine_id }
    $.ajax({
        type: "POST",
        url: "api/machine_information",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            modal = document.getElementById('card_modal');
            modal_title = document.getElementById('modal_title');
            modal_body = document.getElementById('modal_content');
            modal_confirm = document.getElementById('modal_confirm');

            modal_title.innerHTML = "重命名机器 '" + response.machine.givenName + "'?"
            body_html = `
            <ul class="collection">
                <li class="collection-item avatar">
                    <i class="material-icons circle">devices</i>
                    <span class="title">信息</span>
                    <p>您即将重命名 ${response.machine.givenName}</p>
                </li>
            </ul>
            <h6>新名称</h6>
            <div class="input-field">
                <input value='${response.machine.givenName}' id="new_name_form" type="text">
                <label for="new_name_form" class="active">新机器名称</label>
            </div>
            <h6>机器信息</h6>
            <table class="highlight">
                <tbody>
                    <tr>
                        <td><b>机器 ID</b></td>
                        <td>${response.machine.id}</td>
                    </tr>
                    <tr>
                        <td><b>主机名</b></td>
                        <td>${response.machine.name}</td>
                    </tr>
                    <tr>
                        <td><b>用户</b></td>
                        <td>${response.machine.user.name}</td>
                    </tr>
                </tbody>
            </table>
            `
            modal_body.innerHTML = body_html
            modal_confirm.setAttribute('onclick', 'rename_machine(' + machine_id + ')')
        }
    })
}

function load_modal_add_machine() {
    $.ajax({
        type: "POST",
        url: "api/get_users",
        success: function (response) {
            modal_body = document.getElementById('default_add_new_machine_modal');
            modal_confirm = document.getElementById('new_machine_modal_confirm');

            select_html = `
            <div class="col s12 m6">
                <div class="input-field">
                    <i class="material-icons prefix">language</i>
                    <select id='add_machine_user_select'>
                        <option value="" disabled selected>选择用户</option>`
            for (let i = 0; i < response.users.length; i++) {
                var name = response["users"][i]["name"]
                select_html = select_html + `<option value="${name}">${name}</option>`
            }
            select_html = select_html + `
                        <label>选择用户</label>
                    </select>
                </div>
            </div>`
            select_html = select_html + `
            <div class="col s12 m6">
                <div class="input-field">
                    <i class="material-icons prefix">vpn_key</i>
                    <input id="add_machine_key_field" type="password">
                    <label for="add_machine_key_field">机器注册密钥</label>
                </div>
            </div>`
            for (let i = 0; i < response.users.length; i++) {
                var name = response["users"][i]["name"]
            }

            modal_body.innerHTML = select_html
            // 初始化表单和机器选项卡
            M.FormSelect.init(document.querySelectorAll('select'), { classes: 'add_machine_selector_class' })
            M.Tabs.init(document.getElementById('new_machine_tabs'));
        }
    })
}


//-----------------------------------------------------------
// Machine Page Actions
//-----------------------------------------------------------
function delete_chip(machine_id, chipsData) {
    // 我们需要获取所有当前的标签 -- 我们不关心被删除的标签，只关心剩下的标签
    // chipsData 是一个从数组创建的数组
    chips = JSON.stringify(chipsData)

    var formattedData = [];
    for (let tag in chipsData) {
        formattedData[tag] = '"tag:' + chipsData[tag].tag + '"'
    }
    var tags_list = '{"tags": [' + formattedData + ']}'
    var data = { "id": machine_id, "tags_list": tags_list }

    $.ajax({
        type: "POST",
        url: "api/set_machine_tags",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            M.toast({ html: '标签已移除。' });
        }
    })
}

function add_chip(machine_id, chipsData) {
    chips = JSON.stringify(chipsData).toLowerCase()
    chipsData[chipsData.length - 1].tag = chipsData[chipsData.length - 1].tag.trim().replace(/\s+/g, '-')
    last_chip_fixed = chipsData[chipsData.length - 1].tag

    var formattedData = [];
    for (let tag in chipsData) {
        formattedData[tag] = '"tag:' + chipsData[tag].tag + '"'
    }
    var tags_list = '{"tags": [' + formattedData + ']}'
    var data = { "id": machine_id, "tags_list": tags_list }

    $.ajax({
        type: "POST",
        url: "api/set_machine_tags",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            M.toast({ html: '已添加标签 "' + last_chip_fixed + '"。' });
        }
    })
}

function add_machine() {
    var key = document.getElementById('add_machine_key_field').value
    var user = document.getElementById('add_machine_user_select').value
    var data = { "key": key, "user": user }

    if (user == "") {
        load_modal_generic("error", "用户为空", "提交前请选择一个用户")
        return
    }
    if (key == "") {
        load_modal_generic("error", "密钥为空", "输入由您的 <code>tailscale login</code> 命令生成的密钥")
        return
    }

    $.ajax({
        type: "POST",
        url: "api/register_machine",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            if (response.machine) {
                window.location.reload()
                return
            }
            load_modal_generic("error", "添加机器时出错", response.message)
            return
        }
    })
}

function rename_machine(machine_id) {
    var new_name = document.getElementById('new_name_form').value;
    var data = { "id": machine_id, "new_name": new_name };

    // 用于测试的字符串
    var regexIT = /[`!@#$%^&*()_+\=\[\]{};':"\\|,.<>\/?~]/;
    if (regexIT.test(new_name)) { load_modal_generic("error", "无效的名称", "名称不能包含特殊字符（'" + regexIT + "'）"); return }
    // 如果除了 - 和字母数字字符之外还有其他字符，则抛出错误
    if (new_name.includes(' ')) { load_modal_generic("error", "名称不能包含空格", "允许的字符包括破折号（-）和字母数字字符"); return }
    // 如果长度超过32个字符，则抛出错误
    if (new_name.length > 32) { load_modal_generic("error", "名称过长", "名称过长。最大长度为32个字符"); return }
    // 如果 new_name 为空，则抛出错误
    if (!new_name) { load_modal_generic("error", "名称不能为空", "提交前请输入机器名称"); return }

    $.ajax({
        type: "POST",
        url: "api/rename_machine",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {

            if (response.status == "True") {
                // 获取模态框元素并关闭它
                modal_element = document.getElementById('card_modal')
                M.Modal.getInstance(modal_element).close()

                document.getElementById(machine_id + '-name-container').innerHTML = machine_id + ". " + escapeHTML(new_name)
                M.toast({ html: '机器 ' + machine_id + ' 已重命名为 ' + escapeHTML(new_name) });
            } else {
                load_modal_generic("error", "设置机器名称时出错", "Headscale 响应：" + JSON.stringify(response.body.message))
            }
        }
    })
}

function move_machine(machine_id) {
    new_user = document.getElementById('move-select').value
    var data = { "id": machine_id, "new_user": new_user };

    $.ajax({
        type: "POST",
        url: "api/move_user",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            // 获取模态框元素并关闭它
            modal_element = document.getElementById('card_modal')
            M.Modal.getInstance(modal_element).close()

            document.getElementById(machine_id + '-user-container').innerHTML = response.machine.user.name
            document.getElementById(machine_id + '-ns-badge').innerHTML = response.machine.user.name

            // 获取颜色并设置它
            var user_color = get_color(response.machine.user.id)
            document.getElementById(machine_id + '-ns-badge').className = "badge ipinfo " + user_color + " white-text hide-on-small-only"

            M.toast({ html: "已将 '" + response.machine.givenName + "' 移动到用户 " + response.machine.user.name });
        }
    })
}

function delete_machine(machine_id) {
    var data = { "id": machine_id };
    $.ajax({
        type: "POST",
        url: "api/delete_machine",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            // 获取模态框元素并关闭它
            modal_element = document.getElementById('card_modal')
            M.Modal.getInstance(modal_element).close()

            // 删除机器后，隐藏它的可折叠项：
            document.getElementById(machine_id + '-main-collapsible').className = "collapsible popout hide";

            M.toast({ html: '机器已删除。' });
        }
    })
}

function toggle_exit(route1, route2, exit_id, current_state, page) {
    var data1 = { "route_id": route1, "current_state": current_state }
    var data2 = { "route_id": route2, "current_state": current_state }
    var element = document.getElementById(exit_id);

    var disabledClass = ""
    var enabledClass = ""

    if (page == "machines") {
        disabledClass = "waves-effect waves-light btn-small red lighten-2 tooltipped";
        enabledClass = "waves-effect waves-light btn-small green lighten-2 tooltipped";
    }
    if (page == "routes") {
        disabledClass = "material-icons red-text text-lighten-2 tooltipped";
        enabledClass = "material-icons green-text text-lighten-2 tooltipped";
    }

    var disabledTooltip = "点击启用"
    var enabledTooltip = "点击禁用"
    var disableState = "False"
    var enableState = "True"
    var action_taken = "未更改。";

    $.ajax({
        type: "POST",
        url: "api/update_route",
        data: JSON.stringify(data1),
        contentType: "application/json",
        success: function (response) {
            $.ajax({
                type: "POST",
                url: "api/update_route",
                data: JSON.stringify(data2),
                contentType: "application/json",
                success: function (response) {
                    // 响应是一个包含 Headscale API 响应的 JSON 对象，路径为 /v1/api/machines/<id>/route
                    if (element.className == disabledClass) {
                        element.className = enabledClass
                        action_taken = "已启用。"
                        element.setAttribute('data-tooltip', enabledTooltip)
                        element.setAttribute('onclick', 'toggle_exit(' + route1 + ', ' + route2 + ', "' + exit_id + '", "' + enableState + '", "' + page + '")')
                    } else if (element.className == enabledClass) {
                        element.className = disabledClass
                        action_taken = "已禁用。"
                        element.setAttribute('data-tooltip', disabledTooltip)
                        element.setAttribute('onclick', 'toggle_exit(' + route1 + ', ' + route2 + ', "' + exit_id + '", "' + disableState + '", "' + page + '")')
                    }
                    M.toast({ html: '出口路由 ' + action_taken });
                }
            })
        }
    })
}

function toggle_route(route_id, current_state, page) {
    var data = { "route_id": route_id, "current_state": current_state }
    var element = document.getElementById(route_id);

    var disabledClass = ""
    var enabledClass = ""

    if (page == "machines") {
        disabledClass = "waves-effect waves-light btn-small red lighten-2 tooltipped";
        enabledClass = "waves-effect waves-light btn-small green lighten-2 tooltipped";
    }
    if (page == "routes") {
        disabledClass = "material-icons red-text text-lighten-2 tooltipped";
        enabledClass = "material-icons green-text text-lighten-2 tooltipped";
    }

    var disabledTooltip = "点击启用"
    var enabledTooltip = "点击禁用"
    var disableState = "False"
    var enableState = "True"
    var action_taken = "未更改。";
    $.ajax({
        type: "POST",
        url: "api/update_route",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            if (element.className == disabledClass) {
                element.className = enabledClass
                action_taken = "已启用。"
                element.setAttribute('data-tooltip', enabledTooltip)
                element.setAttribute('onclick', 'toggle_route(' + route_id + ', "' + enableState + '", "' + page + '")')
            } else if (element.className == enabledClass) {
                element.className = disabledClass
                action_taken = "已禁用。"
                element.setAttribute('data-tooltip', disabledTooltip)
                element.setAttribute('onclick', 'toggle_route(' + route_id + ', "' + disableState + '", "' + page + '")')
            }
            M.toast({ html: '路由 ' + action_taken });
        }
    })
}

function get_routes() {
    console.log("获取所有路由的信息")
    var data
    $.ajax({
        async: false,
        type: "POST",
        url: "api/get_routes",
        contentType: "application/json",
        success: function (response) {
            console.log("获取所有路由成功。")
            data = response
        }
    })
    return data
}

function toggle_failover_route_routespage(routeid, current_state, prefix, route_id_list) {
    // 首先，切换路由：
    // toggle_route(route_id, current_state, page)
    var data = { "route_id": routeid, "current_state": current_state }
    console.log("数据:  " + JSON.stringify(data))
    console.log("传入:  " + routeid + ", " + current_state + ", " + prefix + ", " + route_id_list)
    var element = document.getElementById(routeid);

    var disabledClass = "material-icons red-text text-lighten-2 tooltipped";
    var enabledClass = "material-icons green-text text-lighten-2 tooltipped";
    var failover_disabledClass = "material-icons small left red-text text-lighten-2"
    var failover_enabledClass = "material-icons small left green-text text-lighten-2"

    var disabledTooltip = "点击启用 (故障切换对)"
    var enabledTooltip = "点击禁用 (故障切换对)"
    var disableState = "False"
    var enableState = "True"
    var action_taken = "未更改。"

    $.ajax({
        type: "POST",
        url: "api/update_route",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            console.log("成功:  路由 ID:  " + routeid)
            console.log("成功: route_id_list:  " + route_id_list)
            if (element.className == disabledClass) {
                element.className = enabledClass
                action_taken = "已启用。"
                element.setAttribute('data-tooltip', enabledTooltip)
                element.setAttribute('onclick', 'toggle_failover_route_routespage(' + routeid + ', "' + enableState + '", "' + prefix + '", [' + route_id_list + '])')
            } else if (element.className == enabledClass) {
                element.className = disabledClass
                action_taken = "已禁用。"
                element.setAttribute('data-tooltip', disabledTooltip)
                element.setAttribute('onclick', 'toggle_failover_route_routespage(' + routeid + ', "' + disableState + '", "' + prefix + '", [' + route_id_list + '])')
            }
            M.toast({ html: '路由 ' + action_taken });

            // 获取所有路由信息：
            console.log("获取前缀 " + prefix + " 的信息")
            var routes = get_routes()
            var failover_enabled = false

            // 获取前缀的主要和启用显示：
            for (let i = 0; i < route_id_list.length; i++) {
                console.log("route_id_list[" + i + "]: " + route_id_list[i])
                var route_id = route_id_list[i]
                var route_index = route_id - 1
                console.log("查找路由 " + route_id + " 在索引 " + route_index + " 处")
                console.log("isPrimary:  " + routes["routes"][route_index]["isPrimary"])

                // 设置主要类：
                var primary_element = document.getElementById(route_id + "-primary")
                var primary_status = routes["routes"][route_index]["isPrimary"]
                var enabled_status = routes["routes"][route_index]["enabled"]

                console.log("enabled_status:  " + enabled_status)

                if (enabled_status == true) {
                    failover_enabled = true
                }

                console.log("设置主要类 '" + route_id + "-primary':  " + primary_status)
                if (primary_status == true) {
                    console.log("检测到此路由是主要路由。设置类")
                    primary_element.className = enabledClass
                } else if (primary_status == false) {
                    console.log("检测到此路由不是主要路由。设置类")
                    primary_element.className = disabledClass
                }
            }

            // 如果有任何启用的路由，则将前缀启用图标设置为启用状态：
            var failover_element = document.getElementById(prefix)
            console.log("故障切换已启用:  " + failover_enabled)
            if (failover_enabled == true) {
                failover_element.className = failover_enabledClass
            }
            else if (failover_enabled == false) {
                failover_element.className = failover_disabledClass
            }
        }
    })
}

function toggle_failover_route(route_id, current_state, color) {
    var data = { "route_id": route_id, "current_state": current_state }
    $.ajax({
        type: "POST",
        url: "api/update_route",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            // 响应是一个包含 Headscale API 响应的 JSON 对象，路径为 /v1/api/machines/<id>/route
            var element = document.getElementById(route_id);
            var disabledClass = "waves-effect waves-light btn-small red lighten-2 tooltipped";
            var enabledClass = "waves-effect waves-light btn-small " + color + " lighten-2 tooltipped";
            var disabledTooltip = "点击启用 (故障切换对)"
            var enabledTooltip = "点击禁用 (故障切换对)"
            var disableState = "False"
            var enableState = "True"
            var action_taken = "未更改。";

            if (element.className == disabledClass) {
                // 1. 更改类以更改图标的颜色
                // 2. 更改 M.toast 弹出窗口的 "action taken"
                // 3. 更改工具提示以显示 "点击启用/禁用"
                element.className = enabledClass
                var action_taken = "已启用。"
                element.setAttribute('data-tooltip', enabledTooltip)
                element.setAttribute('onclick', 'toggle_failover_route(' + route_id + ', "' + enableState + '", "' + color + '")')
            } else if (element.className == enabledClass) {
                element.className = disabledClass
                var action_taken = "已禁用。"
                element.setAttribute('data-tooltip', disabledTooltip)
                element.setAttribute('onclick', 'toggle_failover_route(' + route_id + ', "' + disableState + '", "' + color + '")')
            }
            M.toast({ html: '路由 ' + action_taken });
        }
    })
}

//-----------------------------------------------------------
// 机器页面辅助函数
//-----------------------------------------------------------
function btn_toggle(state) {
    if (state == "show") { document.getElementById('new_machine_modal_confirm').className = 'green btn-flat white-text' }
    else { document.getElementById('new_machine_modal_confirm').className = 'green btn-flat white-text hide' }
}

//-----------------------------------------------------------
// 用户页面操作
//-----------------------------------------------------------
function rename_user(user_id, old_name) {
    var new_name = document.getElementById('new_user_name_form').value;
    var data = { "old_name": old_name, "new_name": new_name }

    // 用于测试的字符串
    var regexIT = /[`!@#$%^&*()_+\=\[\]{};':"\\|,.<>\/?~]/;
    if (regexIT.test(new_name)) { load_modal_generic("error", "无效的名称", "名称不能包含特殊字符（'" + regexIT + "'）"); return }
    // 如果除了 - 和字母数字字符之外还有其他字符，则抛出错误
    if (new_name.includes(' ')) { load_modal_generic("error", "名称不能包含空格", "允许的字符包括破折号（-）和字母数字字符"); return }
    // 如果长度超过32个字符，则抛出错误
    if (new_name.length > 32) { load_modal_generic("error", "名称过长", "用户名称过长。最大长度为32个字符"); return }
    // 如果 new_name 为空，则抛出错误
    if (!new_name) { load_modal_generic("error", "名称不能为空", "用户名称不能为空。"); return }

    $.ajax({
        type: "POST",
        url: "api/rename_user",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            if (response.status == "True") {
                // 获取模态框元素并关闭它
                modal_element = document.getElementById('card_modal')
                M.Modal.getInstance(modal_element).close()

                // 在页面上重命名用户：
                document.getElementById(user_id + '-name-span').innerHTML = escapeHTML(new_name)

                // 设置按钮使用 NEW name 作为 OLD name 的名称
                var rename_button_sm = document.getElementById(user_id + '-rename-user-sm')
                rename_button_sm.setAttribute('onclick', 'load_modal_rename_user(' + user_id + ', "' + new_name + '")')
                var rename_button_lg = document.getElementById(user_id + '-rename-user-lg')
                rename_button_lg.setAttribute('onclick', 'load_modal_rename_user(' + user_id + ', "' + new_name + '")')

                // 发送完成提示
                M.toast({ html: "用户 '" + old_name + "' 已重命名为 '" + new_name + "'。" })
            } else {
                load_modal_generic("error", "设置用户名时出错", "Headscale 响应：" + JSON.stringify(response.body.message))
            }
        }
    })
}

function delete_user(user_id, user_name) {
    var data = { "name": user_name };
    $.ajax({
        type: "POST",
        url: "api/delete_user",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            if (response.status == "True") {
                // 获取模态框元素并关闭它
                modal_element = document.getElementById('card_modal')
                M.Modal.getInstance(modal_element).close()

                // 删除用户时，隐藏其可折叠项：
                document.getElementById(user_id + '-main-collapsible').className = "collapsible popout hide";

                M.toast({ html: '用户已删除。' });
            } else {
                // 发生错误。解析 Headscale 发送的错误并显示：
                load_modal_generic("error", "删除用户时出错", "Headscale 响应：" + JSON.stringify(response.body.message))
            }
        }
    })
}

function add_user() {
    var user_name = document.getElementById('add_user_name_field').value
    var data = { "name": user_name }
    $.ajax({
        type: "POST",
        url: "api/add_user",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            if (response.status == "True") {
                // 获取模态框元素并关闭它
                modal_element = document.getElementById('card_modal')
                M.Modal.getInstance(modal_element).close()

                // 发送完成提示
                M.toast({ html: "用户 '" + user_name + "' 已添加到 Headscale。正在刷新页面..." })
                window.location.reload()
            } else {
                // 发生错误。解析 Headscale 发送的错误并显示：
                load_modal_generic("error", "添加用户时出错", "Headscale 响应：" + JSON.stringify(response.body.message))
            }
        }
    })
}

function add_preauth_key(user_name) {
    var date = document.getElementById('preauth_key_expiration_date').value
    var ephemeral = document.getElementById('checkbox-ephemeral').checked
    var reusable = document.getElementById('checkbox-reusable').checked
    var expiration = date + "T00:00:00.000Z" // Headscale 格式。

    // 如果没有日期，则报错：
    if (!date) { load_modal_generic("error", "无效的日期", "请输入有效日期"); return }
    var data = { "user": user_name, "reusable": reusable, "ephemeral": ephemeral, "expiration": expiration }

    $.ajax({
        type: "POST",
        url: "api/add_preauth_key",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            if (response.status == "True") {
                // 发送完成提示
                M.toast({ html: '在用户 ' + user_name + ' 中创建了预授权密钥' })
                // 如果成功，应重新加载表格并关闭模态框：
                var user_data = { "name": user_name }
                $.ajax({
                    type: "POST",
                    url: "api/build_preauthkey_table",
                    data: JSON.stringify(user_data),
                    contentType: "application/json",
                    success: function (table_data) {
                        table = document.getElementById(user_name + '-preauth-keys-collection')
                        table.innerHTML = table_data
                        // 需要在此之后重新初始化工具提示：
                        M.Tooltip.init(document.querySelectorAll('.tooltipped'))
                    }
                })
                // 获取模态框元素并关闭它
                modal_element = document.getElementById('card_modal')
                M.Modal.getInstance(modal_element).close()

                // 需要在此之后重新初始化工具提示：
                M.Tooltip.init(document.querySelectorAll('.tooltipped'))

            } else {
                load_modal_generic("error", "添加预授权密钥时出错", "Headscale 响应：" + JSON.stringify(response.body.message))
            }
        }
    })
}

function expire_preauth_key(user_name, key) {
    var data = { "user": user_name, "key": key }

    $.ajax({
        type: "POST",
        url: "api/expire_preauth_key",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function (response) {
            if (response.status == "True") {
                // 发送完成提示
                M.toast({ html: '在 ' + user_name + ' 中过期了预授权密钥' })
                // 如果成功，应重新加载表格并关闭模态框：
                var user_data = { "name": user_name }
                $.ajax({
                    type: "POST",
                    url: "api/build_preauthkey_table",
                    data: JSON.stringify(user_data),
                    contentType: "application/json",
                    success: function (table_data) {
                        table = document.getElementById(user_name + '-preauth-keys-collection')
                        table.innerHTML = table_data
                        // 需要在此之后重新初始化工具提示：
                        M.Tooltip.init(document.querySelectorAll('.tooltipped'))
                    }
                })
                // 获取模态框元素并关闭它
                modal_element = document.getElementById('card_modal')
                M.Modal.getInstance(modal_element).close()

                // 需要在此之后重新初始化工具提示：
                M.Tooltip.init(document.querySelectorAll('.tooltipped'))

            } else {
                load_modal_generic("error", "预授权密钥过期时出错", "Headscale 响应：" + JSON.stringify(response.body.message))
            }
        }
    })
}

//-----------------------------------------------------------
// 用户页面辅助函数
//-----------------------------------------------------------
// 切换用户 PreAuth 部分的过期项：
function toggle_expired() {
    var toggle_hide = document.getElementsByClassName('expired-row');
    var hidden = document.getElementsByClassName('expired-row hide');

    if (hidden.length == 0) {
        for (var i = 0; i < toggle_hide.length; i++) {
            toggle_hide[i].className = "expired-row hide";
        }
    } else if (hidden.length > 0) {
        for (var i = 0; i < toggle_hide.length; i++) {
            toggle_hide[i].className = "expired-row";
        }
    }
}

// 将 PreAuth 密钥复制到剪贴板。默认只显示前缀
function copy_preauth_key(key) {
    navigator.clipboard.writeText(key);
    M.toast({ html: 'PreAuth 密钥已复制到剪贴板。' })
}
