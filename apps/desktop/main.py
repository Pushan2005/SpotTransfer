"""SpotTransfer desktop client (tkinter UI, no Bun/Node required).

Run with plain Python — the transfer logic in selfhost.py (same folder) is
reused, so this file only contains UI + worker-thread orchestration:

    cd apps/desktop
    python main.py

On first run the script creates apps/desktop/.venv automatically, installs
the backend dependencies (ytmusicapi, spotapi, ...) into it, and restarts
itself inside that venv. No manual pip step, no Bun/Node.

Sanity check without opening a window:

    python main.py --check
"""

from __future__ import annotations

import json
import os
import queue
import sys
import threading
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DESKTOP_VENV_DIR = BASE_DIR / ".venv"
PROGRESS_PATH = BASE_DIR / "transfer_progress.json"
_PROGRESS_VERSION = 1

from logging_config import configure_logging, logger

configure_logging()

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    logger.exception("Tkinter could not be imported")
    print(
        "tkinter is not available for this Python install.\n"
        "  Windows/macOS (python.org): tkinter ships with Python.\n"
        "  Debian/Ubuntu: sudo apt install python3-tk",
        file=sys.stderr,
    )
    raise SystemExit(1)


def enable_hidpi() -> None:
    """Opt out of Windows bitmap scaling so the UI renders crisply.

    Without this, Windows virtualizes tkinter apps on high-DPI displays
    and upscales the window as a bitmap, which looks blurry/low-res.
    Per-monitor awareness (level 2) re-renders crisply on every display,
    so dragging the window to a monitor with different scaling stays
    sharp. Falls back to system-DPI awareness where unavailable.
    Must run before the first Tk() instance is created.
    """

    if os.name != "nt":
        return
    try:
        from ctypes import windll
        try:
            windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def desktop_venv_python() -> Path:
    if os.name == "nt":
        return DESKTOP_VENV_DIR / "Scripts" / "python.exe"
    return DESKTOP_VENV_DIR / "bin" / "python"


def ensure_deps() -> None:
    """Create apps/desktop/.venv and install backend deps on first run.

    Re-executes this script with the venv interpreter afterwards, so the
    rest of the file can import ytmusicapi/spotapi unconditionally.
    """

    try:
        import spotapi  # noqa: F401
        import ytmusicapi  # noqa: F401
        return
    except ImportError:
        pass

    venv_python = desktop_venv_python()
    if venv_python.is_file() and (
        Path(sys.executable).resolve() != venv_python.resolve()
    ):
        # Venv already set up, but we're running under a different
        # interpreter (e.g. system python): jump straight into it.
        os.execv(str(venv_python), [str(venv_python),
                                    os.path.abspath(__file__),
                                    *sys.argv[1:]])

    if Path(sys.prefix).resolve() == DESKTOP_VENV_DIR.resolve():
        logger.error("Backend dependencies are missing from the desktop virtualenv")
        raise SystemExit(
            "Backend dependencies are still missing inside "
            "apps/desktop/.venv. Delete that folder and try again, or "
            "install manually: pip install -r requirements.txt"
        )

    import subprocess

    print("First run: creating apps/desktop/.venv …")
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(DESKTOP_VENV_DIR)])
    if result.returncode != 0:
        logger.error("Virtualenv creation failed with exit code %d",
                     result.returncode)
        raise SystemExit(
            "Could not create the virtualenv"
            + (" (Debian/Ubuntu: sudo apt install python3-venv)"
               if os.name != "nt" else "")
        )

    print("Installing desktop dependencies into apps/desktop/.venv …")
    result = subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r",
         str(BASE_DIR / "requirements.txt")])
    if result.returncode != 0:
        logger.error("Desktop dependency installation failed with exit code %d",
                     result.returncode)
        raise SystemExit("pip install failed — see the output above.")

    print("Restarting inside apps/desktop/.venv …")
    os.execv(str(venv_python), [str(venv_python), os.path.abspath(__file__),
                                *sys.argv[1:]])


