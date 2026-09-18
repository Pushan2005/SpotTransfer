# SpotTransfer

SpotTransfer is a free, open-source tool for moving Spotify playlists to YouTube Music.

[![](https://star-history.dera.page/svg?repos=Pushan2005/SpotTransfer&type=date&legend=top-left)](https://star-history.dera.page/#Pushan2005/SpotTransfer&type=date&legend=top-left)

---

## Contents

- [Install](#install)
- [Step 1 - YouTube Music credentials](#step-1---youtube-music-credentials)
  - [Why incognito](#why-incognito)
- [Step 2 - Pick your playlists](#step-2---pick-your-playlists)
- [Step 3 - Run the transfer](#step-3---run-the-transfer)
- [If the transfer stops](#if-the-transfer-stops)
- [Keep your credentials out of git](#keep-your-credentials-out-of-git)
- [Known limits](#known-limits)
- [Troubleshooting](#troubleshooting)

---

## Install

**Prerequisites:** Python 3.8+

Copy and paste, one block at a time:

```bash
git clone https://github.com/Pushan2005/SpotTransfer.git
cd SpotTransfer/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows, replace `source venv/bin/activate` with:

```bash
venv\Scripts\activate
```

Every command below assumes you are in the `backend` directory with the virtual
environment activated. Your prompt should start with `(venv)`.

---

## Step 1 - YouTube Music credentials

This tells the script it is allowed to create playlists on your account.

Do this in a **private / incognito window**. It is not about privacy — it is
what stops the credentials expiring every few hours. [Why](#why-incognito).

1. Create `backend/youtubemusic.json` by copying the example:

   ```bash
   cp youtubemusic.json.example youtubemusic.json
   ```

2. Open a **private / incognito window** (`Cmd+Shift+N` / `Ctrl+Shift+N`).
3. Go to [music.youtube.com](https://music.youtube.com) and **sign in** there.
4. Press **F12** to open developer tools, then click the **Network** tab.
5. In the filter box, type `browse`.
6. Reload the page. A list of requests appears.
7. Click a `browse` request whose **Status** is `200` and **Method** is `POST`.
8. Copy it:
   - **Chrome / Edge:** right-click the request → **Copy** → **Copy as cURL**
   - **Firefox:** right-click the request → **Copy Value** → **Copy as cURL**
9. Open `backend/youtubemusic.json`, delete everything in it, paste, and **save**.
10. **Close the incognito window.** Do **not** click "Sign out".

> **The last step is the important one.** Closing the window without signing out is
> what makes the credentials last. Your normal browser session is unaffected
> either way.

### Why incognito

Google keeps advancing your login for as long as a browser is using it. Five of
the cookies in that copied request — `__Secure-1PSIDTS`, `__Secure-3PSIDTS`,
`SIDCC`, `__Secure-1PSIDCC` and `__Secure-3PSIDCC` — get re-issued every few
minutes, and Google rejects the whole session when it is handed an outdated
copy of them.

So if you copy from your everyday signed-in tab and keep browsing, the copy you
pasted goes stale quickly. That is why credentials taken the obvious way tend to
die within hours.

An incognito window gets its own separate session. Once you close it, nothing is
using that session any more, so it stops advancing and the copy you pasted keeps
working. Signing out does the opposite — it ends the session immediately and the
copy dies with it.

The script helps on its own too: it strips those five volatile cookies before
connecting, since they authenticate nothing and only cause rejections. It then
checks the credentials against YouTube Music at startup and prints the account
it signed in as, so a stale paste is caught before any transferring begins
rather than part-way through.

> **Chrome's "Export HAR" does not work here.** Chrome strips the `cookie` and
> `authorization` headers out of HAR exports by default, so the file arrives
> with no credentials in it. Use **Copy as cURL** instead. If you prefer HAR,
> tick **Allow to generate HAR with sensitive data** in the developer tools
> settings (F1 → Preferences → Network) first.

`youtubemusic.json` accepts any of these, so paste whichever your browser gives
you. It does not have to be valid JSON when you paste it; the first run
converts whatever you pasted into the normalized ytmusicapi format.

| Format | Where it comes from |
| --- | --- |
| cURL command | **Copy as cURL** (recommended) |
| Raw request headers | **Copy Request Headers**, or the **Raw** toggle in the Headers tab |
| HAR | **Copy as HAR (with sensitive data)** |

---

## Step 2 - Pick your playlists

Two options. Use **2A** to move your whole library; use **2B** for one or two
playlists.

### 2A - Transfer many playlists (review a list first)

**First, give the script read access to your Spotify library.**

1. Open [open.spotify.com](https://open.spotify.com) and **sign in**.
2. Press **F12**, then open the **Application** tab (**Storage** in Firefox).
3. In the sidebar, expand **Cookies** and click `https://open.spotify.com`.
4. Find the row named `sp_dc` and copy its **Value**.
5. Create `backend/spotify.json` by copying the example:

   ```bash
   cp spotify.json.example spotify.json
   ```

6. Open `backend/spotify.json` and fill in both fields:

   ```json
   {
       "identifier": "your-spotify-email@example.com",
       "cookies": "sp_dc=PASTE_THE_VALUE_YOU_COPIED"
   }
   ```

**Now list your playlists:**

```bash
python3 list_playlists.py
```

This pages through your entire Spotify library, printing its progress, and
writes `backend/playlists.csv`, one playlist per row:

```csv
name,playlist_id,track_count
Café con Leche,37i9dQZF1DXa3NnZWk6Z3T,142
Road Trip,3ydrYAjx0aICD9neZbtPs7,58
Focus,1aaaaaaaaaaaaaaaaaaaaa,1372
```

`track_count` is there so you can see what you are signing up for before
transferring — large playlists take the longest and are the most likely to hit
an expired session part-way through. Spotify does not include counts in the
library listing, so each one costs its own request; they are fetched in
parallel, which takes a few minutes for a large account. To skip them:

```bash
python3 list_playlists.py --no-counts
```

**If counts come back empty**, Spotify is throttling. It starts refusing these
after a sustained run of them, which on a large library means the counts simply
stop part-way down the file. The refusal is temporary, so each one is retried
with a widening delay, and counts already in the file are never fetched twice.
To fill in whatever is still missing:

```bash
python3 list_playlists.py --counts-only
```

That reads the existing `playlists.csv`, fetches only the empty cells and
writes it back. It does not re-list your library, and it leaves every row and
its order untouched — which matters, because `selfhost.py` discards saved
transfer progress whenever the set of playlist IDs changes. Rerun it until the
file is full.

A playlist that stays empty is a personalised one — `Your Top Songs 2025`,
`Discover Weekly`, or a Blend shared with someone else. Those are generated per
listener and cannot be read through the public endpoint at all, so no amount of
retrying will fill them in. The
count is informational — editing or deleting the column does not affect the
transfer.

> **Why so many playlists show exactly 50:** that is the real size. Spotify's
> algorithmic playlists — anything called `X Radio`, `This Is X` or `Daily Mix
> N` — are built to hold 50 tracks. It is not a cap in this tool; your own
> playlists report their true length, into the thousands.

**Review it.** Open `playlists.csv` in a text editor or a spreadsheet, **delete
the rows for playlists you do not want**, and save. Keep the `name,playlist_id`
header row. Whatever is left is what gets transferred.

The reader is deliberately forgiving: blank rows, extra columns, re-ordered
columns, a deleted header, `#` at the start of a row to skip it, a full
playlist URL in place of an ID, and spreadsheet re-saves (CRLF, Excel BOM) all
work.

### 2B - Transfer one or two playlists

Skip `playlists.csv` entirely and edit `backend/setup.py`:

```python
spotify_playlist_link = "https://open.spotify.com/playlist/your-playlist-id"
```

Or a list, transferred in the order given:

```python
spotify_playlist_link = [
    "https://open.spotify.com/playlist/first-playlist-id",
    "https://open.spotify.com/playlist/second-playlist-id",
]
```

> If `playlists.csv` exists and has at least one row, it wins and `setup.py` is
> ignored. Delete `playlists.csv` to go back to using `setup.py`.

---

## Step 3 - Run the transfer

```bash
python3 selfhost.py
```

The script prints which source it is using, then works through the playlists
one at a time, showing a progress bar per playlist. Each playlist is created on
YouTube Music as **private**.

When it finishes it lists every playlist it created, plus any tracks it could
not find on YouTube Music.

---

## If the transfer stops

YouTube Music credentials expire after a while, which you will notice on large
libraries. When that happens the script **stops safely**, saves its place in
`backend/transfer_progress.json`, and tells you what to do:

1. Redo [Step 1](#step-1---youtube-music-credentials) to get fresh credentials,
   **including the incognito window and closing it afterwards** — that is what
   keeps the next set alive longer than the last.
2. Delete everything in `backend/youtubemusic.json`, paste the new copy, and **save**.
3. Run `python3 selfhost.py` again.

It resumes exactly where it stopped. Playlists already created are **not**
created again, and tracks already searched are **not** searched again.

Changing which playlists you want (editing `playlists.csv` or `setup.py`)
discards the saved progress and starts fresh.

---

## Keep your credentials out of git

`youtubemusic.json` holds a live Google session and `spotify.json` holds a live
Spotify session. Anyone with those files can sign in as you.

Both are in `.gitignore`, along with `playlists.csv` and
`transfer_progress.json`; only the `.example` files are tracked. Nothing for
you to do — but never paste the contents of either real file into an issue, a
pull request, or a chat.

> **Upgrading?** This file used to be called `browser.json`, and used to be
> tracked by the repository. It is still read if it is the only one present,
> so nothing breaks, but renaming it drops the old
> `git update-index --skip-worktree` workaround:
>
> ```bash
> git mv backend/browser.json backend/youtubemusic.json
> ```

---

## Known limits

- **Matching is a search, not a lookup.** Tracks are found on YouTube Music by
  searching for the title and artist, so a wrong match or a miss is possible.
  Anything not found is listed at the end of the run. Nothing is deleted from
  Spotify, so a bad result costs you only the new YouTube Music playlist.
- **Both services are read through private APIs.** Spotify is read via
  [SpotAPI](https://github.com/Aran404/SpotAPI) and YouTube Music via
  [ytmusicapi](https://github.com/sigma67/ytmusicapi). Neither is an official,
  supported interface, so either service can change it without notice and break
  this tool until the dependency catches up.
- **YouTube Music credentials expire mid-run.** Expected on large libraries;
  see [If the transfer stops](#if-the-transfer-stops).
- **Local files, podcasts, and unavailable tracks are skipped.** They carry too
  little metadata to search for. The count is reported per playlist.
- **A playlist that Spotify refuses to page through fully is reported, not
  hidden.** If Spotify returns fewer tracks than the playlist's own stated
  total, the run prints a warning naming both numbers rather than silently
  transferring a partial playlist.

---

## Troubleshooting

| Message | Fix |
| --- | --- |
| `The credentials in youtubemusic.json are not signed in to YouTube Music` | The paste is stale. Redo [Step 1](#step-1---youtube-music-credentials) in an incognito window and close it without signing out. |
| `youtubemusic.json is a HAR export whose requests carry no cookie header` | Chrome sanitized the HAR. Use **Copy as cURL** (Step 1). |
| `Parsed youtubemusic.json is missing the authorization header` | You copied only part of the request. Copy the whole thing again. |
| `The "cookies" value in spotify.json does not contain sp_dc` | Copy the `sp_dc` cookie value, not the cookie name or another cookie. |
| `playlists.csv row 4 has an invalid Spotify playlist ID` | That row was edited badly. Fix or delete the row. |
| `playlists.csv lists no playlists` | You deleted every row. Regenerate it or delete the file. |
| `Edit spotify_playlist_link before running the script` | `setup.py` still has the placeholder in it. |
| `cannot import name 'spotify_playlist_link' from 'setup'` | `setup.py` lost its `spotify_playlist_link = ""` line. Add it back. |
| `ModuleNotFoundError` | The virtual environment is not active. Run `source venv/bin/activate`. |

---

# Acknowledgements

- [Aran404](https://github.com/Aran404/) for SpotAPI.
- [sigma67](https://github.com/sigma67) for ytmusicapi.

# Legal Notice

> **Disclaimer**: This repository and any associated code are provided "as is" without warranty of any kind, either expressed or implied. The author of this repository does not accept any responsibility for the use or misuse of this repository or its contents. The author does not endorse any actions or consequences arising from the use of this repository. Any copies, forks, or re-uploads made by other users are not the responsibility of the author. The repository is solely intended as a Proof Of Concept for educational purposes regarding the use of a service's private API. By using this repository, you acknowledge that the author makes no claims about the accuracy, legality, or safety of the code and accepts no liability for any issues that may arise. More information can be found [HERE](./LEGAL_NOTICE.md).
