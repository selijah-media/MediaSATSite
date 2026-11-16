#!/usr/bin/env python3
"""Reads the public Google Drive folders for Top Design, Copyright and SAT PACKS, downloads each PDF
(or Word / PowerPoint file), turns it into page pictures with clickable links, and writes assets/drivedocs.js.

Runs on GitHub every night (and on every upload). Nothing big has to be uploaded to GitHub by hand:
the pictures are made fresh inside the build and published with the site.

Drive layout it understands
  Top Design Files / 2025.pdf, 2024.pdf ...                 -> "VCAA Top Design" menu (one entry per file, newest first)
  Copyright / any PDFs, Word files, folders ...             -> tiles on the Copyright page
  SAT PACKS / SAT PACK 1 / SAT Criteria / *.pdf             -> "SAT 1 Criteria" on every media form
                         / Student Samples / <Form> / files or folders -> "Student Samples" for that form
                         / *.pdf (not criteria)             -> the SAT Pack booklet itself
  (same again for SAT PACK 2 and SAT PACK 3; a folder inside a form folder becomes ONE tile holding all its files)
  A Student Samples folder called "All" or "All Media Forms" feeds every media form.
"""
import json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drive_scan as ds
from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, 'assets', 'dd')
UA = ds.PublicDrive.UA
VID = ('.mp4', '.mov', '.m4v', '.webm'); IMG = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
OFFICE = ('.docx', '.doc', '.pptx', '.ppt', '.odt', '.odp')
log = []

def ext(n): return os.path.splitext(n.lower())[1]
def title_of(n):
    t = os.path.splitext(n)[0] if ext(n) in ('.pdf',) + VID + IMG + OFFICE else n
    return re.sub(r'\s+', ' ', t.replace('_', ' ')).strip()
def clean_url(u):
    return re.sub(r'[?&]utm_[a-z]+=[^&]*', '', u).rstrip('?&')

# ---------- downloading ----------
def fetch_default(fid, dest, want):
    for url in ('https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t' % fid,
                'https://drive.google.com/uc?export=download&id=%s&confirm=t' % fid):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r: data = r.read()
        except Exception: continue
        if data[:len(want)] == want:
            open(dest, 'wb').write(data); return True
    return False

# ---------- PDF -> page pictures ----------
def render_pdf(pdf, prefix, width=1500, q=80):
    os.makedirs(OUT_DIR, exist_ok=True)
    subprocess.run(['pdftoppm', '-jpeg', '-jpegopt', 'quality=%d,optimize=y,progressive=y' % q, '-scale-to-x', str(width), '-scale-to-y', '-1',
                    pdf, os.path.join(OUT_DIR, prefix)], check=True, timeout=900)
    files = sorted(f for f in os.listdir(OUT_DIR) if re.fullmatch(re.escape(prefix) + r'-\d+\.jpg', f))
    r = PdfReader(pdf); pages = []
    for i, pg in enumerate(r.pages):
        links = []
        try:
            W = float(pg.mediabox.width); H = float(pg.mediabox.height)
            for a in pg.get('/Annots') or []:
                a = a.get_object()
                if a.get('/Subtype') != '/Link': continue
                x1, y1, x2, y2 = [float(v) for v in a['/Rect']]
                x1, x2 = min(x1, x2), max(x1, x2); y1, y2 = min(y1, y2), max(y1, y2)
                t = None
                act = a.get('/A')
                if act is not None:
                    act = act.get_object()
                    if '/URI' in act: t = clean_url(str(act['/URI']))
                    elif '/D' in act: t = dest_page(r, act['/D'])
                elif '/Dest' in a: t = dest_page(r, a['/Dest'])
                if t is None: continue
                links.append([round(x1 / W * 100, 2), round((H - y2) / H * 100, 2), round((x2 - x1) / W * 100, 2), round((y2 - y1) / H * 100, 2), t])
        except Exception: pass
        if i < len(files): pages.append({'s': 'assets/dd/' + files[i], 'l': links})
    if files:
        subprocess.run(['pdftoppm', '-jpeg', '-f', '1', '-l', '1', '-scale-to-x', '400', '-scale-to-y', '-1', '-singlefile', pdf,
                        os.path.join(OUT_DIR, prefix + '-th')], check=True, timeout=300)
    return pages

def dest_page(r, d):
    try:
        if isinstance(d, str): return r.get_destination_page_number(r.named_destinations[d])
        return r.get_page_number(d[0].get_object())
    except Exception: return None

