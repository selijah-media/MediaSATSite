#!/usr/bin/env python3
"""Scans inspiration/ and writes assets/inspiration.js. Runs on every deploy (see .github/workflows/deploy.yml).

  inspiration/<media form>/<Category>/[<Sub>/]file      -> shown in that media form
  inspiration/video+animation/<Category>/...            -> a folder named with + shows in several media forms
  inspiration/also.txt   lines like:  video/Acting > animation, print   (show a folder/file in more forms)
  links.txt in any folder, lines:  Title | https://...  (YouTube/Vimeo play inline; other sites open in the viewer)
"""
import os, re, json, hashlib, urllib.parse as u, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
sys_path = os.path.dirname(os.path.abspath(__file__))
import sys; sys.path.insert(0, sys_path)
import drive_scan
report = []
FORMS = ['video', 'animation', 'print', 'audio', 'photography']
VID = ('.mp4', '.mov', '.webm', '.m4v'); IMG = ('.jpg', '.jpeg', '.png', '.gif', '.webp'); AUD = ('.mp3', '.wav', '.m4a', '.ogg', '.aac')
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); base = os.path.join(root, 'inspiration')
def nice(s):
    s = re.sub(r"(?<=[A-Za-z])_s\b", "'s", s.strip())
    s = s.strip().strip('_').replace('_', ' ').strip()
    return s[:1].upper() + s[1:]
def nkey(s): return [(0, int(x), '') if x.isdigit() else (1, 0, x.lower()) for x in re.findall(r'\d+|\D+', s)]
def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
def scan(d):
    items, seen, fd = [], {}, os.path.join(base, d)
    for dp, dn, fn in os.walk(fd):
        dn.sort()
        rel = os.path.relpath(dp, fd); parts = [] if rel == '.' else rel.split(os.sep)
        cat = nice(parts[0]) if parts else 'General'; sub = ' / '.join(nice(x) for x in parts[1:])
        files = [n for n in sorted(fn, key=nkey) if not n.startswith('.') and not n.lower().startswith('readme') and n.lower() not in ('hotspots.json', 'set.txt')]
        url = lambda n: 'inspiration/' + '/'.join(u.quote(x) for x in [d] + parts + [n])
        mk = os.path.join(dp, 'set.txt'); has_mk = os.path.exists(mk)   # set.txt = everything in this folder (images and videos) is one set
        imgs = [n for n in files if os.path.splitext(n)[1].lower() in IMG or (has_mk and os.path.splitext(n)[1].lower() in VID)]
        if len(imgs) >= 2 or (has_mk and imgs):   # several images in one folder = one slide set
            hp = os.path.join(dp, 'hotspots.json'); H = json.load(open(hp)) if os.path.exists(hp) else {}
            it = dict(title=(open(mk, encoding='utf-8').readline().strip() if has_mk else '') or (nice(parts[-1]) if parts else 'Image set'), type='set', srcs=[url(n) for n in imgs], cats=[[cat, sub]], _rel='/'.join([d] + parts))
            if H: it['hot'] = [H.get(n, []) for n in imgs]
            items.append(it)
        for n in files:
            e = os.path.splitext(n)[1].lower(); r = '/'.join([d] + parts + [n])
            if n.lower() == 'links.txt':
                for line in open(os.path.join(dp, n), encoding='utf-8'):
                    if '|' in line and line.split('|', 1)[1].strip().startswith('http'):
                        t, l = line.split('|', 1)
                        items.append(dict(title=t.strip(), type='link', src=l.strip(), cats=[[cat, sub]], _rel=r))
                continue
            if n in imgs and (len(imgs) >= 2 or has_mk): continue
            typ = 'video' if e in VID else 'image' if e in IMG else 'audio' if e in AUD else 'pdf' if e == '.pdf' else 'file'
            h = md5(os.path.join(dp, n))
            if h in seen:   # identical file in two folders = one item in two categories
                if [cat, sub] not in seen[h]['cats']: seen[h]['cats'].append([cat, sub])
                continue
            it = dict(title=nice(os.path.splitext(n)[0]), type=typ, src=url(n), cats=[[cat, sub]], _rel=r); seen[h] = it; items.append(it)
    return items
