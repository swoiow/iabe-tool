$.fn.api.settings.throttle = 1500;
$.fn.api.settings.api = {
    "search": "/search",
    "work": "/do/{service}",
    "api_get": "/api/{service}/{account}",
    "api_post": "/api/{service}"
};

function DoSync(ac, n, a) {
    a = typeof a === "undefined" ? 0 : a;
    $.post({
        url: "/sync",
        data: {"action": ac, "node": n, "all": a, "_xsrf": GetCookie("_xsrf"), "ref": window.location.hostname}
    }).done(function (resp) {
        return MsgBox("#msgBox", "", "请求结果", resp.result, 2500);
    })
}

function MobileView() {
    if (navigator.userAgent.match(/mobile/i)) {
        var isMible = true;
    }

    var rm = $(".right.menu"), m = $(".mobile-view"), p = $(".pc-view");
    var ww = $(window).width(), wh = $(window).height();
    if (isMible) {
        $("#content").css("min-height", wh);
        m.show(300);
        p.hide(250);
        rm.hide(250);
    } else {
        $("#content").css("min-height", "");
        m.hide(250);
        p.show(300);
        rm.show(250);
    }
}

function GetChoosed() {
    $lts = new Array();
    $listGroup = $(".username");
    $checkbox = $listGroup.find(".checkbox");
    $checkbox.each(function () {
        if ($(this).checkbox("is checked")) {
            $lts.push($(this).closest("tr").attr("data-uid"));
        }
    });
    return $lts
}

function GetCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function GetFormVal(FormDom) {
    var fm = $(FormDom);
    return fm.form("get values");
}

function MsgBox(dom, type, title, body, delay) {
    $d = dom ? $(dom) : $("#g_msg");
    tp = type ? type : "info";
    tl = title ? title : "提示!";
    ts = (delay > -1) ? delay : 3000;

    $d.addClass(tp);
    $d.children(".header").text(tl);
    $d.children("p").text(body);

    $d.toggle();
    if (ts) {
        setTimeout(function () {
            $d.toggle()
        }, ts);
    }
}

function ModalBox(title, body) {
    $(".modal .header").text(title);
    $(".modal .content").html(body);
    $(".small.modal").modal("show");
}

/** usersAdd.html start */
$("div.checkbox.add").checkbox({
    onChecked: function () {
        $("div.field.input_zone").removeClass("disabled");
    },
    onUnchecked: function () {
        $("div.field.input_zone").addClass("disabled");
    }
});

var $add_fm = $("#addForm.form");
var $add_btn = $("#addForm .submit");
$add_fm.form({
    on: "change",
    inline: true,
    fields: {
        username: {
            identifier: "username",
            rules: [{
                type: "minLength[7]",
                prompt: "请键入至少一个帐号"
            }]
        },

        password: {
            identifier: "password",
            rules: [{
                type: "minLength[4]",
                prompt: "请键入密码不少于4位"
            }]
        }
    },
    onSuccess: function (event, fields) {
        return true;
    }
});

$add_btn.api({
    action: "api_post",
    urlData: {service: "add"},
    method: "POST",
    transition: "fade down",
    beforeSend: function (settings) {
        ckfm = $add_fm.form('is valid');
        if (!ckfm) {
            return false;
        }
        settings.data = GetFormVal("#addForm");
        return settings;
    },
    onSuccess: function (resp) {
        if (resp.result) {
            $("#addForm.form").form("clear");
            $("input[name=password]").val(1234);
            return MsgBox("#msgBox", "", "提示！", "执行添加中", 5000);
        } else {
            return MsgBox("#msgBox", undefined, resp.msg.detail, 5000);
        }
    },
    onFailure: function (resp) {
        return MsgBox("#msgBox", "error", "提示！", "请求失败。", 5000);
    },
    onError: function (errorMessage, element, xhr) {
        return MsgBox("#msgBox", "error", "提示！", errorMessage, 2500);
    }
});
/** usersAdd.html end */

