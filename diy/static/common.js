/*! 2017-07-07 */
function DoSync(a,b,c){c=void 0===c?0:c,$.post({url:"/sync",data:{action:a,node:b,all:c,_xsrf:GetCookie("_xsrf"),ref:window.location.hostname}}).done(function(a){return MsgBox("#msgBox","","请求结果",a.result,2500)})}function MobileView(){if(navigator.userAgent.match(/mobile/i))var a=!0;var b=$(".right.menu"),c=$(".mobile-view"),d=$(".pc-view"),e=($(window).width(),$(window).height());a?($("#content").css("min-height",e),c.show(300),d.hide(250),b.hide(250)):($("#content").css("min-height",""),c.hide(250),d.show(300),b.show(250))}function GetChoosed(){return $lts=new Array,$listGroup=$(".username"),$checkbox=$listGroup.find(".checkbox"),$checkbox.each(function(){$(this).checkbox("is checked")&&$lts.push($(this).closest("tr").attr("data-uid"))}),$lts}function GetCookie(a){var b=document.cookie.match("\\b"+a+"=([^;]*)\\b");return b?b[1]:void 0}function GetFormVal(a){return $(a).form("get values")}function MsgBox(a,b,c,d,e){$d=a?$(a):$("#g_msg"),tp=b||"info",tl=c||"提示!",ts=e>-1?e:3e3,$d.addClass(tp),$d.children(".header").text(tl),$d.children("p").text(d),$d.toggle(),ts&&setTimeout(function(){$d.toggle()},ts)}function ModalBox(a,b){$(".modal .header").text(a),$(".modal .content").html(b),$(".small.modal").modal("show")}$.fn.api.settings.throttle=1500,$.fn.api.settings.api={search:"/search",work:"/do/{service}",api_get:"/api/{service}/{account}",api_post:"/api/{service}"},$("div.checkbox.add").checkbox({onChecked:function(){$("div.field.input_zone").removeClass("disabled")},onUnchecked:function(){$("div.field.input_zone").addClass("disabled")}});var $add_fm=$("#addForm.form"),$add_btn=$("#addForm .submit");$add_fm.form({on:"change",inline:!0,fields:{username:{identifier:"username",rules:[{type:"minLength[7]",prompt:"请键入至少一个帐号"}]},password:{identifier:"password",rules:[{type:"minLength[4]",prompt:"请键入密码不少于4位"}]}},onSuccess:function(a,b){return!0}}),$add_btn.api({action:"api_post",urlData:{service:"add"},method:"POST",transition:"fade down",beforeSend:function(a){return ckfm=$add_fm.form("is valid"),!!ckfm&&(a.data=GetFormVal("#addForm"),a)},onSuccess:function(a){return a.result?($("#addForm.form").form("clear"),$("input[name=password]").val(1234),MsgBox("#msgBox","","提示！","执行添加中",5e3)):MsgBox("#msgBox",void 0,a.msg.detail,5e3)},onFailure:function(a){return MsgBox("#msgBox","error","提示！","请求失败。",5e3)},onError:function(a,b,c){return MsgBox("#msgBox","error","提示！",a,2500)}}),$(".i_call-cw").api({action:"work",method:"POST",beforeSend:function(a){return u=$(this).closest("tr").attr("data-uid"),s=$(this).attr("data-type"),a.urlData.service="cg",a.data.u=GetChoosed().toString(),a.data.v=s,a.data._xsrf=GetCookie("_xsrf"),a},onSuccess:function(a){return MsgBox("#msgBox","","提示！",a.result,5e3)}}),$(".i_call-mn").api({action:"work",method:"POST",beforeSend:function(a){return u=$(this).closest("tr").attr("data-uid"),s=$(this).attr("data-type"),a.urlData.service="mn",a.data.u=GetChoosed().toString(),a.data.v=s,a.data._xsrf=GetCookie("_xsrf"),a},onSuccess:function(a){return MsgBox("#msgBox","","提示！",a.result,5e3)}}),$(".i_progress").api({action:"api_get",urlData:{service:"process"},method:"GET",beforeSend:function(a){return u=$(this).closest("tr").attr("data-uid"),a.urlData.account=u,a},onSuccess:function(a){ModalBox("查询结果：",a.result)}}),$(".i_xue").api({action:"api_get",urlData:{service:"xue"},method:"GET",beforeSend:function(a){return u=$(this).closest("tr").attr("data-uid"),a.urlData.account=u,a},onSuccess:function(a){var b=Number(a.result);$(this).text(b.toFixed(2))}}),$(".i_status").api({action:"api_get",urlData:{service:"status"},method:"GET",beforeSend:function(a){return u=$(this).closest("tr").attr("data-uid"),a.urlData.account=u,a},onSuccess:function(a){$(this).text(a.result)}}),$(".i_pwd").api({action:"api_post",urlData:{service:"pwd"},method:"POST",beforeSend:function(a){return u=$(this).closest("tr").attr("data-uid"),a.data.username=u,a.data._xsrf=GetCookie("_xsrf"),a},onSuccess:function(a){$(this).text(a.result)}}),$(".i_log").api({action:"api_get",urlData:{service:"logs"},method:"GET",beforeSend:function(a){return u=$(this).closest("tr").attr("data-uid"),a.urlData.account=u,a},onSuccess:function(a){rv=a.result,h="";for(var b=rv.length-1;b>=0;b--)j="<pre>"+rv[b]+"</pre>",h+=j;ModalBox(a.account+"查询结果：",h)}}),$(".i_note").api({action:"api_get",urlData:{service:"note"},method:"GET",beforeSend:function(a){return u=$(this).closest("tr").attr("data-uid"),a.urlData.account=u,a.cxt_dom=$(this),a},onSuccess:function(a){ModalBox(a.account+"查询结果：",a.result)}}),$(".i_call-refresh").bind("click",function(){$listGroup=$(".username").find(".checkbox"),$listGroup.each(function(){$(this).checkbox("is checked")&&$(this).parent().siblings(".i_xue").click()})}),$(".i_call-finish").bind("click",function(){lt=GetChoosed();for(var a=0;a<lt.length;a++)u=lt[a],$.ajax({context:$("tr[data-uid="+u+"]"),url:"/index",type:"delete",data:{username:u,_xsrf:GetCookie("_xsrf")},dataType:"json"}).done(function(a){!0===a.success&&$(this).remove()})}),$(".i_call-exchange, .i_call-exchange4").bind("click",function(){v=this.className.indexOf(4)>0&&4||1,lt=GetChoosed();for(var a=0;a<lt.length;a++)u=lt[a],$.ajax({url:"/api/exchange/"+u,type:"post",data:{var:v,username:u,_xsrf:GetCookie("_xsrf")},dataType:"json"}).done(function(a){!0===a.success?ModalBox(u+"查询结果：",a.result):MsgBox("#msgBox","warning","warning","兑换不成功")})}),$(".ui.search").search({minCharacters:2,searchDelay:1e3,apiSettings:{method:"POST",action:"search",beforeSend:function(a){return a.data.kw=$("input[name=search]").val(),a.data._xsrf=GetCookie("_xsrf"),a}},fields:{results:"items",title:"username",description:"notes"}}),$("div.master.checkbox").checkbox({onChecked:function(){$(".username").find(".checkbox").checkbox("check")},onUnchecked:function(){$(".username").find(".checkbox").checkbox("uncheck")}}),$("div.checkbox.child").checkbox({fireOnInit:!0,onChange:function(){var a=$(".username"),b=$(".master.checkbox"),c=a.find(".checkbox"),d=!0,e=!0;c.each(function(){$(this).checkbox("is checked")?e=!1:d=!1}),d?b.checkbox("set checked"):e?b.checkbox("set unchecked"):b.checkbox("set indeterminate")}}),$(window).load(MobileView),$(window).resize(MobileView),$("#msgBox .close").on("click",function(){$(this).closest(".message").transition("fade")}),$(".launch.icon").on("click",function(){$(".ui.sidebar").sidebar("toggle")}),$("i_sync").bind("click",function(){DoSync("sync")});