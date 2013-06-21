function createAutoClosingAlert(selector, delay) {
   var alert = $(selector).alert();
   window.setTimeout(function() { alert.alert('close') }, delay);
}

function toggleLikeButton(news_id, data){
    var res = $.parseJSON(data);
    if (res.success){
        $('[data-likebutton='+news_id+']').toggleClass('label-success');
    }
}