def load_backend():
    """Import selfhost.py (same folder), with a friendly error if deps miss."""

    try:
        import selfhost  # noqa: F401  (imported for its helpers)

        return selfhost
    except ImportError as error:
        raise RuntimeError(
            "Could not import the transfer backend.\n\n"
            f"Details: {error}\n\n"
            "Install the desktop dependencies first:\n"
            "  pip install -r requirements.txt  (from apps/desktop)\n"
            "or run with the desktop venv interpreter:\n"
            "  .venv/Scripts/python main.py   (Windows)\n"
            "  .venv/bin/python main.py       (macOS/Linux)"
        ) from error


def load_progress() -> dict | None:
    if not PROGRESS_PATH.is_file():
        return None
    try:
        progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        logger.warning("Could not read saved transfer progress; starting fresh",
                       exc_info=True)
        return None
    if (
        not isinstance(progress, dict)
        or progress.get("version") != _PROGRESS_VERSION
        or not isinstance(progress.get("playlist_id"), str)
        or not isinstance(progress.get("tracks"), list)
    ):
        logger.warning("Saved transfer progress has an unsupported format")
        return None
    return progress


def save_progress(progress: dict) -> None:
    tmp_path = PROGRESS_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(progress, ensure_ascii=True, indent=2))
    os.replace(tmp_path, PROGRESS_PATH)


def clear_progress() -> None:
    try:
        PROGRESS_PATH.unlink()
    except FileNotFoundError:
        pass


def sync_text_colors(root: tk.Tk, dark: bool, *widgets: tk.Widget) -> None:
    """Recolor plain tk.Text/Listbox widgets to match the active ttk theme.

    sv-ttk only themes ttk widgets, so the Text boxes (and the root
    background) are synced from the live style instead of hardcoded
    palette values.
    """

    style = ttk.Style(root)
    if dark:
        fallback_bg, fallback_fg = "#1c1c1c", "#ffffff"
    else:
        fallback_bg, fallback_fg = "#ffffff", "#000000"
    bg = style.lookup("TEntry", "fieldbackground") or fallback_bg
    fg = style.lookup("TLabel", "foreground") or fallback_fg
    select_bg = style.lookup("TEntry", "selectbackground") or (
        "#264f78" if dark else "#0078d4")
    select_fg = style.lookup("TEntry", "selectforeground") or "#ffffff"
    frame_bg = style.lookup("TFrame", "background")
    if frame_bg:
        root.configure(background=frame_bg)
    for widget in widgets:
        widget.configure(background=bg, foreground=fg,
                         selectbackground=select_bg,
                         selectforeground=select_fg)
        try:
            widget.configure(insertbackground=fg)
        except tk.TclError:
            pass  # e.g. Listbox has no insertion cursor


AUTH_HELP = (
    "Your YouTube Music headers have expired or are invalid.\n\n"
    "Progress is saved — nothing found so far will be lost.\n\n"
    "To continue:\n"
    "  1. Copy a fresh set of request headers from an authenticated\n"
    "     music.youtube.com /browse request (see README).\n"
    "  2. Paste them into the headers box in this window.\n"
    "  3. Press Clone Playlist again to resume where it stopped."
)

GITHUB_URL = "https://github.com/Pushan2005/SpotTransfer"


