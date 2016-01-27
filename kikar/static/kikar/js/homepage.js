function requestAndAddStatuses(url) {
    var contentMaxLength = 200;
    $.ajax({
        url: url, contentType: "application/json", success: function (data) {
            var listContainer = $('#kikar-facebook-updates-ul');
            var nextBatchOfStatuses = $('#statuses-more');
            nextBatchOfStatuses.data('next', 'http://localhost:8000' + data.meta.next);

            data.objects.forEach(function (element, index, array) {
                //console.log(element);
                var source = $('#facebook-status-template').html();
                var template = Handlebars.compile(source);
                var testElem = {member: "test", party: "test2"};
                var html = template(element);
                //var htmlElem = $.parseHTML("<li class='agenda-mini clearfix'>" + element.content.substring(0, contentMaxLength) + "</li>");
                listContainer.append(html);
            });
        }
    });
}

$(document).ready(function () {
    var url = 'http://localhost:8000/api/v1/facebook_status/?limit=5';
    requestAndAddStatuses(url);

    $('#statuses-more').on("click", function (event) {
        url = $(this).data('next');
        requestAndAddStatuses(url);
    })
});