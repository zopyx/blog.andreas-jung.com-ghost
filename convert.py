import orjson
import os
import lxml.html
import pprint
import requests
import shutil
import tempfile
import urllib.parse
from dateutil.parser import parse
from lxml.cssselect import CSSSelector

ROOT = '/Users/ajung/tmp/blog.zopyx.com/andreas-jung'

def find_blogs():

    blogs = list()
    for dirname, dirnames, filenames in os.walk(ROOT):
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

    # date
    sel = CSSSelector('span.label')
    result = sel(root)
    if result:
        date = result[0].text.strip()
        date = parse(date).isoformat()
    else:
        date = '1999-01-01'

    # date
    sel = CSSSelector('.documentDescription')
    result = sel(root)
    if result:
        desc = result[0].text.strip()
    else:
        desc = None

    # body
    sel = CSSSelector('#content-core')
    result = sel(root)
    if result:
        body = lxml.html.tostring(result[0], encoding=str)
    else:
        body = None

    # newsImage
    sel = CSSSelector('.newsImage')
    result = sel(root)
    if result:
        news_image = dict(result[0].attrib)
    else:
        news_image = None

    # images
    images = list()
    sel = CSSSelector('img')
    images = sel(root)
    if images:
        images = [dict(img.attrib) for img in images]

    return dict(
            filename=fn,
            date=date,
            body=body,
            description=desc,
            images=images,
            news_image=news_image,
            title=title)

def import_images(result):

    for d in result:
        images = d['images']
        fn_base = os.path.dirname(d['filename'])
        for image in images:
            src = image['src']
            if src.startswith('http'):
                response = requests.get(src)
                temp_fn = tempfile.mktemp()
                with open(temp_fn, 'wb') as fp:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, fp)    

            else:
                src = urllib.parse.unquote(src)
                image_fn = os.path.join(fn_base, src)
                print(image_fn, os.path.exists(image_fn))

def main():
    result = list()
    blogs = find_blogs()
    for fn in blogs:
        blog_data = extract_blog(fn)
        result.append(blog_data)

    result = sorted(result, key=lambda x: x['date'])

    with open('output.json', 'w') as fp:
        fp.write(orjson.dumps(result, option=orjson.OPT_INDENT_2).decode("utf8"))

    import_images(result)

if __name__ == '__main__':
    main()