out = {f: [] for f in FORMS}
for d in sorted(os.listdir(base)):
    if not os.path.isdir(os.path.join(base, d)) or d.startswith('.'): continue
    toks = [y.strip().lower() for y in d.split('+')]
    fs = FORMS[:] if 'all' in toks else [x for x in toks if x in FORMS]
    for it in scan(d):
        for f in fs: out[f].append(dict(it))
# --- Google Drive: either DRIVE_LIST_URL (Apps Script web app, no API key) or DRIVE_API_KEY + DRIVE_ROOT_FOLDER_ID ---
def fetch_tree(url):
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(url, timeout=300) as r: return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            if attempt == 2: raise
def tree_to_mock(tree):
    mock = {}
    def index(node):
        kids = []
        for c in node.get('children', []):
            kids.append({k: v for k, v in c.items() if k not in ('children', 'text')})
            if 'text' in c: mock['text:' + c['id']] = c['text']
            if c.get('mimeType') == drive_scan.FOLDER: index(c)
        mock[node['id']] = kids
    index(tree); return mock
try:
    if os.environ.get('DRIVE_LIST_URL'):
        tree = fetch_tree(os.environ['DRIVE_LIST_URL'])
        drive, root_id = drive_scan.Drive(None, tree_to_mock(tree)), tree['id']
    elif os.environ.get('DRIVE_API_KEY') and os.environ.get('DRIVE_ROOT_FOLDER_ID'):
        mock = json.load(open(os.environ['DRIVE_MOCK'])) if os.environ.get('DRIVE_MOCK') else None
        drive, root_id = drive_scan.Drive(os.environ['DRIVE_API_KEY'], mock), os.environ['DRIVE_ROOT_FOLDER_ID']
    elif os.environ.get('DRIVE_ROOT_FOLDER_ID'):
        drive, root_id = drive_scan.PublicDrive(), os.environ['DRIVE_ROOT_FOLDER_ID']
    else: drive = None
    if drive:
        for forms, it in drive_scan.scan(drive, root_id, report):
            for f in forms: out[f].append(dict(it))
    else: report.append('Google Drive not connected yet (see README: add the DRIVE_ROOT_FOLDER_ID variable).')
except Exception as e: report.append('GOOGLE DRIVE ERROR (the site was still built without Drive items): %s' % e)
also = os.path.join(base, 'also.txt')
if os.path.exists(also):
    for line in open(also, encoding='utf-8'):
        if line.strip().startswith('#'): continue
        if '=>' in line:   # <path> => Category / Sub   (adds a category, keeps the original one)
            path, cs = line.split('=>', 1); path = path.strip().strip('/').lower(); cs = [x.strip() for x in cs.strip().split('/')]
            c = [nice(cs[0]), ' / '.join(nice(x) for x in cs[1:])]
            for f in FORMS:
                for it in out[f]:
                    r = it['_rel'].lower()
                    if (r == path or r.startswith(path + '/')) and c not in it['cats']: it['cats'].append(list(c))
            continue
        if '>' not in line: continue
        path, tg = line.split('>', 1); path = path.strip().strip('/').lower()
        tg = [x.strip().lower() for x in tg.split(',') if x.strip().lower() in FORMS]
        for f in FORMS:
            for it in list(out[f]):
                r = it['_rel'].lower()
                if r == path or r.startswith(path + '/'):
                    for t in tg:
                        if t != f: out[t].append(dict(it))
# merge duplicates, unify category spelling
canon = {}
for f in FORMS:
    merged = {}
    for it in out[f]:
        k = it.get('src') or it['srcs'][0]
        if k in merged:
            for c in it['cats']:
                if c not in merged[k]['cats']: merged[k]['cats'].append(c)
        else: merged[k] = dict(it, cats=[list(c) for c in it['cats']])
    out[f] = list(merged.values())
    for it in out[f]:
        for c in it['cats']: c[0] = canon.setdefault(c[0].lower(), c[0])