/** usersList.html start*/
$(".i_call-cw").api({
    action: "work",
    method: "POST",
    beforeSend: function (settings) {
        u = $(this).closest("tr").attr("data-uid");
        s = $(this).attr("data-type");
        settings.urlData.service = "cg";
        settings.data.u = GetChoosed().toString();
        settings.data.v = s;
        settings.data._xsrf = GetCookie("_xsrf");
        return settings;
    },
    onSuccess: function (resp) {
        return MsgBox("#msgBox", "", "提示！", resp.result, 5000);
    }
});

$(".i_call-mn").api({
    action: "work",
    method: "POST",
    beforeSend: function (settings) {
        u = $(this).closest("tr").attr("data-uid");
        s = $(this).attr("data-type");
        settings.urlData.service = "mn";
        settings.data.u = GetChoosed().toString();
        settings.data.v = s;
        settings.data._xsrf = GetCookie("_xsrf");
        return settings;
    },
    onSuccess: function (resp) {
        return MsgBox("#msgBox", "", "提示！", resp.result, 5000);
    }
});

$(".i_progress").api({
    action: "api_get",
    urlData: {service: "process"},
    method: "GET",
    beforeSend: function (settings) {
        u = $(this).closest("tr").attr("data-uid");
        settings.urlData.account = u;
        return settings;
    },
    onSuccess: function (resp) {
        ModalBox("查询结果：", resp.result)
    }
});

$(".i_xue").api({
    action: "api_get",
    urlData: {service: "xue"},
    method: "GET",
    beforeSend: function (settings) {
        u = $(this).closest("tr").attr("data-uid");
        settings.urlData.account = u;
        return settings;
    },
    onSuccess: function (resp) {
        var n = Number(resp.result);
        $(this).text(n.toFixed(2));
    }
});

$(".i_status").api({
    action: "api_get",
    urlData: {service: "status"},
    method: "GET",
    beforeSend: function (settings) {
        u = $(this).closest("tr").attr("data-uid");
        settings.urlData.account = u;
        return settings;
    },
    onSuccess: function (resp) {
        $(this).text(resp.result);
    }
});

$(".i_pwd").api({
    action: "api_post",
    urlData: {service: "pwd"},
    method: "POST",
    beforeSend: function (settings) {
        u = $(this).closest("tr").attr("data-uid");
        settings.data.username = u;
        settings.data._xsrf = GetCookie("_xsrf");
        return settings;
    },
    onSuccess: function (resp) {
        $(this).text(resp.result);
    }
});

$(".i_log").api({
    action: "api_get",
    urlData: {service: "logs"},
    method: "GET",
    beforeSend: function (settings) {
        u = $(this).closest("tr").attr("data-uid");
        settings.urlData.account = u;
        return settings;
    },
    onSuccess: function (resp) {
        rv = resp.result;
        h = "";
        for (var i = rv.length - 1; i >= 0; i--) {
            j = "<pre>" + rv[i] + "</pre>";
            h += j
        }
        ModalBox(resp.account + "查询结果：", h)
    }
});

$(".i_note").api({
    action: "api_get",
    urlData: {service: "note"},
    method: "GET",
    beforeSend: function (settings) {
        u = $(this).closest("tr").attr("data-uid");
        settings.urlData.account = u;
        settings.cxt_dom = $(this);
        return settings;
    },
    onSuccess: function (resp) {
        ModalBox(resp.account + "查询结果：", resp.result)
    }
});

$(".i_call-refresh").bind("click", function () {
    $listGroup = $(".username").find(".checkbox");
    $listGroup.each(function () {
        if ($(this).checkbox("is checked")) {
            $(this).parent().siblings(".i_xue").click()
        }
    })
});

$(".i_call-finish").bind("click", function () {
    lt = GetChoosed();
    for (var i = 0; i < lt.length; i++) {
        u = lt[i];
        $.ajax({
            context: $("tr[data-uid=" + u + "]"),
            url: "/index",
            type: 'delete',
            data: {"username": u, "_xsrf": GetCookie("_xsrf")},
            dataType: "json"
        }).done(function (resp) {
            if (resp.success === true) {
                $(this).remove()
            }
        })
    }
});