def run_transfer(playlist_link: str, auth_headers_raw: str,
                 events: "queue.Queue") -> None:
    """Worker-thread body. Never touches widgets — reports via `events`."""

    def emit(kind: str, *payload) -> None:
        events.put((kind,) + payload)

    logger.info("===== Transfer started (GUI) =====")
    try:
        backend = load_backend()
    except RuntimeError as error:
        logger.exception("Could not load transfer backend")
        logger.info("===== Transfer failed (GUI setup) =====")
        emit("failed", str(error), "setup")
        return
    except Exception as error:
        logger.exception("Unexpected failure loading transfer backend")
        logger.info("===== Transfer failed (GUI setup) =====")
        emit("failed", f"Unexpected error: {error}", "error")
        return

    try:
        try:
            playlist_id = backend.extract_spotify_playlist_id(playlist_link)
        except ValueError as error:
            logger.warning("Spotify playlist URL failed validation: %s", error)
            logger.info("===== Transfer failed (validation) =====")
            emit("failed", str(error), "validation")
            return
        logger.info("===== Transfer started (GUI) | playlist_id=%s =====", playlist_id)

        if not auth_headers_raw.strip():
            logger.warning("Transfer validation failed: YouTube Music headers missing")
            logger.info("===== Transfer failed (validation) | id=%s =====", playlist_id)
            emit("failed", "Paste your YouTube Music request headers first.",
                 "validation")
            return

        progress = load_progress()
        if progress is not None and progress.get("playlist_id") != playlist_id:
            logger.info("Found progress for a different playlist; starting fresh")
            clear_progress()
            progress = None

        if progress is not None:
            playlist_name = str(progress["playlist_name"])
            tracks = list(progress["tracks"])
            skipped = int(progress.get("skipped_tracks") or 0)
            logger.info("===== Transfer started: '%s' (id=%s, GUI, resuming %d/%d already searched) =====",
                        playlist_name, playlist_id,
                        progress.get("searched") or 0, len(tracks))
        else:
            logger.info("Fetching Spotify playlist (GUI, id=%s)", playlist_id)
            emit("mode", "indeterminate")
            emit("status", "Fetching Spotify playlist…")

            def on_fetch_page(fetched: int, total: int) -> None:
                emit("status", f"Fetching Spotify playlist… "
                               f"({fetched}/{total} items)")

            try:
                playlist_name = backend.get_spotify_playlist_name(playlist_link)
                logger.info("===== Transfer started: '%s' (id=%s, GUI) =====",
                            playlist_name, playlist_id)
                tracks, skipped = backend.get_spotify_tracks(
                    playlist_id, on_page=on_fetch_page)
            except Exception as error:
                logger.exception("Could not read Spotify playlist (GUI, id=%s)", playlist_id)
                logger.info("===== Transfer failed (GUI Spotify fetch) | id=%s =====",
                            playlist_id)
                emit("failed", f"Could not read the Spotify playlist: {error}",
                     "error")
                return
            logger.info("Fetched %d tracks for '%s'; skipped %d unavailable items",
                        len(tracks), playlist_name, skipped)
            progress = {
                "version": _PROGRESS_VERSION,
                "playlist_id": playlist_id,
                "playlist_link": playlist_link,
                "playlist_name": playlist_name,
                "tracks": tracks,
                "skipped_tracks": skipped,
                "video_ids": [],
                "missed_tracks": [],
                "searched": 0,
                "search_complete": False,
            }
            save_progress(progress)

        if skipped:
            logger.info("Skipped %d Spotify item(s) without usable metadata for '%s'",
                        skipped, playlist_name)

        try:
            auth_config = backend.parse_browser_headers(auth_headers_raw)
        except ValueError as error:
            logger.warning("YouTube Music headers failed validation: %s", error)
            logger.info("===== Transfer failed (validation) | '%s' =====", playlist_name)
            emit("failed", str(error), "validation")
            return

        from ytmusicapi import YTMusic
        logger.info("Loading YouTube Music auth for '%s' (GUI)", playlist_name)
        ytmusic = YTMusic(auth_config)

        video_ids: list[str] = list(progress.get("video_ids") or [])
        missed: list[str] = list(progress.get("missed_tracks") or [])
        start = int(progress.get("searched") or 0)
        total = len(tracks)
        if not 0 <= start <= total:
            start = 0
        logger.info("Searching YouTube Music for '%s': %d tracks from item %d",
                    playlist_name, total, start + 1)
        emit("mode", "determinate", total)
        emit("progress", start, total)

        for index in range(start, total):
            track = tracks[index]
            name = str(track.get("name", ""))
            artists = track.get("artists") or []
            label = f"{name} - {', '.join(str(a) for a in artists)}"
            emit("status", f"Searching {index + 1}/{total}: {label}")
            try:
                results = ytmusic.search(
                    " ".join([name, *(str(a) for a in artists)]),
                    filter="songs",
                )
                video_id = next(
                    (r.get("videoId") for r in results
                     if isinstance(r, dict) and r.get("videoId")),
                    None,
                )
            except Exception as error:
                if backend._is_auth_error(error):
                    logger.exception(
                        "YouTube Music authentication failed (GUI) at [%d/%d] '%s'",
                        index + 1, total, label)
                    logger.info("===== Transfer paused (auth expired) | '%s' =====",
                                playlist_name)
                    emit("failed", AUTH_HELP, "auth")
                    return
                logger.exception(
                    "YouTube Music search failed (GUI) at [%d/%d] '%s'; treating as not found",
                    index + 1, total, label)
                video_id = None
            if video_id is None:
                missed.append(label)
                logger.info("[%d/%d] YTM NOT FOUND: '%s'", index + 1, total, label)
            else:
                video_ids.append(video_id)
                logger.info("[%d/%d] YTM FOUND: '%s' -> %s",
                            index + 1, total, label, video_id)
            progress["video_ids"] = video_ids
            progress["missed_tracks"] = missed
            progress["searched"] = index + 1
            save_progress(progress)
            emit("progress", index + 1, total)

        if not video_ids:
            logger.error("No Spotify tracks were found on YouTube Music for '%s'",
                         playlist_name)
            logger.info("===== Transfer failed (nothing found) | '%s' =====",
                        playlist_name)
            emit("failed", "No Spotify tracks were found on YouTube Music.",
                 "error")
            return

        progress["search_complete"] = True
        save_progress(progress)
        logger.info("YouTube Music search complete for '%s': found %d/%d; missed %d",
                    playlist_name, len(video_ids), total, len(missed))
        for missed_label in missed:
            logger.info("YTM missed: '%s'", missed_label)

        emit("mode", "indeterminate")
        emit("status", f"Creating YouTube Music playlist '{playlist_name}'…")
        logger.info("Creating YouTube Music playlist '%s' with %d tracks (GUI)",
                    playlist_name, len(video_ids))
        try:
            created_id = ytmusic.create_playlist(
                playlist_name, "", "PRIVATE", video_ids)
        except Exception as error:
            if backend._is_auth_error(error):
                logger.exception("YouTube Music authentication failed creating playlist for '%s'",
                                 playlist_name)
                logger.info("===== Transfer paused (auth expired) | '%s' =====",
                            playlist_name)
                emit("failed", AUTH_HELP, "auth")
                return
            logger.exception("Could not create YouTube Music playlist for '%s'",
                             playlist_name)
            logger.info("===== Transfer failed (create) | '%s' =====", playlist_name)
            emit("failed", f"Could not create the playlist: {error}", "error")
            return
        if not created_id:
            logger.error("YouTube Music did not return a playlist ID for '%s'",
                         playlist_name)
            logger.info("===== Transfer failed (no playlist ID) | '%s' =====",
                        playlist_name)
            emit("failed", "YouTube Music did not return a playlist ID.",
                 "error")
            return

        clear_progress()
        logger.info("Transfer completed for '%s': found %d of %d tracks; %d not found",
                    playlist_name, len(video_ids), total, len(missed))
        logger.info("===== Transfer finished: '%s' (id=%s) =====",
                    playlist_name, playlist_id)
        emit("finished", {"playlist_id": created_id,
                          "playlist_name": playlist_name,
                          "missed": missed, "found": len(video_ids),
                          "total": total})
    except Exception as error:  # last-resort guard for the worker thread
        logger.exception("Unexpected transfer failure")
        logger.info("===== Transfer failed (unexpected) =====")
        emit("failed", f"Unexpected error: {error}", "error")


