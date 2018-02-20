<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{% block title %}SUI Tpl{% endblock %}</title>
    <meta name="viewport" content="initial-scale=1, maximum-scale=1">
    <link rel="shortcut icon" href="/favicon.ico">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">

    <link rel="stylesheet" href="/static/sm.min.css">
    <link rel="stylesheet" href="/static/sm-extend.min.css">
</head>
<body>

{% block body %}

{% endblock %}

<div class="js" hidden>
    {% block js %}
    <script type='text/javascript' src='/static/zepto.min.js' charset='utf-8'></script>
    <script type='text/javascript' src='/static/sm.min.js' charset='utf-8'></script>
    <script type='text/javascript' src='/static/sm-extend.min.js' charset='utf-8'></script>
    {% endblock %}

    <script>$.init()</script>
</div>
</body>
</html>
