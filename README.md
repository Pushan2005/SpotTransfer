# SpotTransfer

SpotTransfer is a free, open-source tool for moving Spotify playlists to YouTube Music.

[![](https://star-history.dera.page/svg?repos=Pushan2005/SpotTransfer&type=date&legend=top-left)](https://star-history.dera.page/#Pushan2005/SpotTransfer&type=date&legend=top-left)

This repo holds the web frontend (`apps/web`, Bun) and the self-hosted
desktop client (`apps/desktop`, plain Python, intentionally outside the Bun
workspaces).

### Prerequisites
- Bun 1.2+ (web frontend only)
- Python 3.8+ for the desktop client (a `.venv` is created automatically on first run)

```bash
git clone https://github.com/Pushan2005/SpotTransfer.git
cd SpotTransfer
bun install
```

Copy the web env example:

```bash
cp apps/web/.env.example apps/web/.env
```

`apps/web/.env` holds `VITE_API_URL` (default `http://localhost:8080`).

### Run the web app

```bash
bun run dev
```

This starts Vite (`http://localhost:5173`). To also open it in your browser:

```bash
bun run dev:all
```

Other root scripts: `bun run build`, `bun run lint`, `bun run preview`.

### Desktop client (no Bun needed)

`apps/desktop/main.py` is a tkinter GUI with playlist-link and headers input
fields. It runs on plain Python and sets up its own venv — see
`apps/desktop/README.md`.

### Get your YouTube Music request headers

1. Open [music.youtube.com](https://music.youtube.com) and sign in to your Google account.
2. Open your browser's developer tools and go to the **Network** tab.
3. Filter the requests for `/browse` and find a successful `POST` request with a `200` status.
    - In Firefox, right-click the request and choose **Copy > Copy Request Headers**.
    - In Chrome or Edge, open the request, go to **Headers**, and copy everything from `accept: */*` to the end of **Request Headers**.
4. Paste the copied request headers into the desktop app's headers box (or into `apps/desktop/browser.json` for the CLI flow) and save the file. Paste them into the file instead of the web-hosted form.

### Run a transfer (self-hosted)

Easiest: the desktop GUI (`apps/desktop/main.py`) takes the playlist link
and headers as input fields. Prefer the terminal? Edit
`apps/desktop/setup.py`:

    ```python
    spotify_playlist_link = "https://open.spotify.com/playlist/your-playlist-id"
    ```

then, from `apps/desktop`, run the venv interpreter on `selfhost.py`:

    ```bash
    .venv/Scripts/python selfhost.py   # Windows
    .venv/bin/python selfhost.py       # macOS/Linux
    ```

For a new playlist, change `spotify_playlist_link` in `setup.py` and run `selfhost.py` again. Repeat this for each playlist you want to transfer.

### Authentication issues

The YouTube Music request headers expire periodically, which is most noticeable on large playlists. When that happens the script pauses the transfer, saves its progress to `apps/desktop/transfer_progress.json`, and tells you what to do:

1. Get a fresh set of request headers from YouTube Music.
2. Delete the contents of `apps/desktop/browser.json` (CLI flow), paste the new headers in, and **save the file**. In the GUI, just paste the fresh headers into the headers box.
3. Run the transfer again. The script re-reads the headers on startup and resumes from where it stopped — already-searched tracks are not repeated.

Starting a transfer for a different playlist (by changing `spotify_playlist_link` in `setup.py`) automatically discards any saved progress for the previous one.

# Acknowledgements

[Aran404](https://github.com/Aran404/) for SpotAPI

# Legal Notice

> **Disclaimer**: This repository and any associated code are provided "as is" without warranty of any kind, either expressed or implied. The author of this repository does not accept any responsibility for the use or misuse of this repository or its contents. The author does not endorse any actions or consequences arising from the use of this repository. Any copies, forks, or re-uploads made by other users are not the responsibility of the author. The repository is solely intended as a Proof Of Concept for educational purposes regarding the use of a service's private API. By using this repository, you acknowledge that the author makes no claims about the accuracy, legality, or safety of the code and accepts no liability for any issues that may arise. More information can be found [HERE](./LEGAL_NOTICE.md).