class App:
    LINK_PLACEHOLDER = "open.spotify.com/playlist/..."
    HEADERS_PLACEHOLDER = "Paste your headers here"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("SpotTransfer")
        root.minsize(760, 560)

        self.events: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None

        frame = ttk.Frame(root, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        top = ttk.Frame(frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="TRANSFER",
                  font=("TkDefaultFont", 9, "bold")).grid(
            row=0, column=0, sticky="w")
        self.theme_btn = ttk.Button(top, text="Theme: Light",
                                    command=self.toggle_theme,
                                    state="disabled")
        self.theme_btn.grid(row=0, column=1, sticky="e")

        columns = ttk.Frame(frame)
        columns.grid(row=1, column=0, sticky="nsew")
        columns.columnconfigure(0, weight=1)
        columns.columnconfigure(1, weight=1)
        columns.rowconfigure(0, weight=1)

        left = ttk.Frame(columns)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        ttk.Label(left, text="Paste headers here").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        headers_box = ttk.Frame(left)
        headers_box.grid(row=1, column=0, sticky="nsew")
        headers_box.columnconfigure(0, weight=1)
        headers_box.rowconfigure(0, weight=1)
        self.headers = tk.Text(headers_box, wrap="none",
                               font=("TkDefaultFont", 9))
        headers_scroll = ttk.Scrollbar(headers_box, orient="vertical",
                                       command=self.headers.yview)
        self.headers.configure(yscrollcommand=headers_scroll.set)
        self.headers.grid(row=0, column=0, sticky="nsew")
        headers_scroll.grid(row=0, column=1, sticky="ns")
        self.headers_has_placeholder = True
        self.headers.insert("1.0", self.HEADERS_PLACEHOLDER)
        self.headers.bind("<FocusIn>", self._clear_headers_placeholder)
        self.headers.bind("<FocusOut>", self._restore_headers_placeholder)
        self.headers.bind("<KeyRelease>",
                          lambda _event: self.refresh_start_state())

        right = ttk.Frame(columns)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        right.columnconfigure(0, weight=1)
        ttk.Label(right, text="Spotify playlist URL").grid(
            row=0, column=0, sticky="w")
        ttk.Label(right, text="\u24d8 The playlist must be public",
                  foreground="gray",
                  font=("TkDefaultFont", 8)).grid(
            row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Label(right,
                  text="\u26a0 Headers may expire midway \u2014 paste a fresh set "
                       "if the transfer pauses.",
                  foreground="gray", font=("TkDefaultFont", 8),
                  wraplength=300, justify="left").grid(
            row=2, column=0, sticky="w")
        self.link_var = tk.StringVar(value=self.LINK_PLACEHOLDER)
        self.link_has_placeholder = True
        self.link = ttk.Entry(right, textvariable=self.link_var)
        self.link.grid(row=3, column=0, sticky="ew", pady=(6, 8))
        self.link.bind("<FocusIn>", self._clear_link_placeholder)
        self.link.bind("<FocusOut>", self._restore_link_placeholder)
        self.link_var.trace_add(
            "write", lambda *_args: self.refresh_start_state())
        self.start_btn = ttk.Button(right, text="Clone Playlist",
                                    command=self.start, state="disabled")
        self.start_btn.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self.status = ttk.Label(right, text="Ready.", width=40)
        self.status.grid(row=6, column=0, sticky="w", pady=(8, 0))
        self.progress = ttk.Progressbar(right, mode="determinate")
        self.progress.grid(row=7, column=0, sticky="ew", pady=(2, 0))

        self.missed_label = ttk.Label(right, text="Missed tracks: none yet.")
        self.missed_label.grid(row=8, column=0, sticky="w", pady=(12, 4))
        missed_box = ttk.Frame(right)
        missed_box.grid(row=9, column=0, sticky="ew")
        missed_box.columnconfigure(0, weight=1)
        self.missed_list = tk.Listbox(missed_box, height=8,
                                      activestyle="none",
                                      font=("TkDefaultFont", 9))
        missed_scroll = ttk.Scrollbar(missed_box, orient="vertical",
                                      command=self.missed_list.yview)
        self.missed_list.configure(yscrollcommand=missed_scroll.set)
        self.missed_list.grid(row=0, column=0, sticky="ew")
        missed_scroll.grid(row=0, column=1, sticky="ns")

        frame.rowconfigure(1, weight=1)

        self.dark_mode = False
        self.apply_theme()
        self.refresh_start_state()
        root.report_callback_exception = self._log_callback_exception

        self.overlay = None
        self.overlay_status = None
        self.overlay_progress = None
        self.root.bind("<Configure>", self._sync_overlay_geometry, add="+")

        self.root.after(100, self.pump)

    def show_overlay(self) -> None:
        """Cover the window with a semi-transparent progress modal."""

        if self.overlay is not None:
            return
        self.root.update_idletasks()
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.transient(self.root)
        try:
            overlay.attributes("-alpha", 0.85)
        except tk.TclError:
            pass
        outer = ttk.Frame(overlay)
        outer.pack(fill="both", expand=True)
        content = ttk.Frame(outer)
        content.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(content, text="Transferring playlist…",
                  font=("TkDefaultFont", 12, "bold")).pack(pady=(0, 8))
        self.overlay_status = ttk.Label(content, text="Starting…",
                                        wraplength=420, justify="center")
        self.overlay_status.pack(pady=(0, 8))
        self.overlay_progress = ttk.Progressbar(content, mode="determinate",
                                                length=360)
        self.overlay_progress.pack()
        self.overlay = overlay
        self._sync_overlay_geometry()
        try:
            overlay.grab_set()
        except tk.TclError:
            pass

    def hide_overlay(self) -> None:
        overlay, self.overlay = self.overlay, None
        self.overlay_status = None
        self.overlay_progress = None
        if overlay is not None:
            try:
                overlay.grab_release()
            except tk.TclError:
                pass
            overlay.destroy()

    def _sync_overlay_geometry(self, _event=None) -> None:
        if self.overlay is None:
            return
        try:
            self.overlay.geometry(
                f"{self.root.winfo_width()}x{self.root.winfo_height()}"
                f"+{self.root.winfo_rootx()}+{self.root.winfo_rooty()}")
        except tk.TclError:
            pass

    @staticmethod
    def _short_status(text: str, limit: int = 90) -> str:
        text = str(text)
        return text if len(text) <= limit else text[:limit - 1] + "…"

    def playlist_url(self) -> str:
        if self.link_has_placeholder:
            return ""
        return self.link_var.get().strip()

    def headers_text(self) -> str:
        if self.headers_has_placeholder:
            return ""
        return self.headers.get("1.0", "end")

    def refresh_start_state(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            return
        url = self.playlist_url()
        ready = bool(url and "open.spotify.com/playlist/" in url
                     and self.headers_text().strip())
        self.start_btn.configure(state="normal" if ready else "disabled")

    def _clear_link_placeholder(self, _event) -> None:
        if self.link_has_placeholder:
            self.link_has_placeholder = False
            self.link_var.set("")

    def _restore_link_placeholder(self, _event) -> None:
        if not self.link_var.get().strip():
            self.link_has_placeholder = True
            self.link_var.set(self.LINK_PLACEHOLDER)

    def _clear_headers_placeholder(self, _event) -> None:
        if self.headers_has_placeholder:
            self.headers_has_placeholder = False
            self.headers.delete("1.0", "end")

    def _restore_headers_placeholder(self, _event) -> None:
        if not self.headers.get("1.0", "end").strip():
            self.headers_has_placeholder = True
            self.headers.insert("1.0", self.HEADERS_PLACEHOLDER)

    def apply_theme(self) -> None:
        try:
            import sv_ttk
        except ImportError:
            logger.info("sv-ttk not installed; using default theme")
            return
        sv_ttk.use_dark_theme()
        self.dark_mode = True
        self.theme_btn.configure(state="normal", text="Theme: Light")
        sync_text_colors(self.root, True, self.headers, self.missed_list)

    def toggle_theme(self) -> None:
        import sv_ttk
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            sv_ttk.use_dark_theme()
        else:
            sv_ttk.use_light_theme()
        self.theme_btn.configure(
            text="Theme: Light" if self.dark_mode else "Theme: Dark")
        sync_text_colors(self.root, self.dark_mode,
                         self.headers, self.missed_list)

    @staticmethod
    def _log_callback_exception(exc_type, exc_value, exc_traceback) -> None:
        logger.error("Tkinter callback failed",
                     exc_info=(exc_type, exc_value, exc_traceback))

    def set_running(self, running: bool) -> None:
        self.link.configure(state="disabled" if running else "normal")
        self.headers.configure(state="disabled" if running else "normal")
        if running:
            self.start_btn.configure(state="disabled")
        else:
            self.refresh_start_state()

    def start(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            return
        link = self.playlist_url()
        headers_raw = self.headers_text()
        self.missed_list.delete(0, "end")
        self.missed_label.configure(text="Missed tracks: searching…")
        self.set_running(True)
        self.show_overlay()
        self.worker = threading.Thread(
            target=run_transfer,
            args=(link, headers_raw, self.events),
            daemon=True,
        )
        self.worker.start()

    def pump(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                self.handle(event)
        except queue.Empty:
            pass
        self.root.after(100, self.pump)

    def handle(self, event: tuple) -> None:
        kind = event[0]
        if kind == "status":
            self.status.configure(text=event[1])
            if self.overlay_status is not None:
                self.overlay_status.configure(
                    text=self._short_status(event[1]))
        elif kind == "mode":
            self.progress.configure(mode=event[1])
            if self.overlay_progress is not None:
                self.overlay_progress.configure(mode=event[1])
            if event[1] == "determinate":
                self.progress.configure(maximum=event[2], value=0)
                if self.overlay_progress is not None:
                    self.overlay_progress.configure(maximum=event[2], value=0)
        elif kind == "progress":
            self.progress.configure(value=event[1])
            if self.overlay_progress is not None:
                self.overlay_progress.configure(value=event[1])
        elif kind == "failed":
            message, failure_kind = event[1], event[2]
            self.hide_overlay()
            self.set_running(False)
            self.status.configure(text="Failed.")
            if failure_kind == "auth":
                messagebox.showwarning("Headers expired", message)
            else:
                messagebox.showerror("Transfer failed", message)
        elif kind == "finished":
            self.hide_overlay()
            self.set_running(False)
            result = event[1]
            self.status.configure(text="Done.")
            self.progress.configure(value=self.progress.cget("maximum"))
            self.show_missed(result.get("missed") or [])
            self.show_finished_dialog(result)

    def show_missed(self, missed: list) -> None:
        """Fill the fixed-height missed-tracks list below the progress bar."""
        self.missed_list.delete(0, "end")
        for track in missed:
            self.missed_list.insert("end", str(track))
        if missed:
            self.missed_label.configure(text=f"Missed tracks ({len(missed)}):")
        else:
            self.missed_label.configure(
                text="Missed tracks (0) – all tracks found.")

    def show_finished_dialog(self, result: dict) -> None:
        """Completion popup with a clickable GitHub star link."""

        dialog = tk.Toplevel(self.root)
        dialog.title("Playlist created")
        dialog.transient(self.root)
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame,
            text=f"'{result['playlist_name']}' created "
            f"({result['found']}/{result['total']} tracks found).",
            wraplength=360,
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            frame,
            text="Found SpotTransfer helpful? Please star "
            "the project on GitHub, it's free and it helps a lot:",
            wraplength=360,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(12, 2))
        link = ttk.Label(
            frame,
            text=GITHUB_URL,
            foreground="#58a6ff",
            cursor="hand2",
            font=("TkDefaultFont", 9, "underline"),
            takefocus=True,
        )
        link.grid(row=2, column=0, sticky="w")
        def _open_link(_event=None):
            webbrowser.open(GITHUB_URL)
            return "break"

        link.bind("<Button-1>", _open_link)
        link.bind("<Return>", _open_link)

        ok_btn = ttk.Button(frame, text="OK", command=dialog.destroy)
        ok_btn.grid(row=3, column=0, sticky="e", pady=(16, 0))

        dialog.bind("<Return>", lambda _event: dialog.destroy())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

        dialog.update_idletasks()
        x = self.root.winfo_rootx() + max(
            0, (self.root.winfo_width() - dialog.winfo_width()) // 2)
        y = self.root.winfo_rooty() + max(
            0, (self.root.winfo_height() - dialog.winfo_height()) // 2)
        dialog.geometry(f"+{x}+{y}")

        try:
            dialog.grab_set()
        except tk.TclError:
            pass
        ok_btn.focus_set()


def self_check() -> int:
    """Headless sanity check: imports only, no window is opened."""

    print(f"python: {sys.version.split()[0]}")
    print("tkinter: import ok")
    try:
        backend = load_backend()
    except RuntimeError as error:
        print(f"backend: MISSING\n{error}")
        return 1
    for helper in ("extract_spotify_playlist_id", "get_spotify_playlist_name",
                   "get_spotify_tracks", "parse_browser_headers"):
        assert callable(getattr(backend, helper, None)), helper
    print(f"transfer logic: {BASE_DIR} (selfhost helpers ok)")
    try:
        import ytmusicapi  # noqa: F401
        import spotapi  # noqa: F401
        print("deps: ytmusicapi + spotapi installed")
    except ImportError as error:
        print(f"deps: MISSING ({error})\n"
              "  pip install -r requirements.txt")
        return 1
    print("check: OK — run without --check to open the app")
    return 0


if __name__ == "__main__":
    enable_hidpi()
    ensure_deps()
    if "--check" in sys.argv:
        raise SystemExit(self_check())
    root = tk.Tk()
    App(root)
    root.mainloop()