# ---------- one Drive item -> (pages, thumbnail, download link) ----------
class Ctx:
    def __init__(self, drive, fetch=fetch_default, tmp=None):
        self.drive, self.fetch, self.tmp = drive, fetch, tmp or tempfile.mkdtemp()
        self.soffice = shutil.which('soffice') or shutil.which('libreoffice')

def item(ctx, f):
    """Returns dict(t, p, th, dl) for one Drive file, or None."""
    n, fid, m = f['name'], f['id'], f.get('mimeType', '')
    e = ext(n); t = title_of(n)
    if n.lower() in ('links.txt', 'thumbs.db', '.ds_store') or n.startswith('~$'): return None
    dl = 'https://drive.google.com/uc?export=download&id=' + fid
    if e == '.pdf' or m.endswith('/pdf'):
        pdf = os.path.join(ctx.tmp, fid + '.pdf')
        if ctx.fetch(fid, pdf, b'%PDF'):
            try:
                p = render_pdf(pdf, fid)
                if p: return dict(t=t, p=p, th='assets/dd/%s-th.jpg' % fid, dl=dl)
            except Exception as ex: log.append('  could not render %s: %s' % (n, ex))
        log.append('  %s could not be downloaded, showing Google\'s own viewer instead' % n)
        return dict(t=t, p=[{'s': ds.prev(fid), 'l': []}], th=ds.thumb(fid).replace('w2000', 'w400'), dl=dl)
    if e in OFFICE and ctx.soffice:
        src = os.path.join(ctx.tmp, fid + e)
        if ctx.fetch(fid, src, b'PK' if e[-1] == 'x' else b''):
            try:
                subprocess.run([ctx.soffice, '--headless', '--convert-to', 'pdf', '--outdir', ctx.tmp, src], check=True, timeout=240, capture_output=True)
                pdf = os.path.join(ctx.tmp, fid + '.pdf')
                p = render_pdf(pdf, fid)
                if p: return dict(t=t, p=p, th='assets/dd/%s-th.jpg' % fid, dl=dl)
            except Exception as ex: log.append('  could not convert %s: %s' % (n, ex))
    if e in IMG or m.startswith('image/'):
        return dict(t=t, p=[{'s': ds.thumb(fid), 'l': []}], th=ds.thumb(fid).replace('w2000', 'w400'), dl=dl)
    if 'google-apps.document' in m: return dict(t=t, p=[{'s': 'https://docs.google.com/document/d/%s/preview' % fid, 'l': []}], th=ds.thumb(fid).replace('w2000', 'w400'))
    if 'google-apps.presentation' in m: return dict(t=t, p=[{'s': 'https://docs.google.com/presentation/d/%s/preview' % fid, 'l': []}], th=ds.thumb(fid).replace('w2000', 'w400'))
    if 'google-apps.spreadsheet' in m: return dict(t=t, p=[{'s': 'https://docs.google.com/spreadsheets/d/%s/preview' % fid, 'l': []}], th=ds.thumb(fid).replace('w2000', 'w400'))
    if 'google-apps' in m: return None
    # videos, Office files without a converter, anything else Drive can preview
    return dict(t=t, p=[{'s': ds.prev(fid), 'l': []}], th=ds.thumb(fid).replace('w2000', 'w400'), dl=dl)

def folder_docs(ctx, fid, depth=0):
    """Every file becomes a tile; every sub-folder becomes ONE tile holding all of its files."""
    docs = []
    kids = sorted((ds.resolve(k) for k in ctx.drive.children(fid)), key=lambda k: ds.nkey(k['name']))
    for k in kids:
        if k['mimeType'] == ds.FOLDER:
            if depth >= 3: continue
            inner = [d for d in folder_docs(ctx, k['id'], depth + 1)]
            if not inner: continue
            pages = [pg for d in inner for pg in d['p']]
            name = re.sub(r'^samples?\s*[-–:]\s*', '', k['name'], flags=re.I).strip() or k['name']
            docs.append(dict(t=name, p=pages, th=inner[0].get('th')))
        else:
            d = item(ctx, k)
            if d: docs.append(d)
    return docs

def find_child(ctx, fid, pred):
    for k in ctx.drive.children(fid):
        k = ds.resolve(k)
        if k['mimeType'] == ds.FOLDER and pred(ds.nz(k['name'])): return k['id']
    return None

