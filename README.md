# Media 12 SAT Inspiration

Static site for VCE Media Units 3 and 4. The site itself lives on GitHub Pages (a few MB). The videos, images and slide sets live in a Google Drive folder, and the site reads that folder automatically.

## 1. Publish the site (once)
1. Create a GitHub repo and upload everything in this folder (keep `assets`, `inspiration`, `tools` and `.github`).
2. Repo **Settings > Pages > Source = GitHub Actions**.

## 2. Connect Google Drive (once)
Your Drive root folder must be shared as **Anyone with the link: Viewer** (subfolders inherit this).

### Option A: no key, no script, no sign-in (try this first)
1. Open the root Drive folder. The web address ends in `/folders/XXXXXXXX`. Copy that last part (the folder ID).
2. In your GitHub repo: **Settings > Secrets and variables > Actions > Variables tab > New repository variable**. Name `DRIVE_ROOT_FOLDER_ID`, value = the folder ID. (Nothing secret here: the folder is already public by link.)
3. **Actions** tab > **Deploy site** > **Run workflow**. Open the finished run and read the summary: it lists every Drive folder found and how many items.

This reads the public folder page that Google serves for shared folders. It is not an official interface, so if the summary says the folder returned nothing, or items are missing, use Option B.

### Option B: Google Apps Script (no API key, no Google Cloud, no billing)
1. Go to https://script.google.com signed in as the account that owns the folders, start a **New project**, and paste in everything from `tools/drive-folder-list.gs` with your folder ID on the first line.
2. **Run** once (function `doGet`). Google shows "Google hasn't verified this app". That is normal for your own script (the developer named is you): choose **Advanced > Go to project (unsafe) > Allow**. Only you see this screen, never students.
3. **Deploy > New deployment > Web app**, *Execute as: Me*, *Who has access: Anyone*. Copy the Web app URL.
4. In GitHub add a repository **secret** `DRIVE_LIST_URL` with that URL, then run **Deploy site**.

### Option C: Drive API key
Create a key in Google Cloud Console restricted to the Google Drive API, then add the repo secret `DRIVE_API_KEY` and the variable `DRIVE_ROOT_FOLDER_ID`.

### Keeping secrets private
Secrets (`DRIVE_LIST_URL`, `DRIVE_API_KEY`) live only in GitHub's encrypted settings and are never written into the website files. Never paste them into a file in the repo or share them in chat. Option A has no secret at all.

After this the site rebuilds every night (and whenever you press Run workflow) so new Drive files appear. GitHub switches off scheduled runs after 60 days with no repo activity: if the site stops updating, press Run workflow once.

## 3. How to organise the Drive folder
    Root folder
      Video & Animation            <- name must contain Video, Animation, Audio, Print or Photography
        Media Codes                <- group folder (Media Codes / Media Conventions / Media Production Process)
          Camera Techniques        <- category (a menu topic)
            Camera Angles          <- sub-category
              kubrick.mp4
      All Media Forms              <- shows in every media form
- **Media forms:** the top-level folder name says where its contents show. "Video Animation and Audio" feeds those three forms. "All Media Forms" feeds all five.
- **Category = folder name.** Files go in the folder; the file name is the title shown on the site.
- **Sets:** a folder whose name starts with `set` (for example `set` or `set - Rules of composition`) keeps everything inside it together as one slide set, in file-name order. Images and videos can be mixed. The set's title is the text after `set -`, or the parent folder's name.
- **More than one category:** make a Drive **shortcut** to the file (or the `set` folder) in the other category folder. It shows once, listed under both.
- **Websites / YouTube:** put a text file called `links.txt` in a folder, one line per link: `Title | https://...` (a Google Doc called `links` also works). YouTube plays inside the viewer. Small `links.txt` files can also stay in this repo under `inspiration/<media form>/<Category>/`.
- **Creators:** the `Creator's Style` folder holds one sub-folder per person (for example `Wes Anderson`). Anything that names a director or creator goes there.
- **New categories:** a new folder inside Media Codes, Media Conventions or Media Production Process appears automatically under that group in the menu. Empty folders stay hidden until they hold something.
- Folder names are matched to the menu groups in `index.html` (the `GROUPS` list). A category that is not in the list shows as its own button, never under "Other". Tell Claude where it belongs.

## Notes
- Drive videos play in Google's player (click to play, no autoplay). They can take a few minutes to work after upload.
- The viewer's thumbnail strip shows titles and icons only.
- Link checking: on every build GitHub checks websites; dead ones are removed and listed in the run summary and `assets/link-report.txt`.
