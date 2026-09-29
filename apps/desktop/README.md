# SpotTransfer usage

1.  Run the following commands

```bash
   cd apps/desktop
   python main.py
```

On first run this creates `apps/desktop/.venv` automatically, installs the
backend dependencies into it, and restarts itself inside that venv — no
manual `pip` step.

2. Paste a public Spotify playlist link.
3. Paste raw request headers from an authenticated `music.youtube.com`
   `/browse` request (same headers the web app / `browser.json` flow uses).
4. Press **Start Transfer**. Progress is saved to
   `apps/desktop/transfer_progress.json` after every track, so **Stop** or
   expired headers never lose completed work — press Start again to resume.

## Run it

Dependencies are handled automatically (see step 1). To reuse the backend
venv instead of the desktop one:

```bash
../backend/.venv/Scripts/python main.py   # Windows
../backend/.venv/bin/python main.py       # macOS/Linux
```

Headless sanity check (verifies imports, opens no window):

```bash
python main.py --check
```

On Debian/Ubuntu, tkinter itself may be missing: `sudo apt install python3-tk`.
