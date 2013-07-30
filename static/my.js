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

function toggleLikeButton(el, data) {
    var res = $.parseJSON(data);
    if (res.success) {
        var article_id = el.data('likebutton-itemid');
        var elements = $('[data-likebutton-itemid=' + article_id + ']');

        if (el.hasClass('label-success') || el.hasClass('label-inverse')) {
            elements.toggleClass('label-inverse');
        }
        elements.toggleClass('label-success');
    }
}

function likeButtonOnClick(el) {
    if (el.hasClass('label-success')) {
        dislikeArticle(el);
    } else {
        likeArticle(el);
    }
}

function readArticle(article_id) {
    $.post(
        "/a/read",
        {article_id: article_id},
        function (data) {}
    );
    $('[data-articlehead=' + article_id + ']').removeClass('article-head-unread');
}

function initArticle(article_id) {
    $('#collapse' + article_id).on('shown', function () {
        $('html, body').scrollTop($('#collapse' + article_id).offset().top - 80);
        readArticle(article_id);
        Nav.currentItem = article_id;
    });

    $('[data-toggle="source-popover"]').popover();
}

function likeArticle(el) {
    var article_id = el.data('likebutton-itemid');
    $.post(
        '/a/like',
        {article_id: article_id},
        function (data) {
            toggleLikeButton(el, data);
        }
    );
}

function dislikeArticle(el) {
    var article_id = el.data('likebutton-itemid');
    $.post(
        '/a/dislike',
        {article_id: article_id},
        function (data) {
            toggleLikeButton(el, data);
        }
    );
}

function goToArticle(article_id) {
    article_id = String(article_id);
    var article_idx = article_ids.indexOf(article_id);

    if (!article_id || article_idx == -1) {
        return false;
    }
    if (Nav.currentItem) {
        $('#collapse' + Nav.currentItem).collapse('hide');
    }
    $('#collapse' + article_id).collapse('show');

    Nav.currentItem = article_id;
}

function goToNext() {
    if (!Nav.currentItem) {
        Nav.nextItem = article_ids[0];
    } else {
        var article_id = String(Nav.currentItem);
        var article_idx = article_ids.indexOf(article_id);
        if (article_idx == article_ids.length - 1) {
            return false;
        } else {
            Nav.nextItem = article_ids[article_idx + 1]
        }
    }
    goToArticle(Nav.nextItem);
}

function goToPreviuos() {
    if (!Nav.currentItem) {
        Nav.previousItem = article_ids[article_ids.length - 1];
    } else {
        var article_id = String(Nav.currentItem);
        var article_idx = article_ids.indexOf(article_id);
        if (article_idx == 0) {
            return false;
        } else {
            Nav.previousItem = article_ids[article_idx - 1]
        }
    }
    goToArticle(Nav.previousItem);
}

function markAllPageItemsAsRead() {
    $.post(
        '/a/read-all',
        {article_ids: JSON.stringify(article_ids)},
        function (data) {
            var res = $.parseJSON(data);
            if (res.success) {
                $(".article-head-unread").addClass("article-head-read").removeClass("article-head-unread");
            }
        }
    );
}

function initLikeButtons() {
    $(".like-label").click(function (event) {
        event.stopPropagation();
        likeButtonOnClick($(this))
    });
}

function initHotkeys() {
    $("body").keydown(function (e) {
        if (e.keyCode == 74) { // J down
            goToNext();
        }
        else if (e.keyCode == 75) { // K up
            goToPreviuos();
        }
    });
}

$(document).ready(function () {
    initHotkeys();
    initLikeButtons();
});