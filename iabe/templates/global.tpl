<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>{% block title %}Global Tpl{% endblock %}</title>

    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <meta name="referrer" content="no-referrer-when-downgrade">
    <meta name="description" content="description">
    <meta name="keywords" content="keywords">

    {% block css %}{% endblock %}
</head>

<body>
{% block body %}{% endblock %}

{% block footer %}
    <div id="foo" style="display: flex; justify-content: center;">
        <script>
            document.getElementById("foo").innerHTML = "&copy; Copyright " + new Date().getFullYear();
        </script>
    </div>
{% endblock %}

<div id="js" style="display: none">
    <script type="text/javascript" src="//code.jquery.com/jquery-2.2.4.min.js"></script>
    {% block js %}{% endblock %}
</div>

</body>
</html>
