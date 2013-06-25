function createAutoClosingAlert(selector, delay) {
    var alert = $(selector).alert();
    window.setTimeout(function () {
        alert.alert('close')
    }, delay);
}

function toggleLikeButton(article_id, data) {
    var res = $.parseJSON(data);
    if (res.success) {
        $('[data-likebutton=' + article_id + ']').toggleClass('label-success');
    }
}

function readArticle(article_id) {
    $('#collapse' + article_id).on('shown', function () {
        $('html, body').scrollTop($('#collapse' + article_id).offset().top - 80);
        $.post(
            "/a/read",
            {article_id: article_id},
            function (data) {
            }
        );
        $('[data-articlehead=' + article_id + ']').removeClass('article-head-unread');
    });
    $('[data-toggle="source-popover"]').popover();
}

$(document).ready(function () {
    $("body").keydown(function (e) {
        if (e.keyCode == 74) { // J down

        }
        else if (e.keyCode == 75) { // K up

        }
    });
});