javascript:function bklt() {
    var d = document, z = d.createElement('scr' + 'ipt'), b = d.body, l = d.location;
    try {
        if (!b)throw(0);
        d.title = '(Saving...) ' + d.title;
        z.setAttribute(
            'src',
            l.protocol +
                '//thelinkstore.ru/a/add?u=' + encodeURIComponent(l.href) +
                '&r=' + encodeURIComponent(d.referrer) +
                '&t=' + (new Date().getTime()) +
                '&l=' + 'UserName'
        );
        b.appendChild(z);
    } catch (e) {
        alert('Please wait until the page has loaded.');
    }
}
bklt();
void(0)