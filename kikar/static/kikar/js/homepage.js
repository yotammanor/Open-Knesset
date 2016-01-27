$(document).ready(function () {
    var kikarUrlBase = 'http://www.kikar.org';
    var loadingSymbol = $('#loading-statuses-symbol');
    var statusNumLimitPerRequest = 5;
    function requestAndAddStatuses(url) {
        var requestURL = '/kikar/get-statuses/?path=' + encodeURI(url);
        console.log(requestURL);
        loadingSymbol.show();
        var listContainer = $('#kikar-facebook-updates-ul');
        $.ajax({
            url: requestURL, contentType: "application/json",
            success: function (data) {
                var nextBatchOfStatuses = $('#statuses-more');
                nextBatchOfStatuses.data('next', kikarUrlBase + data.meta.next);
                loadingSymbol.hide();
                data.objects.forEach(function (element, index, array) {
                    //console.log(element);
                    var source = $('#facebook-status-template').html();
                    var template = Handlebars.compile(source);
                    var testElem = {member: "test", party: "test2"};
                    var html = template(element);
                    //var htmlElem = $.parseHTML("<li class='agenda-mini clearfix'>" + element.content.substring(0, contentMaxLength) + "</li>");
                    listContainer.append(html);
                });
            },
            error: function () {
                loadingSymbol.hide();
                listContainer.append("<p>התנצלותינו הכנה, ישנה תקלה בקטעינת הסטאטוס.</p>")
            }
        });
    }

    var url = kikarUrlBase + '/api/v1/facebook_status/?limit=' + statusNumLimitPerRequest;
    requestAndAddStatuses(url);

    $('#statuses-more').on("click", function (event) {
        url = $(this).data('next');
        requestAndAddStatuses(url);
    })
});