// Google Apps Script: lists your Drive folder tree as JSON so GitHub can build the site menu. No API key needed.
// 1. Go to https://script.google.com (signed in to the Google account that owns the folders) > New project.
// 2. Delete the sample code, paste ALL of this in, and put your root folder ID on the ROOT_ID line.
//    (the folder ID is the last part of the folder's web address after /folders/)
// 3. Press Run once (choose doGet) and allow access when asked.
// 4. Deploy > New deployment > type: Web app > Execute as: Me > Who has access: Anyone > Deploy. Copy the Web app URL (ends in /exec).
// 5. In GitHub: Settings > Secrets and variables > Actions > New repository secret: DRIVE_LIST_URL = that URL.
const ROOT_ID = 'PASTE_YOUR_ROOT_FOLDER_ID_HERE';
const FOLDER = 'application/vnd.google-apps.folder';
const SHORTCUT = 'application/vnd.google-apps.shortcut';

function doGet() {
  const root = DriveApp.getFolderById(ROOT_ID);
  const tree = {id: root.getId(), name: root.getName(), mimeType: FOLDER, children: walk(root, {})};
  return ContentService.createTextOutput(JSON.stringify(tree)).setMimeType(ContentService.MimeType.JSON);
}

function walk(folder, stack) {
  const out = [];
  stack[folder.getId()] = true;
  const subs = folder.getFolders();
  while (subs.hasNext()) {
    const f = subs.next();
    if (stack[f.getId()]) continue;
    out.push({id: f.getId(), name: f.getName(), mimeType: FOLDER, children: walk(f, stack)});
  }
  const files = folder.getFiles();
  while (files.hasNext()) {
    const f = files.next();
    let id = f.getId(), mime = f.getMimeType(), name = f.getName();
    if (mime === SHORTCUT) {            // a shortcut counts as the real file or folder (one item in several categories)
      try { id = f.getTargetId(); mime = f.getTargetMimeType(); } catch (e) { continue; }
      if (mime === FOLDER) {
        if (!stack[id]) out.push({id: id, name: name, mimeType: FOLDER, children: walk(DriveApp.getFolderById(id), stack)});
        continue;
      }
    }
    const o = {id: id, name: name, mimeType: mime};
    if (/^links?(\.txt)?$/i.test(name.trim())) {   // links.txt (or a Google Doc called links): "Title | https://..." per line
      try {
        o.text = mime === 'application/vnd.google-apps.document'
          ? DocumentApp.openById(id).getBody().getText()
          : DriveApp.getFileById(id).getBlob().getDataAsString();
      } catch (e) {}
    }
    out.push(o);
  }
  delete stack[folder.getId()];
  return out;
}