# websites: upgrade http->https. When online (e.g. on GitHub) also drop dead links and record which sites allow embedding.
import socket
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'}
def embed_form(url):
    m = re.search(r'docs\.google\.com/presentation/d/([\w-]+)', url)
    if m: return 'https://docs.google.com/presentation/d/%s/embed' % m.group(1)
    m = re.search(r'docs\.google\.com/(document|spreadsheets)/d/([\w-]+)', url)
    if m: return 'https://docs.google.com/%s/d/%s/preview' % (m.group(1), m.group(2))
    m = re.search(r'drive\.google\.com/file/d/([\w-]+)', url)
    if m: return 'https://drive.google.com/file/d/%s/preview' % m.group(1)
    return url
def probe(url):   # 'dead', True (embeddable), False (blocks embedding) or None (unknown)
    r = None
    for attempt in (1, 2):
        try:
            r = urllib.request.urlopen(urllib.request.Request(embed_form(url), headers=UA), timeout=10); break
        except urllib.error.HTTPError as e: return 'dead' if e.code in (404, 410) else None
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.gaierror):
                if attempt == 2: return 'dead'
                continue
            return None
        except Exception: return None
    xfo = (r.headers.get('X-Frame-Options') or '').lower(); csp = (r.headers.get('Content-Security-Policy') or '').lower()
    if 'deny' in xfo or 'sameorigin' in xfo: return False
    mm = re.search(r'frame-ancestors([^;]*)', csp)
    if mm and '*' not in mm.group(1).split(): return False
    return True
def online():
    try:
        for s in ('https://github.com', 'https://en.wikipedia.org'): urllib.request.urlopen(urllib.request.Request(s, headers=UA), timeout=8)
        return True
    except Exception: return False
urls = set()
for f in FORMS:
    for it in out[f]:
        if it['type'] == 'link' and not it.get('drive'):
            it['src'] = re.sub(r'^http://', 'https://', it['src'])
            if not re.search(r'youtube\.com/watch|youtu\.be|vimeo\.com', it['src']): urls.add(it['src'])
for dp, dn, fn in os.walk(root):   # links used as clickable areas in PDF pages and slide sets
    for n in fn:
        if n == 'hotspots.json' or (n == 'data.js' and 'assets' in dp):
            for x in re.findall(r'https?://[^"\\\s]+', open(os.path.join(dp, n), encoding='utf-8').read()): urls |= {x, re.sub(r'^http://', 'https://', x)}
EMBED = {}
if online():
    ul = sorted(urls)
    with ThreadPoolExecutor(8) as ex: res = dict(zip(ul, ex.map(probe, ul)))
    dead = {k for k, v in res.items() if v == 'dead'}
    EMBED = {k: v for k, v in res.items() if isinstance(v, bool)}
    for f in FORMS:
        for it in out[f]:
            if it['type'] == 'link' and it['src'] in dead: report.append('REMOVED (dead link): %s  %s' % (it['title'], it['src']))
        out[f] = [it for it in out[f] if not (it['type'] == 'link' and it['src'] in dead)]
    report.append('Embeddable: %d, blocks embedding: %d, unknown: %d' % (sum(EMBED.values()), len(EMBED) - sum(EMBED.values()), len(ul) - len(EMBED) - len(dead)))
else: report.append('Offline: link check skipped (it runs on GitHub when the site is deployed).')
for f in FORMS:
    for it in out[f]: it.pop('_rel', None)
    out[f].sort(key=lambda x: (x['cats'][0][0].lower(), x['cats'][0][1].lower(), x['title'].lower()))
with open(os.path.join(root, 'assets', 'inspiration.js'), 'w', encoding='utf-8') as fh:
    fh.write('const INSPO=' + json.dumps(out, ensure_ascii=False) + ';\nconst EMBED=' + json.dumps(EMBED) + ';')
open(os.path.join(root, 'assets', 'link-report.txt'), 'w').write('\n'.join(report) + '\n')
print({k: len(v) for k, v in out.items()}); print('\n'.join(report))
