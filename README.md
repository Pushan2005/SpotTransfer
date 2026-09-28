# SpotTransfer

SpotTransfer is a free, open-source tool for moving Spotify playlists to YouTube Music.

[![](https://star-history.dera.page/svg?repos=Pushan2005/SpotTransfer&type=date&legend=top-left)](https://star-history.dera.page/#Pushan2005/SpotTransfer&type=date&legend=top-left)

This repo is a Bun monorepo (`apps/web` + `apps/backend`). The Python backend is unchanged — Bun workspaces only orchestrate installs and dev processes via `scripts/`.

### Prerequisites
- Bun 1.2+
- Python 3.8+ (a `.venv` is created automatically on first run)

```bash
git clone https://github.com/Pushan2005/SpotTransfer.git
cd SpotTransfer
bun install
```

Copy the env examples:

```bash
cp apps/web/.env.example apps/web/.env
cp apps/backend/.env.example apps/backend/.env
```

`apps/web/.env` holds `VITE_API_URL` (default `http://localhost:8080`, the Flask port in `apps/backend/main.py`).

### Run the web app + API together

```bash
bun run dev
```

This starts Vite (`http://localhost:5173`) and the Flask API (`http://localhost:8080`) with prefixed logs. To also open the frontend in your browser once Vite is ready:

```bash
bun run dev:all
```

Run them separately with:
```bash
bun run dev:web
bun run dev:backend
```

Other root scripts: `bun run build`, `bun run lint`, `bun run preview`.

### Get your YouTube Music request headers

1. Open [music.youtube.com](https://music.youtube.com) and sign in to your Google account.
2. Open your browser's developer tools and go to the **Network** tab.
3. Filter the requests for `/browse` and find a successful `POST` request with a `200` status.
    - In Firefox, right-click the request and choose **Copy > Copy Request Headers**.
    - In Chrome or Edge, open the request, go to **Headers**, and copy everything from `accept: */*` to the end of **Request Headers**.
4. Paste the copied request headers into `apps/backend/browser.json` and save the file. Paste them into the file instead of the web-hosted form.

### Run a transfer (self-hosted CLI)

1. Open `apps/backend/setup.py` and paste your Spotify playlist link into the variable:

    ```python
    spotify_playlist_link = "https://open.spotify.com/playlist/your-playlist-id"
    ```

2. From the repo root, run:

    ```bash
    bun run transfer
    ```

For a new playlist, change `spotify_playlist_link` in `setup.py` and run `bun run transfer` again. Repeat this for each playlist you want to transfer.

### Authentication issues

The YouTube Music request headers in `browser.json` expire periodically, which is most noticeable on large playlists. When that happens the script pauses the transfer, saves its progress to `apps/backend/transfer_progress.json`, and tells you what to do:

1. Get a fresh set of request headers from YouTube Music.
2. Delete the contents of `apps/backend/browser.json`, paste the new headers in, and **save the file**.
3. Run `bun run transfer` again. The script re-reads `browser.json` on startup and resumes the transfer from where it stopped — already-searched tracks are not repeated.

Starting a transfer for a different playlist (by changing `spotify_playlist_link` in `setup.py`) automatically discards any saved progress for the previous one.

# Acknowledgements

[Aran404](https://github.com/Aran404/) for SpotAPI

# Legal Notice

> **Disclaimer**: This repository and any associated code are provided "as is" without warranty of any kind, either expressed or implied. The author of this repository does not accept any responsibility for the use or misuse of this repository or its contents. The author does not endorse any actions or consequences arising from the use of this repository. Any copies, forks, or re-uploads made by other users are not the responsibility of the author. The repository is solely intended as a Proof Of Concept for educational purposes regarding the use of a service's private API. By using this repository, you acknowledge that the author makes no claims about the accuracy, legality, or safety of the code and accepts no liability for any issues that may arise. More information can be found [HERE](./LEGAL_NOTICE.md).
