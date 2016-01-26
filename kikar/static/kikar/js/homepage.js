
$(document).ready(function () {
    var contentMaxLength = 200;
    var url = 'http://localhost:8000/en/api/v1/facebook_status/?limit=5';
    $.ajax({
        url: url, contentType: "application/json", success: function (data) {
            var listContainer = $('#kikar-facebook-updates-ul');
            data.objects.forEach(function (element, index, array) {
                console.log(element);
                var htmlElem = $.parseHTML("<li class='agenda-mini clearfix'>" + element.content.substring(0, contentMaxLength) + "</li>");
                listContainer.append(htmlElem);
            });
        }
    });
});