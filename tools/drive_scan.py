"""Reads a public Google Drive folder tree (Drive API v3 + API key) and returns inspiration items.

Drive layout:  <Root> / <media form folder(s)> / [group folder] / <Category> / [<Sub> ...] / files
  - Instead of an API key you can use the Apps Script in tools/drive-folder-list.gs (set DRIVE_LIST_URL).
  - Top-level folder names say which media forms they feed: any of the words Video, Animation, Audio,
    Print, Photography in the name ("Video & Animation", "Print and Photography"), or "All Media Forms".
  - A group folder named like "Media Codes", "Media Conventions" or "Media Production Process" is optional and is ignored.
  - A folder whose name starts with "set" keeps everything inside it together as one slide set.
  - A Drive shortcut to a file or folder counts as the real thing, so shortcuts put one item in several categories.
  - links.txt (a text file, or a Google Doc named links) holds website lines:  Title | https://...
"""
import json, re, time, html as htmllib, urllib.parse as u, urllib.request, urllib.error
API = 'https://www.googleapis.com/drive/v3/files'
FORMS = ['video', 'animation', 'print', 'audio', 'photography']
FOLDER = 'application/vnd.google-apps.folder'; SHORTCUT = 'application/vnd.google-apps.shortcut'; GDOC = 'application/vnd.google-apps.document'
GROUPS = {'media codes', 'codes', 'media conventions', 'conventions', 'media production process', 'media production', 'production process', 'media production processes'}
def nz(s): return re.sub(r'[^a-z0-9]+', ' ', s.lower().replace('&', ' and ')).strip()
def nice(s):
    s = re.sub(r"(?<=[A-Za-z])_s\b", "'s", s.strip())   # Creator_s Style -> Creator's Style
    s = s.strip().strip('_').replace('_', ' ').strip()
    return s[:1].upper() + s[1:]
def nkey(s): return [(0, int(x), '') if x.isdigit() else (1, 0, x.lower()) for x in re.findall(r'\d+|\D+', s)]

class Drive:
    def __init__(self, key, mock=None):
        self.key, self.mock = key, mock
    def _get(self, url):
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=40) as r: return r.read()
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503) and attempt < 3: time.sleep(2 * (attempt + 1)); continue
                raise RuntimeError('Drive API error %s: %s' % (e.code, e.read()[:300].decode('utf-8', 'ignore')))
            except urllib.error.URLError:
                if attempt < 3: time.sleep(2); continue
                raise
    def children(self, fid):
        if self.mock is not None: return self.mock.get(fid, [])
        out, token = [], None
        while True:
            q = {'q': "'%s' in parents and trashed=false" % fid, 'pageSize': 1000, 'key': self.key, 'supportsAllDrives': 'true', 'includeItemsFromAllDrives': 'true',
                 'fields': 'nextPageToken,files(id,name,mimeType,shortcutDetails(targetId,targetMimeType))'}
            if token: q['pageToken'] = token
            d = json.loads(self._get(API + '?' + u.urlencode(q)))
            out += d.get('files', []); token = d.get('nextPageToken')
            if not token: return out
    def text(self, f):
        if self.mock is not None: return self.mock.get('text:' + f['id'], '')
        url = (API + '/%s/export?mimeType=text/plain&key=%s' if f['mimeType'] == GDOC else API + '/%s?alt=media&key=%s') % (f['id'], self.key)
        return self._get(url).decode('utf-8', 'ignore')

class PublicDrive(Drive):
    """No key, no script, no sign-in: reads the public 'embedded folder' page Google serves for any folder shared with Anyone with the link."""
    UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'}
    def __init__(self): super().__init__(None, None)
    def _page(self, url):
        for attempt in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=self.UA), timeout=40) as r: return r.read().decode('utf-8', 'ignore')
            except Exception:
                if attempt == 2: raise
                time.sleep(2 * (attempt + 1))
    def children(self, fid):
        page = self._page('https://drive.google.com/embeddedfolderview?id=%s' % fid)
        out = []
        for chunk in page.split('id="entry-')[1:]:
            eid = chunk.split('"', 1)[0]
            t = re.search(r'flip-entry-title[^>]*>([^<]*)<', chunk)
            if not t: continue
            ic = re.search(r'/type/([^"\'\s>]+)', chunk)
            mime = ic.group(1) if ic else 'application/octet-stream'
            if 'folder' in mime or '/drive/folders/' + eid in chunk: mime = FOLDER
            out.append(dict(id=eid, name=htmllib.unescape(t.group(1)).strip(), mimeType=mime))
        return out
    def text(self, f):
        url = ('https://docs.google.com/document/d/%s/export?format=txt' if f['mimeType'] == GDOC else 'https://drive.google.com/uc?export=download&id=%s') % f['id']
        return self._page(url)

def resolve(f):
    sd = f.get('shortcutDetails')
    if f.get('mimeType') == SHORTCUT and sd: return dict(id=sd['targetId'], name=f['name'], mimeType=sd['targetMimeType'])
    return f
def parse_forms(name):
    n = nz(name)
    if n == 'all' or ('all' in n.split() and 'media' in n): return FORMS[:]
    return [f for f in FORMS if f in n]
