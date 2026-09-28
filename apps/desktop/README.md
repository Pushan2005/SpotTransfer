# SpotTransfer usage

1.  Run the following commands

```bash
   cd apps/desktop
   pip install -r ../backend/requirements.txt
   python main.py
```

2. Paste a public Spotify playlist link.
3. Paste raw request headers from an authenticated `music.youtube.com`
   `/browse` request (same headers the web app / `browser.json` flow uses).
4. Press **Start Transfer**. Progress is saved to
   `apps/desktop/transfer_progress.json` after every track, so **Stop** or
   expired headers never lose completed work — press Start again to resume.

## Run it

The backend libraries (`ytmusicapi`, `spotapi`, ...) must be installed in the
interpreter you use. Either reuse the backend venv:

```bash
../backend/.venv/Scripts/python main.py   # Windows
../backend/.venv/bin/python main.py       # macOS/Linux
```

Headless sanity check (verifies imports, opens no window):

```bash
python main.py --check
```

On Debian/Ubuntu, tkinter itself may be missing: `sudo apt install python3-tk`.
