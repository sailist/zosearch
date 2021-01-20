#!/usr/bin/env python3
import os
from itertools import chain
import fire

import rich
from whoosh.fields import *
from whoosh.index import create_in
from whoosh.index import open_dir
from whoosh.query import *


import re

zopath_f = os.path.join(os.path.expanduser('~'),'.zosearch')
os.makedirs(zopath_f,exist_ok=True)
zopath_f = os.path.join(os.path.expanduser('~'),'.zosearch','zopath')


try:
    with open(zopath_f) as r:
        zopath = r.read().strip()
        if len(zopath) == 0:
            raise RuntimeError()
except:
    print('please create file "zopath" and write Zotero root path.("{}")'.format(os.path.dirname(zopath_f)))
    exit(1)

indexdir = os.path.join(zopath, 'whoosh')
storgedir = os.path.join(zopath, 'storage')

match_highlight = re.compile('<b class="match term([0-9]+)">([^<]+)<\/b>')


def index():
    schema = Schema(title=TEXT(stored=True, spelling_prefix=True),
                    zohash=ID(stored=True),
                    content=TEXT(stored=True, spelling_prefix=True), path=TEXT(stored=True))

    zopath = '/Users/yanghaozhe/Zotero/'
    indexdir = os.path.join(zopath, 'whoosh')
    storgedir = os.path.join(zopath, 'storage')

    if not os.path.exists(indexdir):
        os.mkdir(indexdir)
    ix = create_in(indexdir, schema)

    # TODO 增量备份
    # indexkeyf = os.path.join(zopath, 'whoosh.key')
    # if os.path.exists(indexkeyf):
    #     keys = pickle.load(indexkeyf)
    # else:
    #     keys = {}

    writer = ix.writer()

    for fdir in os.listdir(storgedir):
        _cache_f = os.path.join(storgedir, fdir, '.zotero-ft-cache')
        if not os.path.exists(_cache_f):
            continue
        with open(_cache_f, 'r', encoding='utf-8') as r:
            content = r.read()

        _pdf = [i for i in os.listdir(os.path.join(storgedir, fdir)) if i.endswith('pdf')][0]
        _pre, _ = os.path.splitext(_pdf)
        title = _pre.split(' - ')[-1]

        path = os.path.join(fdir, _pdf)
        writer.add_document(title=title, content=content, zohash=fdir, path=path)

    writer.commit()
    print("find {} docs.".format(ix.doc_count()))


def search(*content: str):
    ix = open_dir(indexdir)
    searcher = ix.searcher()


    items = list(chain(*[i.split(' ') for i in content]))
    items = [Term('title', item) for item in items] + [Term('content', item) for item in items]

    quary = Or(items)

    results = searcher.search(q=quary)
    print('Find results({}/{}):\n'.format(len(results), searcher.doc_count()))
    for i in range(len(results)):
        res = results[i].fields()
        path = res['path']
        title = results[i].highlights('title').split('...')[0]
        if len(title.strip()) == 0:
            title = res['title']
        results.fragmenter.surround = 75
        contents = results[i].highlights('content').replace('\n', ' ').split('...')

        title = re.sub(match_highlight,
                       lambda k: '[bold red]{}[/bold red][bold magenta]{}[/bold magenta]'.format(k.group(2), ''),
                       title)

        contents = [re.sub(match_highlight,
                           lambda k: '[bold yellow]{}[/bold yellow][bold magenta]{}[/bold magenta]'.format(k.group(2), ''),
                           i) for i in contents]

        rich.print("{}. ".format(i+1) + title)
        for content in contents:
            rich.print(' - ' + content)
        print()


def manage(*args,**kwargs):
    if len(args) == 0:
        args = ['index']
    func = args[0]
    if func == 'index':
        print('run index')
        index()
    elif func == 's' or func == 'search':
        search(*args[1:])

    print('bye.')

fire.Fire(manage)
# search('meta','pseudo')