$(".i_call-exchange, .i_call-exchange4").bind("click", function () {
    v = this.className.indexOf(4) > 0 && 4 || 1;
    lt = GetChoosed();
    for (var i = 0; i < lt.length; i++) {
        u = lt[i];
        $.ajax({
            url: "/api/exchange/" + u,
            type: 'post',
            data: {"var": v, "username": u, "_xsrf": GetCookie("_xsrf")},
            dataType: "json"
        }).done(function (resp) {
            if (resp.success === true) {
                ModalBox(u + "查询结果：", resp.result)
            } else {
                MsgBox("#msgBox", "warning", "warning", "兑换不成功")
            }
        })
    }
});

$('.ui.search').search({
    minCharacters: 2,
    searchDelay: 1000,
    apiSettings: {
        method: "POST",
        action: 'search',
        beforeSend: function (settings) {
            settings.data.kw = $("input[name=search]").val();
            settings.data._xsrf = GetCookie("_xsrf");
            return settings;
        }
    },
    fields: {
        results: 'items',
        title: 'username',
        description: "notes"
    }
});

// Master Checkboxes //
$("div.master.checkbox").checkbox({
    onChecked: function () {
        var $childCheckbox = $(".username").find(".checkbox");
        $childCheckbox.checkbox("check");
    },
    onUnchecked: function () {
        var $childCheckbox = $(".username").find(".checkbox");
        $childCheckbox.checkbox("uncheck");
    }
});
// Child Checkboxes //
$("div.checkbox.child").checkbox({
    // Fire on load to set parent value
    fireOnInit: true,
    // Change parent state on each child checkbox change
    onChange: function () {
        var $listGroup = $(".username"),
            $parentCheckbox = $(".master.checkbox"),
            $checkbox = $listGroup.find(".checkbox"),
            allChecked = true,
            allUnchecked = true;
        // check to see if all other siblings are checked or unchecked
        $checkbox.each(function () {
            if ($(this).checkbox("is checked")) {
                allUnchecked = false;
            } else {
                allChecked = false;
            }
        });
        // set parent checkbox state, but dont trigger its onChange callback
        if (allChecked) {
            $parentCheckbox.checkbox("set checked");
        } else if (allUnchecked) {
            $parentCheckbox.checkbox("set unchecked");
        } else {
            $parentCheckbox.checkbox("set indeterminate");
        }
    }
});
/** usersList.html end */

/** faceList.html start */
var ft = 'ShiPinTongGuoYuFou="D"; imagestring="$img-str"; GetResult("UploadImage"); SubAnswer()';
$("div[data-btn='copy']").click(function () {
    md5 = $(this).parents().filter('.card').attr("data-md5");
    id = $(this).parents().filter('.card').attr("data-uid");
    $.ajax({
        url: "/api/face/" + id,
        type: 'get',
        data: {"md5": md5},
        dataType: "json"
    }).done(function (resp) {
        $d = $("#" + md5);
        $d.toggle();
        $d.text(ft.replace("$img-str", resp.data));
        $d.select();
        document.execCommand("copy")
        // MsgBox("#msgBox", "", "提示！", "已复制");
    });
});

$("div[data-btn='used']").bind("click", function () {
    $d = $(this).parents().filter('.card');
    md5 = $d.attr("data-md5");
    id = $d.attr("data-uid");
    $.ajax({
        context: $d,
        url: "/api/face/" + id,
        type: 'delete',
        data: {"md5": md5, "_xsrf": GetCookie("_xsrf")},
        dataType: "json"
    }).done(function (resp) {
        if (resp.result) {
            $(this).toggle()
        }
    })
});
/** faceList.html end */

$(window).load(MobileView);
$(window).resize(MobileView);

$("#msgBox .close").on("click", function () {
    $(this).closest(".message").transition("fade");
});

$(".launch.icon").on("click", function () {
    $(".ui.sidebar").sidebar("toggle");
});

$("i_sync").bind("click", function () {
    DoSync("sync")
});