# ---------- the three sections ----------
def top_design(ctx, fid):
    docs = folder_docs(ctx, fid)
    def yr(d):
        m = re.search(r'(20\d\d)', d['t']); return int(m.group(1)) if m else 0
    docs.sort(key=lambda d: (-yr(d), d['t']))
    for d in docs:
        y = yr(d)
        d['n'] = d['t']; d['t'] = str(y) if y else d['t']
    return docs

def sat_packs(ctx, fid, res):
    for k in sorted((ds.resolve(x) for x in ctx.drive.children(fid)), key=lambda x: ds.nkey(x['name'])):
        m = re.search(r'pack\s*([123])\b', ds.nz(k['name']))
        if not m or k['mimeType'] != ds.FOLDER: continue
        n = m.group(1)
        for c in sorted((ds.resolve(x) for x in ctx.drive.children(k['id'])), key=lambda x: ds.nkey(x['name'])):
            nm = ds.nz(c['name'])
            if c['mimeType'] == ds.FOLDER and 'criteria' in nm:
                res['c'][n] = folder_docs(ctx, c['id'])
            elif c['mimeType'] == ds.FOLDER and 'sample' in nm:
                for ff in sorted((ds.resolve(x) for x in ctx.drive.children(c['id'])), key=lambda x: ds.nkey(x['name'])):
                    if ff['mimeType'] != ds.FOLDER: continue
                    forms = ds.parse_forms(ff['name'])
                    if not forms: log.append('  folder "%s" in Student Samples is not a media form name, skipped' % ff['name']); continue
                    docs = folder_docs(ctx, ff['id'])
                    for fm in forms: res['s'].setdefault(n, {}).setdefault(fm, []).extend(docs)
            elif c['mimeType'] != ds.FOLDER:
                d = item(ctx, c)
                if d: res['c' if 'criteria' in nm else 'pk'].setdefault(n, []).append(d)
        for key in ('c', 'pk'):
            if n in res[key] and not res[key][n]: del res[key][n]

def build(drive, folders, root_id, fetch=fetch_default):
    ctx = Ctx(drive, fetch)
    res = dict(status='ok', td=[], cr=[], c={}, pk={}, s={})
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    def pick(key, names):
        fid = folders.get(key)
        if not fid and root_id:
            fid = find_child(ctx, root_id, lambda n: any(x in n for x in names))
        return fid
    for key, names, fn in (('topdesign', ('top design',), lambda fid: res.update(td=top_design(ctx, fid))),
                           ('copyright', ('copyright',), lambda fid: res.update(cr=folder_docs(ctx, fid))),
                           ('satpacks', ('sat packs', 'sat pack'), lambda fid: sat_packs(ctx, fid, res))):
        fid = pick(key, names)
        if not fid: log.append('%s: folder not found. Paste its link into tools/drive_folders.json' % key); continue
        try:
            fn(fid)
            cnt = len(res['td']) if key == 'topdesign' else len(res['cr']) if key == 'copyright' else sum(len(v) for v in res['c'].values()) + sum(len(d) for v in res['s'].values() for d in v.values()) + sum(len(v) for v in res['pk'].values())
            log.append('%s: %d document(s)' % (key, cnt))
        except Exception as ex:
            res['status'] = 'error'; log.append('%s: ERROR %s' % (key, ex))
    return res

def main():
    cfg = json.load(open(os.path.join(ROOT, 'tools', 'drive_folders.json')))
    folders = {k: v.strip() for k, v in cfg.items() if not k.startswith('_') and isinstance(v, str)}
    for k, v in folders.items():
        m = re.search(r'folders/([\w-]+)', v)
        if m: folders[k] = m.group(1)
    key = os.environ.get('DRIVE_API_KEY')
    drive = ds.Drive(key) if key else ds.PublicDrive()
    try: res = build(drive, folders, os.environ.get('DRIVE_ROOT_FOLDER_ID'))
    except Exception as ex:
        res = dict(status='error', td=[], cr=[], c={}, pk={}, s={}); log.append('GOOGLE DRIVE ERROR (documents): %s' % ex)
    open(os.path.join(ROOT, 'assets', 'drivedocs.js'), 'w').write('const DRIVEDOCS=' + json.dumps(res, ensure_ascii=False) + ';')
    print('### Documents from Google Drive (Top Design, Copyright, SAT Packs)')
    for l in log: print(l)
    print('pages written: %d' % len([f for f in os.listdir(OUT_DIR)] if os.path.isdir(OUT_DIR) else []))

if __name__ == '__main__': main()
