import json
import orjson
import os
import lxml.html
import pprint
import requests
import shutil
import tempfile
import urllib.parse
import html2markdown
from markdownify import markdownify as md
from dateutil.parser import parse
from lxml.cssselect import CSSSelector

ROOTS = ('/Users/ajung/tmp/blog.zopyx.com/andreas-jung',
         '/home/ajung/src/blog.andreas-jung.com-ghost/andreas-jung')

ROOT = next((root for root in ROOTS if os.path.exists(root)), None)
if not ROOT:
    raise IOError('No root directory found')


def find_blogs():

    blogs = []
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
    title = result[0].text.strip() if (result := sel(root)) else None
    # date
    sel = CSSSelector('span.label')
    if result := sel(root):
        date = result[0].text.strip()
        date = f'{parse(date).isoformat()}.000Z'
    else:
        date = '1999-01-01T00:00:00.000Z'

    # date
    sel = CSSSelector('.documentDescription')
    desc = result[0].text.strip() if (result := sel(root)) else None
    # body
    sel = CSSSelector('#content-core')
    if result := sel(root):
        body = lxml.html.tostring(result[0], encoding=str)
    else:
        body = ''

    # body MD
    body_md = md(body)

    # newsImage
    sel = CSSSelector('.newsImage')
    news_image = dict(result[0].attrib) if (result := sel(root)) else None
    # images
    images = []
    sel = CSSSelector('img')
    images = sel(root)
    if images:
        images = [dict(img.attrib) for img in images]

    return dict(
            filename=fn,
            id=os.path.basename(fn),
            date=date,
            body=body,     
            body_md=body_md,
            description=desc,
            images=images,
            news_image=news_image,
            title=title)

def import_posts(result):

    data = dict(username="info@zopyx.com", password="01$$Yetsux")
    headers = {
            'content-type': 'application/json',
            'accept': 'application/json',
            }

    url = 'http://localhost:2368/ghost/api/v3/admin/session'
    response = requests.post(url,
            data=json.dumps(data),
            headers=headers)
    assert response.status_code == 201
    cookie = response.headers["set-cookie"]
    cookie_key, cookie_value = cookie.split('=', 1)
    cookies = {cookie_key: cookie_value}

    authors = [
            {"id": "ajung",
             "name": "Andreas Jung"
    }]

    for d in result:
        html = d['body']
        html = '<p>FOO</p>'
        post = dict(
                slug=d['id'],
                id=d['id'],
                uuid=d['id'],
                published_at=d['date'],
                created_at=d['date'],
                updated_at=d['date'],
                title=d['title'],
                html=html,
                status='published',
                authors=authors)

        data = dict(posts=[post])
        url = 'http://localhost:2368/ghost/api/v3/admin/posts'
        response = requests.post(
                url,
                headers=headers,
                cookies=cookies,
                data=json.dumps(data))
        print(response)

def import_images(result):

    data = dict(username="info@zopyx.com", password="01$$Yetsux")
    headers = {
            'content-type': 'application/json',
            'accept': 'application/json',
            }

    url = 'http://localhost:2368/ghost/api/v3/admin/session'
    response = requests.post(url,
            data=json.dumps(data),
            headers=headers)
    assert response.status_code == 201
    cookie = response.headers["set-cookie"]
    print(cookie)

    cookie_key, cookie_value = cookie.split('=', 1)
    cookies = {cookie_key: cookie_value}

    url = 'http://localhost:2368/ghost/api/v3/admin/posts'
    data = dict(posts=[dict(title="foo", html="<p>XXXXX</p>")])
    import pdb
    pdb.set_trace()
    response = requests.post(
            url,
            headers=headers,
            cookies=cookies,
            data=json.dumps(data))

    url = 'http://localhost:2368/ghost/api/v3/admin/images/upload'
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
                image_fn = temp_fn

            else:
                src = urllib.parse.unquote(src)
                image_fn = os.path.join(fn_base, src)
                print(image_fn, os.path.exists(image_fn))

            files = {
                    'file': open(image_fn, 'rb')
                    }

            response = requests.post(
                    url,
                    cookies=cookies,
                    files=files)

def main():
    result = []
    blogs = find_blogs()
    for fn in blogs:
        blog_data = extract_blog(fn)
        result.append(blog_data)

    result = sorted(result, key=lambda x: x['date'])

    with open('output.json', 'w') as fp:
        fp.write(orjson.dumps(result, option=orjson.OPT_INDENT_2).decode("utf8"))

    import_posts(result)
#    import_images(result)


if __name__ == '__main__':
    main()
