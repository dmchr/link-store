javascript:function bklt_sub() {
    var d = document,
        h = d.head,
        l = d.location;

    var sub = function (d, url, title) {
        var b = d.body,
            z = d.createElement('scr' + 'ipt');
        try {
            if (!b)throw(0);
            d.title = '(Saving...) ' + d.title;
            z.setAttribute(
                'src',
                l.protocol +
                    '//thelinkstore.ru/s/add?u=' + encodeURIComponent(url) +
                    '&t=' + title +
                    '&l=' + 'UserName'
            );
            b.appendChild(z);
        } catch (e) {
            alert('Please wait until the page has loaded.');
        }
    };
    if (!h) throw(0);
    var a = h.getElementsByTagName('link');
    if (!a) throw(0);
    for (var i = 0; i < a.length; i++) {
        var rel = a[i].getAttribute('rel');
        var type = a[i].getAttribute('type');
        var url = a[i].getAttribute('href');
        var title = a[i].getAttribute('title');
        if (rel == 'alternate' && (type == 'application/atom+xml' || type == 'application/rss+xml')) {
            var msg = 'Subscribe to feed: ' + title + ' (' + url + ')';
            if (confirm(msg)){
                sub(d, url, d.title);
                console.log(msg);
                break;
            }
        }
    }
}
bklt_sub();
void(0)