def is_set(name): return re.match(r'^set\b', name.strip(), re.I) is not None
def set_title(name): return re.sub(r'^set\b[\s:_\-–]*', '', name.strip(), flags=re.I).strip()
def prev(i): return 'https://drive.google.com/file/d/%s/preview' % i
def thumb(i): return 'https://drive.google.com/thumbnail?id=%s&sz=w2000' % i
def kind(m, name):
    n = name.lower()
    if m in ('', 'application/octet-stream'):   # public-page mode may not know the type: fall back to the file extension
        if re.search(r'\.(mp4|mov|m4v|webm)$', n): return 'video'
        if re.search(r'\.(jpe?g|png|gif|webp)$', n): return 'image'
        if re.search(r'\.(mp3|wav|m4a|ogg|aac)$', n): return 'audio'
        if n.endswith('.pdf'): return 'pdf'
        if n.endswith('.txt'): return 'file'
    if m.startswith('video/'): return 'video'
    if m.startswith('image/'): return 'image'
    if m.startswith('audio/'): return 'audio'
    if m == 'application/pdf': return 'pdf'
    if m.startswith('application/vnd.google-apps.'): return 'gdoc'
    return 'file'
def cats_from(parts):
    eff, grp = list(parts), None
    if eff and nz(eff[0]) in GROUPS: grp = nice(eff[0]); eff = eff[1:]
    c = [nice(eff[0]) if eff else 'General', ' / '.join(nice(x) for x in eff[1:])]
    if grp: c.append(grp)   # the group folder (e.g. Media Codes) travels with the category so the menu can place new categories
    return [c]

def scan(drive, root, report):
    result = []   # (forms, item)
    def walk(fid, parts, top, forms):
        kids = [resolve(k) for k in drive.children(fid)]
        folders = [k for k in kids if k['mimeType'] == FOLDER]; files = [k for k in kids if k['mimeType'] != FOLDER and not k['name'].startswith('.')]
        for f in sorted(folders, key=lambda k: nkey(k['name'])):
            if is_set(f['name']): do_set(f, parts, top, forms)
            else: walk(f['id'], parts + [f['name']], top, forms)
        for f in sorted(files, key=lambda k: nkey(k['name'])):
            k = kind(f['mimeType'], f['name']); cats = cats_from(parts); rel = '/'.join([top.lower()] + parts + [f['name']]).lower()
            base = re.sub(r'\.[A-Za-z0-9]{2,4}$', '', f['name'])
            if re.match(r'^links?$', base.strip(), re.I) and (f['mimeType'] == GDOC or f['mimeType'].startswith('text/')):
                for line in drive.text(f).splitlines():
                    if '|' in line and line.split('|', 1)[1].strip().startswith('http'):
                        t, l = line.split('|', 1); result.append((forms, dict(title=t.strip(), type='link', src=l.strip(), cats=cats, _rel=rel)))
                continue
            title = nice(base)
            if k == 'video': it = dict(title=title, type='video', src=prev(f['id']), drive=1)
            elif k == 'audio': it = dict(title=title, type='audio', src=prev(f['id']), drive=1)
            elif k == 'pdf': it = dict(title=title, type='pdf', src=prev(f['id']), drive=1)
            elif k == 'image': it = dict(title=title, type='image', src=thumb(f['id']), drive=1)
            elif k == 'gdoc': it = dict(title=title, type='link', src='https://drive.google.com/open?id=' + f['id'], drive=1)
            else: it = dict(title=title, type='file', src='https://drive.google.com/file/d/%s/view' % f['id'], drive=1)
            it.update(cats=cats, _rel=rel); result.append((forms, it))
    def do_set(folder, parts, top, forms):
        kids = [resolve(k) for k in drive.children(folder['id'])]
        media = [k for k in kids if k['mimeType'] != FOLDER and kind(k['mimeType'], k['name']) in ('image', 'video') and not k['name'].startswith('.')]
        media.sort(key=lambda k: nkey(k['name']))
        if not media: report.append('Empty set folder: %s/%s' % ('/'.join(parts), folder['name'])); return
        srcs = [thumb(k['id']) if kind(k['mimeType'], k['name']) == 'image' else prev(k['id']) for k in media]
        title = nice(set_title(folder['name']) or (parts[-1] if parts else 'Set'))
        result.append((forms, dict(title=title, type='set', srcs=srcs, drive=1, cats=cats_from(parts), _rel='/'.join([top] + parts).lower())))
    root_kids = drive.children(root)
    if not root_kids:
        report.append('The root Drive folder returned nothing. Check it is shared as "Anyone with the link: Viewer" and that DRIVE_ROOT_FOLDER_ID is the folder ID. (In no-key mode Google may also have changed or blocked its public folder page: see README Option B.)')
    for top in sorted((resolve(k) for k in root_kids), key=lambda k: nkey(k['name'])):
        if top['mimeType'] != FOLDER:
            continue
        forms = parse_forms(top['name'])
        if not forms: report.append('SKIPPED top-level folder "%s": its name has no media form word (Video, Animation, Audio, Print, Photography, All Media Forms)' % top['name']); continue
        n0 = len(result); walk(top['id'], [], top['name'], forms)
        report.append('Drive folder "%s" -> %s: %d items' % (top['name'], ', '.join(forms), len(result) - n0))
    return result
