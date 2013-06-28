Nav = {
    nextItem: 0,
    previousItem: 0,
    currentItem: 0
}

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
        Nav.currentItem = article_id;
    });
    $('[data-toggle="source-popover"]').popover();
}

function goToArticle(article_id){
    article_id = String(article_id);
    var article_idx = article_ids.indexOf(article_id);

    if (!article_id || article_idx == -1){
        return false;
    }
    if (Nav.currentItem){
        $('#collapse' + Nav.currentItem).collapse('hide');
    }
    $('#collapse' + article_id).collapse('show');

    Nav.currentItem = article_id;
}

function goToNext(){
    if (!Nav.currentItem){
        Nav.nextItem = article_ids[0];
    } else {
        var article_id = String(Nav.currentItem);
        var article_idx = article_ids.indexOf(article_id);
        if (article_idx == article_ids.length - 1){
            return false;
        } else {
            Nav.nextItem = article_ids[article_idx + 1]
        }
    }
    goToArticle(Nav.nextItem);
}

function goToPreviuos(){
    if (!Nav.currentItem){
        Nav.previousItem = article_ids[article_ids.length - 1];
    } else {
        var article_id = String(Nav.currentItem);
        var article_idx = article_ids.indexOf(article_id);
        if (article_idx == 0){
            return false;
        } else {
            Nav.previousItem = article_ids[article_idx - 1]
        }
    }
    goToArticle(Nav.previousItem);
}

$(document).ready(function () {
    $("body").keydown(function (e) {
        if (e.keyCode == 74) { // J down
            goToNext();
        }
        else if (e.keyCode == 75) { // K up
            goToPreviuos();
        }
    });
});