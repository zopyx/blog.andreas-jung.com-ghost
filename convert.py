import os
import lxml.html
from lxml.cssselect import CSSSelector

def find_blogs():

    blogs = list()
    for dirname, dirnames, filenames in os.walk("andreas-jung"):
        for fname in filenames:
            if fname.startswith('contents'):
                continue
            if fname in ('image_view_fullscreen.html',) :
                continue
            fname = os.path.join(dirname, fname)
            if 'assets' in fname or 'images' in fname:
                continue
            with open(fname, 'rb') as fp:
                data = fp.read()
            if '<head>' in data.decode('utf8', 'ignore'):
                blogs.append(os.path.abspath(fname))
    return blogs

def extract_blog(fn):

    print(fn)
    with open(fn) as fp:
        html = fp.read()

    root = lxml.html.fromstring(html)
    # title=
    sel = CSSSelector('h1.documentFirstHeading')
    result = sel(root)
    if result:
        title = result[0].text.strip()
    else:
        title = None

    return dict(
            filename=fn,
            title=title)

def main():
    blogs = find_blogs()
    for fn in blogs:
        blog_data = extract_blog(fn)
        print(blog_data)

if __name__ == '__main__':
    main()
