#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import json
import time
import ftplib
import pathlib
import datetime
import traceback
import threading
import urllib.request
import shutil
import fnmatch
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except Exception as e:
    raise SystemExit("Tkinter is required. Error: %s" % e)

APP_NAME = "AutomationZ Mod Update Auto-Deploy"
APP_VERSION = "1.1.0"

BASE_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
STATE_DIR  = BASE_DIR / "state"
LOGS_DIR   = BASE_DIR / "logs"

PROFILES_PATH = CONFIG_DIR / "profiles.json"
MODS_PATH     = CONFIG_DIR / "mods.json"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
STATE_PATH    = STATE_DIR / "mod_state.json"

# ---- theme colors (shared across AutomationZ tools) ----
C_BG = "#333333"       # base background
C_PANEL = "#363636"    # panels
C_TEXT = "#e6e6e6"     # readable light text
C_MUTED = "#b8b8b8"
C_ACCENT = "#4CAF50"   # AutomationZ green
C_WARN = "#ffb74d"
C_BAD = "#ef5350"

def apply_dark_theme(root: tk.Tk) -> ttk.Style:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(bg=C_BG)

    style.configure(".", background=C_BG, foreground=C_TEXT)
    style.configure("TFrame", background=C_BG)
    style.configure("TLabel", background=C_BG, foreground=C_TEXT)
    style.configure("TLabelFrame", background=C_BG, foreground=C_TEXT)
    style.configure("TLabelFrame.Label", background=C_BG, foreground=C_TEXT)

    style.configure("TEntry", fieldbackground=C_PANEL, background=C_PANEL, foreground=C_TEXT, insertcolor=C_TEXT)
    style.configure("TCombobox", fieldbackground=C_PANEL, background=C_PANEL, foreground=C_TEXT, arrowcolor=C_TEXT)
    style.map("TCombobox",
              fieldbackground=[("readonly", C_PANEL)],
              background=[("readonly", C_PANEL)],
              foreground=[("readonly", C_TEXT)])

    style.configure("TNotebook", background=C_BG, borderwidth=0)
    style.configure("TNotebook.Tab", background=C_PANEL, foreground=C_TEXT, padding=(10, 6))
    style.map("TNotebook.Tab",
              background=[("selected", "#242424"), ("active", "#2d2d2d")],
              foreground=[("disabled", C_MUTED)])

    style.configure("TButton", background=C_PANEL, foreground=C_TEXT, borderwidth=1, focusthickness=2, focuscolor=C_ACCENT)
    style.map("TButton",
              background=[("active", "#3a3a3a"), ("pressed", "#3f3f3f")],
              foreground=[("disabled", C_MUTED)])

    style.configure(
        "Colored.TButton",
        foreground="white",
        background=C_ACCENT,
        bordercolor=C_ACCENT,
        padding=(10, 6),
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "Colored.TButton",
        background=[
            ("active", "#66BB6A"),
            ("pressed", "#388E3C"),
            ("disabled", "#555555"),
        ],
        foreground=[
            ("disabled", "#aaaaaa"),
        ],
    )

    style.configure("TSeparator", background="#1f1f1f")
    return style

def style_text_widget(txt: tk.Text) -> None:
    txt.configure(
        bg=C_PANEL,
        fg=C_TEXT,
        insertbackground=C_TEXT,
        selectbackground="#1f3b2b",
        selectforeground="#ffffff",
        relief="flat",
        highlightthickness=1,
        highlightbackground="#1f1f1f",
        highlightcolor=C_ACCENT,
        bd=0
    )

def style_listbox(lb: tk.Listbox) -> None:
    lb.configure(
        bg=C_PANEL,
        fg=C_TEXT,
        selectbackground="#1f3b2b",
        selectforeground="#ffffff",
        relief="flat",
        highlightthickness=1,
        highlightbackground="#1f1f1f",
        highlightcolor=C_ACCENT,
        bd=0
    )

def now_stamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def load_json(path: pathlib.Path, default_obj):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_obj, f, indent=4)
        return default_obj
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: pathlib.Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4)

def norm_remote(path: str) -> str:
    p = (path or "").replace("\\", "/").replace("\r","").replace("\n","")
    return p.strip("/")

def ensure_clean_dir(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

class Logger:
    def __init__(self, widget: tk.Text):
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.widget = widget
        self.file = LOGS_DIR / ("mod_autodeploy_" + now_stamp() + ".log")
        self._write(APP_NAME + " v" + APP_VERSION + "\n\n")

    def _write(self, s: str) -> None:
        with open(self.file, "a", encoding="utf-8") as f:
            f.write(s)

    def log(self, level: str, msg: str) -> None:
        line = f"[{level}] {msg}\n"
        self._write(line)
        try:
            self.widget.configure(state="normal")
            self.widget.insert("end", line)
            self.widget.see("end")
            self.widget.configure(state="disabled")
        except Exception:
            pass

    def info(self, msg: str) -> None: self.log("INFO", msg)
    def warn(self, msg: str) -> None: self.log("WARN", msg)
    def error(self, msg: str) -> None: self.log("ERROR", msg)

@dataclass
class Profile:
    name: str
    host: str
    port: int
    username: str
    password: str
    tls: bool
    root: str

@dataclass
class ModWatch:
    name: str
    enabled: bool
    local_path: str
    remote_path: str

def load_profiles() -> Tuple[List[Profile], Optional[str]]:
    obj = load_json(PROFILES_PATH, {"profiles": [], "active_profile": None})
    out: List[Profile] = []
    for p in obj.get("profiles", []):
        out.append(Profile(
            name=p.get("name","Unnamed"),
            host=p.get("host",""),
            port=int(p.get("port",21)),
            username=p.get("username",""),
            password=p.get("password",""),
            tls=bool(p.get("tls", False)),
            root=p.get("root","/"),
        ))
    return out, obj.get("active_profile")

def save_profiles(profiles: List[Profile], active: Optional[str]) -> None:
    save_json(PROFILES_PATH, {"profiles":[p.__dict__ for p in profiles], "active_profile": active})

def load_mods() -> List[ModWatch]:
    obj = load_json(MODS_PATH, {"mods": []})
    out: List[ModWatch] = []
    for m in obj.get("mods", []):
        out.append(ModWatch(
            name=m.get("name","@UnnamedMod"),
            enabled=bool(m.get("enabled", True)),
            local_path=m.get("local_path",""),
            remote_path=m.get("remote_path","mods/" + m.get("name","@UnnamedMod")),
        ))
    return out

def save_mods(mods: List[ModWatch]) -> None:
    save_json(MODS_PATH, {"mods":[m.__dict__ for m in mods]})

def load_settings() -> dict:
    # NOTE: Restart options removed on purpose (per request).
    return load_json(SETTINGS_PATH, {
        "app": {
            "timeout_seconds": 30,
            "tick_seconds": 60,
            "auto_start": False,
            "workshop_dir": r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop"
        },
        "deploy": {
            "mode": "ftp",  # ftp | local
            "remote_mods_base": "mods",
            "local_deploy_dir": "",  # used when mode=local
            "debounce_seconds": 60,  # wait for Steam to finish writing before deploy
            "bundle_window_seconds": 30,  # bundle multiple updates into one deploy batch
            "exclude_patterns": ["*.log","*.tmp","*.cache","*.bak","*.old","*.swp","*.part","*.download"]
        },
        "discord": {
            "webhook_url": "",
            "notify_update_found": True,
            "notify_upload_done": True,
            "notify_failure": True
        }
    })

def discord_post(webhook_url: str, text: str, timeout: int = 15) -> Tuple[bool, str]:
    webhook_url = (webhook_url or "").strip()
    if not webhook_url:
        return False, "No webhook_url configured"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        payload = {"content": text}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": f"{APP_NAME}/{APP_VERSION}"},
            method="POST",
        )
        with opener.open(req, timeout=timeout) as resp:
            code = getattr(resp, "status", 200)
            return (200 <= code < 300), f"HTTP {code}"
    except Exception as e:
        return False, str(e)

class FTPClient:
    def __init__(self, profile: Profile, timeout: int):
        self.p = profile
        self.timeout = timeout
        self.ftp = None

    def connect(self):
        ftp = ftplib.FTP_TLS(timeout=self.timeout) if self.p.tls else ftplib.FTP(timeout=self.timeout)
        ftp.connect(self.p.host, self.p.port)
        ftp.login(self.p.username, self.p.password)
        if self.p.tls and isinstance(ftp, ftplib.FTP_TLS):
            ftp.prot_p()
        self.ftp = ftp

    def close(self):
        try:
            if self.ftp:
                self.ftp.quit()
        except Exception:
            try:
                if self.ftp:
                    self.ftp.close()
            except Exception:
                pass
        self.ftp = None

    def _ensure_dir(self, remote_dir: str):
        remote_dir = "/" + norm_remote(remote_dir)
        parts = [p for p in remote_dir.split("/") if p]
        cur = ""
        for part in parts:
            cur += "/" + part
            try:
                self.ftp.mkd(cur)
            except Exception:
                pass

    def upload_file(self, local_path: pathlib.Path, remote_full: str):
        remote_full = "/" + norm_remote(remote_full)
        remote_dir = "/" + "/".join(remote_full.split("/")[:-1])
        self._ensure_dir(remote_dir)
        with open(local_path, "rb") as f:
            self.ftp.storbinary("STOR " + remote_full, f)

    def upload_tree(self, local_dir: pathlib.Path, remote_dir: str, log_cb=None, exclude_patterns: Optional[List[str]] = None) -> Tuple[int, int]:
        local_dir = local_dir.resolve()
        remote_dir = "/" + norm_remote(remote_dir)
        patterns = exclude_patterns or []
        files = 0
        total_bytes = 0

        for root, _, fnames in os.walk(local_dir):
            root_p = pathlib.Path(root)
            rel_dir = root_p.relative_to(local_dir).as_posix()
            target_dir = remote_dir if rel_dir == "." else remote_dir + "/" + rel_dir
            self._ensure_dir(target_dir)

            for fname in fnames:
                lp = root_p / fname
                rel_file = lp.relative_to(local_dir).as_posix()
                if should_exclude(rel_file, patterns):
                    continue

                rp = target_dir + "/" + fname
                try:
                    sz = lp.stat().st_size
                except Exception:
                    sz = 0
                self.upload_file(lp, rp)
                files += 1
                total_bytes += int(sz)
                if log_cb:
                    log_cb(f"Uploaded: {lp.name} -> {rp}")
        return files, total_bytes

def copy_tree(local_src: pathlib.Path, local_dst: pathlib.Path, log_cb=None, exclude_patterns: Optional[List[str]] = None) -> Tuple[int, int]:
    """
    Mirror-copy local_src into local_dst (overwrite existing files), ignoring excluded patterns.
    Returns: (file_count, total_bytes)
    """
    local_src = local_src.resolve()
    local_dst = local_dst.resolve()
    patterns = exclude_patterns or []
    files = 0
    total_bytes = 0

    for root, dirs, fnames in os.walk(local_src):
        root_p = pathlib.Path(root)
        rel = root_p.relative_to(local_src)
        target_dir = local_dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)

        for d in dirs:
            (target_dir / d).mkdir(parents=True, exist_ok=True)

        for fname in fnames:
            sp = root_p / fname
            rel_file = sp.relative_to(local_src).as_posix()
            if should_exclude(rel_file, patterns):
                continue

            dp = target_dir / fname
            try:
                sz = sp.stat().st_size
            except Exception:
                sz = 0
            shutil.copy2(sp, dp)
            files += 1
            total_bytes += int(sz)
            if log_cb:
                log_cb(f"Copied: {sp.name} -> {dp}")
    return files, total_bytes

def should_exclude(rel_posix: str, patterns: List[str]) -> bool:
    rel_posix = (rel_posix or "").replace("\\", "/")
    for pat in patterns or []:
        pat = (pat or "").strip()
        if not pat:
            continue
        # match both full relative path and basename
        if fnmatch.fnmatch(rel_posix, pat) or fnmatch.fnmatch(pathlib.Path(rel_posix).name, pat):
            return True
    return False

def folder_fingerprint(path: pathlib.Path, exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Return a lightweight fingerprint of a folder, ignoring excluded files."""
    patterns = exclude_patterns or []
    files = 0
    total = 0
    latest = 0.0
    for root, _, fnames in os.walk(path):
        root_p = pathlib.Path(root)
        for fn in fnames:
            try:
                p = root_p / fn
                rel = p.relative_to(path).as_posix()
                if should_exclude(rel, patterns):
                    continue
                st = p.stat()
                files += 1
                total += int(st.st_size)
                if st.st_mtime > latest:
                    latest = st.st_mtime
            except Exception:
                pass
    return {"files": files, "bytes": total, "latest_mtime": latest}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.style = apply_dark_theme(self)
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1100x740")
        self.minsize(980, 640)

        for p in [CONFIG_DIR, STATE_DIR, LOGS_DIR]:
            p.mkdir(parents=True, exist_ok=True)

        self.settings = load_settings()
        self.timeout = int(self.settings.get("app",{}).get("timeout_seconds", 30))
        self.tick_seconds = int(self.settings.get("app",{}).get("tick_seconds", 60))
        self.auto_start = bool(self.settings.get("app",{}).get("auto_start", False))
        self.workshop_dir = pathlib.Path(self.settings.get("app",{}).get("workshop_dir","")).expanduser()

        dpl = self.settings.get("deploy", {})
        self.debounce_seconds = int(dpl.get("debounce_seconds", 60) or 60)
        self.bundle_window_seconds = int(dpl.get("bundle_window_seconds", 30) or 30)
        self.exclude_patterns = list(dpl.get("exclude_patterns", []) or [])
        # pending queue: mod_name -> last_change_ts
        self.pending: Dict[str, float] = {}

        self.profiles, self.active_profile = load_profiles()
        self.mods = load_mods()
        self.state = load_json(STATE_PATH, {"mods": {}}).get("mods", {})
        # Backward compatible state upgrade (from plain fingerprint dicts)
        for k, v in list(self.state.items()):
            if isinstance(v, dict) and "fp" in v:
                continue
            if isinstance(v, dict) and {"files","bytes","latest_mtime"}.issubset(set(v.keys())):
                self.state[k] = {"fp": v, "last_change": 0.0, "deployed_fp": v}
            else:
                self.state[k] = {"fp": v, "last_change": 0.0, "deployed_fp": v}

        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._busy_lock = threading.Lock()

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.tab_dash = ttk.Frame(nb)
        self.tab_profiles = ttk.Frame(nb)
        self.tab_mods = ttk.Frame(nb)
        self.tab_settings = ttk.Frame(nb)
        self.tab_help = ttk.Frame(nb)

        nb.add(self.tab_dash, text="Dashboard")
        nb.add(self.tab_profiles, text="Profiles")
        nb.add(self.tab_mods, text="Mods")
        nb.add(self.tab_settings, text="Settings")
        nb.add(self.tab_help, text="Help")

        log_box = ttk.LabelFrame(self, text="Log")
        log_box.pack(fill="both", expand=False, padx=10, pady=8)
        self.log_text = tk.Text(log_box, height=10, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)
        style_text_widget(self.log_text)
        self.log = Logger(self.log_text)

        self._build_dash()
        self._build_profiles()
        self._build_mods()
        self._build_settings()
        self._build_help()

        self.refresh_profiles_combo()
        self.refresh_profiles_list()
        self.refresh_mods_list()
        self.refresh_status()

        if self.auto_start:
            self.start_monitor()

    # Dashboard
    def _build_dash(self):
        f = self.tab_dash
        top = ttk.Frame(f); top.pack(fill="x", padx=12, pady=10)

        ttk.Label(top, text="Profile:").grid(row=0, column=0, sticky="w")
        self.cmb_profile = ttk.Combobox(top, state="readonly", width=34)
        self.cmb_profile.grid(row=0, column=1, sticky="w", padx=(6,18))

        ttk.Button(top, text="Test Connection", command=self.test_conn, style="Colored.TButton").grid(row=0, column=2, sticky="w", padx=(0,10))
        ttk.Button(top, text="Scan Now", command=self.scan_once, style="Colored.TButton").grid(row=0, column=3, sticky="w", padx=(0,10))
        ttk.Button(top, text="Start Monitor", command=self.start_monitor, style="Colored.TButton").grid(row=0, column=4, sticky="w", padx=(0,10))
        ttk.Button(top, text="Stop", command=self.stop_monitor, style="Colored.TButton").grid(row=0, column=5, sticky="w")

        status = ttk.LabelFrame(f, text="Status")
        status.pack(fill="x", padx=12, pady=(0,10))

        self.lbl_workshop = ttk.Label(status, text="Workshop: -")
        self.lbl_workshop.grid(row=0, column=0, sticky="w", padx=10, pady=6, columnspan=3)

        self.lbl_last = ttk.Label(status, text="Last scan: -")
        self.lbl_last.grid(row=1, column=0, sticky="w", padx=10, pady=6)

        self.lbl_queue = ttk.Label(status, text="Deploy: idle")
        self.lbl_queue.grid(row=1, column=1, sticky="w", padx=10, pady=6)

        box = ttk.LabelFrame(f, text="Recent detected updates")
        box.pack(fill="both", expand=True, padx=12, pady=(0,10))
        self.lst_updates = tk.Listbox(box, height=14, exportselection=False)
        self.lst_updates.pack(fill="both", expand=True, padx=8, pady=8)
        style_listbox(self.lst_updates)

        ttk.Button(f, text="Clear List", command=lambda: self.lst_updates.delete(0, "end"), style="Colored.TButton").pack(anchor="w", padx=12, pady=(0,12))

    def refresh_status(self):
        self.lbl_workshop.configure(text=f"Workshop: {self.workshop_dir}")
        last = getattr(self, "_last_scan", None)
        self.lbl_last.configure(text=f"Last scan: {last or '-'}")

    def selected_profile(self) -> Optional[Profile]:
        name = (self.cmb_profile.get() or "").strip()
        for p in self.profiles:
            if p.name == name:
                return p
        return None

    def test_conn(self):
        p = self.selected_profile()
        if not p:
            messagebox.showwarning("No profile", "Create/select a profile in Profiles tab.")
            return
        self.log.info(f"Testing connection to {p.host}:{p.port} TLS={p.tls}")
        cli = FTPClient(p, self.timeout)
        try:
            cli.connect()
            self.log.info("Connected OK.")
            messagebox.showinfo("OK", "Connected.")
        except Exception as e:
            self.log.error("Connection failed: " + str(e))
            messagebox.showerror("Failed", str(e))
        finally:
            cli.close()

    def start_monitor(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self.log.info(f"Monitor started (tick={self.tick_seconds}s).")

    def stop_monitor(self):
        self._stop_evt.set()
        self.log.info("Monitor stopping...")

    def _monitor_loop(self):
        while not self._stop_evt.is_set():
            try:
                self.scan_once(silent=True)
            except Exception as e:
                self.log.error("Monitor loop error: " + str(e))
            for _ in range(max(1, self.tick_seconds)):
                if self._stop_evt.is_set():
                    break
                time.sleep(1)

    
    def _pending_earliest(self) -> Optional[float]:
        return min(self.pending.values()) if self.pending else None

    def _maybe_start_deploy(self):
        # Don't start if already deploying
        try:
            if self._busy_lock.locked():
                return
        except Exception:
            pass

        if not self.pending:
            return

        now_ts = time.time()
        earliest = self._pending_earliest()
        if earliest is None:
            return

        # Wait for oldest change to become stable (debounce)
        if now_ts - earliest < self.debounce_seconds:
            return

        # Bundle window: after first mod becomes stable, wait a bit more to collect additional mod updates
        if now_ts < (earliest + self.debounce_seconds + self.bundle_window_seconds):
            return

        # Build batch: all mods that have been stable for debounce_seconds
        ready_names = []
        for name, t_change in list(self.pending.items()):
            if now_ts - float(t_change) >= self.debounce_seconds:
                ready_names.append(name)

        if not ready_names:
            return

        # Map names -> ModWatch objects
        name_to_mod = {m.name: m for m in self.mods if m.enabled}
        batch = [name_to_mod[n] for n in ready_names if n in name_to_mod]

        if not batch:
            # nothing enabled anymore
            for n in ready_names:
                self.pending.pop(n, None)
            return

        self.log.info(f"Queue: starting deploy for {len(batch)} mod(s) after debounce/bundle.")
        threading.Thread(target=self._deploy_many, args=(batch,), daemon=True).start()

    def scan_once(self, silent: bool = False):
        enabled = [m for m in self.mods if m.enabled]
        if not enabled:
            if not silent:
                messagebox.showwarning("No mods", "No enabled mods. Add mods in Mods tab.")
            return

        self._last_scan = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.after(0, self.refresh_status)

        now_ts = time.time()
        changed_now: List[ModWatch] = []

        for m in enabled:
            lp = pathlib.Path(m.local_path).expanduser()
            if not lp.exists() or not lp.is_dir():
                self.log.warn(f"Missing local mod folder: {lp}")
                continue

            fp = folder_fingerprint(lp, self.exclude_patterns)

            st = self.state.get(m.name) if isinstance(self.state.get(m.name), dict) else None
            if not st or "fp" not in st:
                st = {"fp": None, "last_change": 0.0, "deployed_fp": None}

            if st.get("fp") != fp:
                st["fp"] = fp
                st["last_change"] = now_ts
                # mark pending (debounce will decide when to deploy)
                self.pending[m.name] = now_ts
                changed_now.append(m)

            self.state[m.name] = st

        save_json(STATE_PATH, {"mods": self.state})

        if changed_now:
            for m in changed_now:
                self.lst_updates.insert("end", f"{self._last_scan} | UPDATED: {m.name} (queued)")

            d = self.settings.get("discord", {})
            if d.get("notify_update_found", True) and (d.get("webhook_url") or "").strip():
                names = ", ".join([m.name for m in changed_now][:25])
                discord_post(d.get("webhook_url",""), f"🧩 {APP_NAME}: update detected (queued): {names}")

            if not silent:
                messagebox.showinfo("Queued", f"Queued {len(changed_now)} mod update(s). Will deploy after cooldown.")

        # Try to start a deploy if queue is ready
        self._maybe_start_deploy()

        if not changed_now and not silent:
            self.log.info("Scan done. No changes.")
            messagebox.showinfo("Scan", "No mod updates detected.")

    def _deploy_many(self, mods: List[ModWatch]):
        with self._busy_lock:
            self.after(0, lambda: self.lbl_queue.configure(text=f"Deploy: running ({len(mods)} mod(s))"))
            dpl = self.settings.get("deploy", {})
            mode = (dpl.get("mode", "ftp") or "ftp").strip().lower()

            p = self.selected_profile()

            if mode == "ftp" and not p:
                self.log.error("No profile selected for FTP deploy.")
                self.after(0, lambda: self.lbl_queue.configure(text="Deploy: idle"))
                # if more mods are queued, try to deploy next batch
                try:
                    self._maybe_start_deploy()
                except Exception:
                    pass
                return

            cli = FTPClient(p, self.timeout) if mode == "ftp" else None
            try:
                if mode == "ftp":
                    cli.connect()

                base_remote = norm_remote(dpl.get("remote_mods_base","mods") or "mods")
                root = norm_remote((p.root if p else "") or "/")
                local_deploy_dir = pathlib.Path(dpl.get("local_deploy_dir","") or "").expanduser()

                if mode == "local":
                    if not str(local_deploy_dir).strip():
                        raise RuntimeError("Deploy mode is LOCAL but local_deploy_dir is empty. Set it in Settings.")
                    local_deploy_dir.mkdir(parents=True, exist_ok=True)

                total_files = 0
                total_bytes = 0

                for m in mods:
                    lp = pathlib.Path(m.local_path).expanduser().resolve()
                    if not lp.exists():
                        self.log.warn(f"Skip missing folder: {lp}")
                        continue

                    rel_remote = norm_remote(m.remote_path) if (m.remote_path or "").strip() else f"{base_remote}/{m.name}"

                    if mode == "ftp":
                        remote_full = "/" + ("/".join([root, rel_remote])).strip("/")
                        self.log.info(f"Deploying (FTP) {m.name} -> {remote_full}")
                        files, bytes_up = cli.upload_tree(lp, remote_full, log_cb=self.log.info, exclude_patterns=self.exclude_patterns)
                        self.log.info(f"Deploy done: {m.name} files={files} bytes={bytes_up}")
                        total_files += files
                        total_bytes += bytes_up
                        # mark as deployed and clear from pending queue
                        st = self.state.get(m.name, {"fp": None, "last_change": 0.0, "deployed_fp": None})
                        if isinstance(st, dict) and "fp" in st:
                            st["deployed_fp"] = st.get("fp")
                            self.state[m.name] = st
                        self.pending.pop(m.name, None)

                    else:
                        # local mode mirrors into: <local_deploy_dir>/<rel_remote>
                        dest = (local_deploy_dir / rel_remote)
                        self.log.info(f"Deploying (LOCAL) {m.name} -> {dest}")
                        files, bytes_up = copy_tree(lp, dest, log_cb=self.log.info, exclude_patterns=self.exclude_patterns)
                        self.log.info(f"Deploy done: {m.name} files={files} bytes={bytes_up}")
                        total_files += files
                        total_bytes += bytes_up
                        # mark as deployed and clear from pending queue
                        st = self.state.get(m.name, {"fp": None, "last_change": 0.0, "deployed_fp": None})
                        if isinstance(st, dict) and "fp" in st:
                            st["deployed_fp"] = st.get("fp")
                            self.state[m.name] = st
                        self.pending.pop(m.name, None)


                save_json(STATE_PATH, {"mods": self.state})

                disc = self.settings.get("discord", {})
                if disc.get("notify_upload_done", True) and (disc.get("webhook_url") or "").strip():
                    action = "copy" if mode == "local" else "upload"
                    names = ", ".join([m.name for m in mods][:25])
                    discord_post(disc.get("webhook_url",""), f"✅ {APP_NAME}: {action} finished for {len(mods)} mod(s) ({total_files} files, {total_bytes} bytes).\n{names}")

            except Exception as e:
                self.log.error("Deploy failed: " + str(e))
                self.log.error(traceback.format_exc())
                save_json(STATE_PATH, {"mods": self.state})

                disc = self.settings.get("discord", {})
                if disc.get("notify_failure", True) and (disc.get("webhook_url") or "").strip():
                    discord_post(disc.get("webhook_url",""), f"❌ {APP_NAME}: deploy failed: {e}")
            finally:
                try:
                    if cli:
                        cli.close()
                except Exception:
                    pass
                self.after(0, lambda: self.lbl_queue.configure(text="Deploy: idle"))
                # if more mods are queued, try to deploy next batch
                try:
                    self._maybe_start_deploy()
                except Exception:
                    pass

    # Profiles
    def _build_profiles(self):
        f = self.tab_profiles
        outer = ttk.Frame(f); outer.pack(fill="both", expand=True, padx=12, pady=10)

        left = ttk.LabelFrame(outer, text="Profiles")
        left.pack(side="left", fill="both", expand=False)

        self.lst_profiles = tk.Listbox(left, width=28, height=18, exportselection=False)
        self.lst_profiles.pack(fill="both", expand=True, padx=8, pady=8)
        style_listbox(self.lst_profiles)
        self.lst_profiles.bind("<<ListboxSelect>>", lambda e: self.on_profile_select())

        btns = ttk.Frame(left); btns.pack(fill="x", padx=8, pady=(0,8))
        ttk.Button(btns, text="New", command=self.profile_new, style="Colored.TButton").pack(side="left")
        ttk.Button(btns, text="Delete", command=self.profile_delete, style="Colored.TButton").pack(side="left", padx=6)
        ttk.Button(btns, text="Set Active", command=self.profile_set_active, style="Colored.TButton").pack(side="left")

        right = ttk.LabelFrame(outer, text="Profile details")
        right.pack(side="left", fill="both", expand=True, padx=(12,0))
        form = ttk.Frame(right); form.pack(fill="both", expand=True, padx=10, pady=10)

        self.v_name = tk.StringVar()
        self.v_host = tk.StringVar()
        self.v_port = tk.StringVar(value="21")
        self.v_user = tk.StringVar()
        self.v_pass = tk.StringVar()
        self.v_tls  = tk.BooleanVar(value=False)
        self.v_root = tk.StringVar(value="/dayzstandalone")

        r=0
        ttk.Label(form, text="Name").grid(row=r, column=0, sticky="w"); ttk.Entry(form, textvariable=self.v_name, width=40).grid(row=r, column=1, sticky="w", pady=2); r+=1
        ttk.Label(form, text="Host").grid(row=r, column=0, sticky="w"); ttk.Entry(form, textvariable=self.v_host, width=40).grid(row=r, column=1, sticky="w", pady=2); r+=1
        ttk.Label(form, text="Port").grid(row=r, column=0, sticky="w"); ttk.Entry(form, textvariable=self.v_port, width=12).grid(row=r, column=1, sticky="w", pady=2); r+=1
        ttk.Label(form, text="Username").grid(row=r, column=0, sticky="w"); ttk.Entry(form, textvariable=self.v_user, width=40).grid(row=r, column=1, sticky="w", pady=2); r+=1
        ttk.Label(form, text="Password").grid(row=r, column=0, sticky="w"); ttk.Entry(form, textvariable=self.v_pass, width=40, show="*").grid(row=r, column=1, sticky="w", pady=2); r+=1
        ttk.Checkbutton(form, text="Use FTPS (FTP over TLS)", variable=self.v_tls).grid(row=r, column=1, sticky="w", pady=2); r+=1
        ttk.Label(form, text="Remote root").grid(row=r, column=0, sticky="w"); ttk.Entry(form, textvariable=self.v_root, width=40).grid(row=r, column=1, sticky="w", pady=2); r+=1

        actions = ttk.Frame(right); actions.pack(fill="x", padx=10, pady=(0,10))
        ttk.Button(actions, text="Save Changes", command=self.profile_save, style="Colored.TButton").pack(side="left")

    def refresh_profiles_combo(self):
        names = [p.name for p in self.profiles]
        self.cmb_profile["values"] = names
        if self.active_profile and self.active_profile in names:
            self.cmb_profile.set(self.active_profile)
        elif names:
            self.cmb_profile.set(names[0])
        else:
            self.cmb_profile.set("")

    def refresh_profiles_list(self):
        self.lst_profiles.delete(0, "end")
        for p in self.profiles:
            suffix = " (active)" if self.active_profile == p.name else ""
            self.lst_profiles.insert("end", p.name + suffix)

    def _sel_index(self, lb: tk.Listbox) -> Optional[int]:
        sel = lb.curselection()
        return int(sel[0]) if sel else None

    def on_profile_select(self):
        idx = self._sel_index(self.lst_profiles)
        if idx is None: return
        p = self.profiles[idx]
        self.v_name.set(p.name); self.v_host.set(p.host); self.v_port.set(str(p.port))
        self.v_user.set(p.username); self.v_pass.set(p.password); self.v_tls.set(p.tls); self.v_root.set(p.root)

    def profile_new(self):
        n = "Profile_" + str(len(self.profiles) + 1)
        self.profiles.append(Profile(n, "", 21, "", "", False, "/dayzstandalone"))
        self.active_profile = n
        save_profiles(self.profiles, self.active_profile)
        self.refresh_profiles_list(); self.refresh_profiles_combo()

    def profile_delete(self):
        idx = self._sel_index(self.lst_profiles)
        if idx is None: return
        p = self.profiles[idx]
        if not messagebox.askyesno("Delete", f"Delete profile '{p.name}'?"): return
        del self.profiles[idx]
        if self.active_profile == p.name:
            self.active_profile = self.profiles[0].name if self.profiles else None
        save_profiles(self.profiles, self.active_profile)
        self.refresh_profiles_list(); self.refresh_profiles_combo()

    def profile_set_active(self):
        idx = self._sel_index(self.lst_profiles)
        if idx is None: return
        self.active_profile = self.profiles[idx].name
        save_profiles(self.profiles, self.active_profile)
        self.refresh_profiles_list(); self.refresh_profiles_combo()

    def profile_save(self):
        try:
            port = int((self.v_port.get() or "21").strip())
        except ValueError:
            messagebox.showerror("Invalid", "Port must be a number.")
            return

        new_profile = Profile(
            name=self.v_name.get().strip() or "Unnamed",
            host=self.v_host.get().strip(),
            port=port,
            username=self.v_user.get().strip(),
            password=self.v_pass.get(),
            tls=bool(self.v_tls.get()),
            root=self.v_root.get().strip() or "/"
        )

        i = self._sel_index(self.lst_profiles)
        existing_names = [p.name for p in self.profiles]

        if i is None:
            if new_profile.name in existing_names:
                messagebox.showerror("Duplicate name", "A profile with this name already exists.")
                return
            self.profiles.append(new_profile)
            self.active_profile = new_profile.name
        else:
            old_name = self.profiles[i].name
            if new_profile.name != old_name and new_profile.name in existing_names:
                messagebox.showerror("Duplicate name", "A profile with this name already exists.")
                return
            self.profiles[i] = new_profile
            if self.active_profile == old_name:
                self.active_profile = new_profile.name

        save_profiles(self.profiles, self.active_profile)
        self.refresh_profiles_list()
        self.refresh_profiles_combo()
        messagebox.showinfo("Saved", "Profile saved.")

    # Mods
    def _build_mods(self):
        f = self.tab_mods
        outer = ttk.Frame(f); outer.pack(fill="both", expand=True, padx=12, pady=10)

        left = ttk.LabelFrame(outer, text="Mods to watch")
        left.pack(side="left", fill="both", expand=False)

        self.lst_mods = tk.Listbox(left, width=56, height=18, exportselection=False)
        self.lst_mods.pack(fill="both", expand=True, padx=8, pady=8)
        style_listbox(self.lst_mods)
        self.lst_mods.bind("<<ListboxSelect>>", lambda e: self.on_mod_select())

        btns = ttk.Frame(left); btns.pack(fill="x", padx=8, pady=(0,8))
        ttk.Button(btns, text="New", command=self.mod_new, style="Colored.TButton").pack(side="left")
        ttk.Button(btns, text="Delete", command=self.mod_delete, style="Colored.TButton").pack(side="left", padx=6)
        ttk.Button(btns, text="Save Changes", command=self.mod_save, style="Colored.TButton").pack(side="left")
        ttk.Button(btns, text="Scan Workshop (@folders)", command=self.scan_workshop_add, style="Colored.TButton").pack(side="left", padx=6)

        right = ttk.LabelFrame(outer, text="Mod details")
        right.pack(side="left", fill="both", expand=True, padx=(12,0))
        form = ttk.Frame(right); form.pack(fill="both", expand=True, padx=10, pady=10)

        self.m_name = tk.StringVar(value="@MyMod")
        self.m_enabled = tk.BooleanVar(value=True)
        self.m_local = tk.StringVar()
        self.m_remote = tk.StringVar()

        r=0
        ttk.Label(form, text="Name").grid(row=r, column=0, sticky="w"); ttk.Entry(form, textvariable=self.m_name, width=56).grid(row=r, column=1, sticky="w", pady=2); r+=1
        ttk.Checkbutton(form, text="Enabled", variable=self.m_enabled).grid(row=r, column=1, sticky="w", pady=2); r+=1

        ttk.Label(form, text="Local folder (@Mod)").grid(row=r, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.m_local, width=56).grid(row=r, column=1, sticky="w", pady=2)
        ttk.Button(form, text="Browse…", command=self.browse_mod_folder, style="Colored.TButton").grid(row=r, column=2, sticky="w", padx=8); r+=1

        ttk.Label(form, text="Remote folder (relative to root)").grid(row=r, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.m_remote, width=56).grid(row=r, column=1, sticky="w", pady=2); r+=1

        hint = tk.Text(form, height=8, wrap="word")
        hint.grid(row=r, column=0, columnspan=3, sticky="nsew", pady=(10,0))
        style_text_widget(hint)
        hint.insert("1.0",
            "Tip:\n"
            "- Remote folder example: mods/@YourMod\n"
            "- Leave Remote folder empty to default to: <remote_mods_base>/@ModName\n"
            "- This tool checks your local Steam @mod folder for changes, then deploys the full mod folder to keep the server in sync.\n"
            "\n"
            "Recommended settings (smooth + safe):\n"
            "- Debounce/Cooldown: 60–120s (prevents deploying while Steam is still writing files)\n"
            "- Bundle window: 20–60s (groups multiple mod updates into one deploy batch)\n"
            "- Exclude patterns: *.log, *.tmp, *.cache, *.bak, *.old, *.swp, *.part, *.download\n"
            "\n"
            "Workshop folder notes:\n"
            "- Your Workshop dir must contain @folders (DayZ Launcher can open the exact location)\n"
            "- If you use multiple Steam libraries, set the correct workshop folder in Settings\n"
            "\n"
            "Deploy behavior:\n"
            "- FTP mode uploads to your server (FTPS recommended if your host supports it)\n"
            "- LOCAL mode copies to a folder (useful if another tool syncs files to the server)\n"
            "- Deploy is sequential: if 10 mods update, it queues them and deploys one-by-one\n"
            "\n"
            "Discord notifications:\n"
            "- Add a webhook URL to get a message when updates are detected + when deploy finishes\n"
            "- If deploy fails, the error is logged and (optionally) sent to Discord\n"
            "\n"
            "Best practice:\n"
            "- Keep mod names matching the folder name (starts with @)\n"
            "- Make sure your server loads the same mod folder names you deploy\n"
            "- First time: press 'Scan Workshop (@folders)' then run 'Scan Now' to create baseline state\n"
            "\n"
            "Tips:\n"
            "- Remote folder example: mods/@YourMod\n"
            "- Leave Remote folder EMPTY to deploy mods directly into your server root\n"
            "  (example: /dayzstandalone/@YourMod)\n"
            "\n"
            "How paths are built:\n"
            "- Final path = <Profile Root> / <Remote mods base> / <@ModName>\n"
            "\n"
            "Examples:\n"
            "- Root: /dayzstandalone + Base: mods\n"
            "  → /dayzstandalone/mods/@YourMod\n"
            "\n"
            "- Root: /dayzstandalone + Base: (empty)\n"
            "  → /dayzstandalone/@YourMod\n"
            "\n"
            "Notes:\n"
            "- Missing folders are created automatically\n"
            "- Full mod folders are always deployed\n"
            "- Safe to run while Steam is updating mods\n"
            "Safe testing tip:\n"
            "- You can safely test this tool by creating a small text file\n"
            "  inside any @Mod folder (for example: test.txt)\n"
            "\n"
            "Why this is safe:\n"
            "- DayZ completely ignores loose files like .txt\n"
            "- Only .pbo files are loaded by the game engine\n"
            "- Many mods already include README and documentation files\n"
            "\n"
            "What will happen:\n"
            "- The tool detects the folder change\n"
            "- The full mod folder is deployed\n"
            "- Your server and mod remain fully functional\n"
            "\n"
            "This is the recommended way to verify detection and deployment\n"
            "without waiting for a real Steam update.\n"
        )
        hint.configure(state="disabled")

        form.grid_rowconfigure(r, weight=1)
        form.grid_columnconfigure(1, weight=1)

    def browse_mod_folder(self):
        p = filedialog.askdirectory(title="Select @Mod folder")
        if p:
            self.m_local.set(p)
            try:
                name = pathlib.Path(p).name
                if name.startswith("@"):
                    self.m_name.set(name)
            except Exception:
                pass

    def scan_workshop_add(self):
        wdir = self.workshop_dir
        if not wdir.exists():
            messagebox.showerror("Workshop folder not found", f"Not found:\n{wdir}\n\nSet it in Settings.")
            return

        found = []
        for child in sorted(wdir.iterdir()):
            if child.is_dir() and child.name.startswith("@"):
                found.append(child)

        if not found:
            messagebox.showinfo("No mods found", f"No @folders found in:\n{wdir}")
            return

        existing = {m.name for m in self.mods}
        base_remote = norm_remote(self.settings.get("deploy",{}).get("remote_mods_base","mods") or "mods")

        added = 0
        for p in found:
            if p.name in existing:
                continue
            self.mods.append(ModWatch(
                name=p.name,
                enabled=True,
                local_path=str(p),
                remote_path=f"{base_remote}/{p.name}",
            ))
            added += 1

        save_mods(self.mods)
        self.refresh_mods_list()
        messagebox.showinfo("Done", f"Added {added} mod(s) from Workshop.")

    def refresh_mods_list(self):
        self.lst_mods.delete(0, "end")
        for m in self.mods:
            flag = "ON" if m.enabled else "OFF"
            self.lst_mods.insert("end", f"[{flag}] {m.name} | local: {m.local_path} -> remote: {m.remote_path}")

    def on_mod_select(self):
        idx = self._sel_index(self.lst_mods)
        if idx is None: return
        m = self.mods[idx]
        self.m_name.set(m.name)
        self.m_enabled.set(m.enabled)
        self.m_local.set(m.local_path)
        self.m_remote.set(m.remote_path)

    def mod_new(self):
        self.mods.append(ModWatch("@NewMod", True, "", ""))
        save_mods(self.mods)
        self.refresh_mods_list()

    def mod_delete(self):
        idx = self._sel_index(self.lst_mods)
        if idx is None: return
        m = self.mods[idx]
        if not messagebox.askyesno("Delete", f"Delete mod '{m.name}'?"): return
        del self.mods[idx]
        save_mods(self.mods)
        self.refresh_mods_list()

    def mod_save(self):
        idx = self._sel_index(self.lst_mods)
        if idx is None:
            messagebox.showwarning("No mod", "Select a mod in the list.")
            return
        self.mods[idx] = ModWatch(
            name=(self.m_name.get() or "").strip() or "@UnnamedMod",
            enabled=bool(self.m_enabled.get()),
            local_path=(self.m_local.get() or "").strip(),
            remote_path=(self.m_remote.get() or "").strip(),
        )
        save_mods(self.mods)
        self.refresh_mods_list()
        messagebox.showinfo("Saved", "Mod saved.")

    # Settings
    def _build_settings(self):
        f = self.tab_settings
        outer = ttk.Frame(f); outer.pack(fill="both", expand=True, padx=12, pady=10)

        app_box = ttk.LabelFrame(outer, text="App")
        app_box.pack(fill="x", pady=(0,10))

        self.s_timeout = tk.StringVar(value=str(self.timeout))
        self.s_tick = tk.StringVar(value=str(self.tick_seconds))
        self.s_autostart = tk.BooleanVar(value=self.auto_start)
        self.s_workshop = tk.StringVar(value=str(self.workshop_dir))

        ttk.Label(app_box, text="FTP timeout (seconds)").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(app_box, textvariable=self.s_timeout, width=10).grid(row=0, column=1, sticky="w", padx=10, pady=6)

        ttk.Label(app_box, text="Scan tick (seconds)").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(app_box, textvariable=self.s_tick, width=10).grid(row=1, column=1, sticky="w", padx=10, pady=6)

        ttk.Checkbutton(app_box, text="Auto-start monitor on launch", variable=self.s_autostart).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=6)

        ttk.Label(app_box, text="Steam Workshop dir (contains @folders)").grid(row=3, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(app_box, textvariable=self.s_workshop, width=70).grid(row=3, column=1, sticky="w", padx=10, pady=6)
        ttk.Button(app_box, text="Browse…", command=self.browse_workshop, style="Colored.TButton").grid(row=3, column=2, sticky="w", padx=10, pady=6)

        dep_box = ttk.LabelFrame(outer, text="Deploy")
        dep_box.pack(fill="x", pady=(0,10))
        dep = self.settings.get("deploy", {})

        self.s_mode = tk.StringVar(value=str(dep.get("mode","ftp")))
        self.s_remote_base = tk.StringVar(value=str(dep.get("remote_mods_base","mods")))
        self.s_local_deploy = tk.StringVar(value=str(dep.get("local_deploy_dir","")))

        ttk.Label(dep_box, text="Deploy mode").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        ttk.Combobox(dep_box, textvariable=self.s_mode, state="readonly",
                     values=["ftp","local"], width=18).grid(row=0, column=1, sticky="w", padx=10, pady=6)

        ttk.Label(dep_box, text="Remote mods base folder (FTP mode)").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(dep_box, textvariable=self.s_remote_base, width=30).grid(row=1, column=1, sticky="w", padx=10, pady=6)

        ttk.Label(dep_box, text="Local deploy dir (LOCAL mode)").grid(row=2, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(dep_box, textvariable=self.s_local_deploy, width=70).grid(row=2, column=1, sticky="w", padx=10, pady=6)
        ttk.Button(dep_box, text="Browse…", command=self.browse_local_deploy, style="Colored.TButton").grid(row=2, column=2, sticky="w", padx=10, pady=6)


        # Stability & filters
        self.s_debounce = tk.StringVar(value=str(dep.get("debounce_seconds", 60)))
        self.s_bundle = tk.StringVar(value=str(dep.get("bundle_window_seconds", 30)))
        self.s_exclude = tk.StringVar(value=",".join(dep.get("exclude_patterns", []) or []))

        ttk.Label(dep_box, text="Debounce / cooldown (seconds)").grid(row=3, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(dep_box, textvariable=self.s_debounce, width=10).grid(row=3, column=1, sticky="w", padx=10, pady=6)

        ttk.Label(dep_box, text="Bundle window (seconds)").grid(row=4, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(dep_box, textvariable=self.s_bundle, width=10).grid(row=4, column=1, sticky="w", padx=10, pady=6)

        ttk.Label(dep_box, text="Exclude patterns (comma-separated)").grid(row=5, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(dep_box, textvariable=self.s_exclude, width=70).grid(row=5, column=1, sticky="w", padx=10, pady=6, columnspan=2)


        disc_box = ttk.LabelFrame(outer, text="Discord (optional)")
        disc_box.pack(fill="x", pady=(0,10))
        disc = self.settings.get("discord", {})

        self.s_discord = tk.StringVar(value=str(disc.get("webhook_url","")))
        self.s_d_found = tk.BooleanVar(value=bool(disc.get("notify_update_found", True)))
        self.s_d_done  = tk.BooleanVar(value=bool(disc.get("notify_upload_done", True)))
        self.s_d_fail  = tk.BooleanVar(value=bool(disc.get("notify_failure", True)))

        ttk.Label(disc_box, text="Discord webhook URL").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        ttk.Entry(disc_box, textvariable=self.s_discord, width=90).grid(row=0, column=1, sticky="w", padx=10, pady=6)

        ttk.Checkbutton(disc_box, text="Notify update detected", variable=self.s_d_found).grid(row=1, column=0, sticky="w", padx=10, pady=2)
        ttk.Checkbutton(disc_box, text="Notify deploy finished", variable=self.s_d_done).grid(row=1, column=1, sticky="w", padx=10, pady=2)
        ttk.Checkbutton(disc_box, text="Notify failures", variable=self.s_d_fail).grid(row=2, column=0, sticky="w", padx=10, pady=2)

        btns = ttk.Frame(outer); btns.pack(fill="x")
        ttk.Button(btns, text="Save Settings", command=self.save_settings_ui, style="Colored.TButton").pack(side="left")

    def browse_workshop(self):
        p = filedialog.askdirectory(title="Select Steam Workshop folder containing @mods")
        if p:
            self.s_workshop.set(p)

    def browse_local_deploy(self):
        p = filedialog.askdirectory(title="Select local deploy destination")
        if p:
            self.s_local_deploy.set(p)

    def save_settings_ui(self):
        try:
            timeout = int((self.s_timeout.get() or "30").strip())
            tick = int((self.s_tick.get() or "60").strip())
            debounce = int((getattr(self, "s_debounce", tk.StringVar(value="60")).get() or "60").strip())
            bundle = int((getattr(self, "s_bundle", tk.StringVar(value="30")).get() or "30").strip())
        except ValueError:
            messagebox.showerror("Invalid", "Timeout / Tick / Debounce / Bundle must be numbers.")
            return

        self.timeout = max(5, timeout)
        self.tick_seconds = max(10, tick)
        self.auto_start = bool(self.s_autostart.get())
        self.workshop_dir = pathlib.Path(self.s_workshop.get()).expanduser()
        self.debounce_seconds = max(0, debounce)
        self.bundle_window_seconds = max(0, bundle)
        # parse exclude patterns
        ex = (getattr(self, "s_exclude", tk.StringVar(value="")).get() or "").strip()
        self.exclude_patterns = [p.strip() for p in ex.split(",") if p.strip()]

        self.settings["app"] = {
            "timeout_seconds": self.timeout,
            "tick_seconds": self.tick_seconds,
            "auto_start": self.auto_start,
            "workshop_dir": str(self.workshop_dir),
        }
        self.settings["deploy"] = {
            "mode": (self.s_mode.get() or "ftp").strip().lower(),
            "remote_mods_base": (self.s_remote_base.get() or "mods").strip() or "mods",
            "local_deploy_dir": (self.s_local_deploy.get() or "").strip(),
            "debounce_seconds": self.debounce_seconds,
            "bundle_window_seconds": self.bundle_window_seconds,
            "exclude_patterns": self.exclude_patterns,
        }
        self.settings["discord"] = {
            "webhook_url": (self.s_discord.get() or "").strip(),
            "notify_update_found": bool(self.s_d_found.get()),
            "notify_upload_done": bool(self.s_d_done.get()),
            "notify_failure": bool(self.s_d_fail.get()),
        }

        save_json(SETTINGS_PATH, self.settings)
        self.log.info("Settings saved.")
        self.refresh_status()
        messagebox.showinfo("Saved", "Settings saved.")

    # Help
    def _build_help(self):
        t = tk.Text(self.tab_help, wrap="word")
        t.pack(fill="both", expand=True, padx=12, pady=12)
        style_text_widget(t)
        t.insert("1.0",
            f"{APP_NAME}\n\n"
            f"Version: {APP_VERSION}\n"
            "Created by Danny van den Brande\n\n"
            "What it does:\n"
            "- Monitors your local Steam Workshop @mod folders for file changes\n"
            "- Detects mod updates automatically (no manual checking needed)\n"
            "- Deploys updated mod folders to keep your server perfectly in sync\n"
            "\n"
            "Deploy methods:\n"
            "- FTP / FTPS: Uploads mods directly to a remote server (recommended for game hosts & VPS)\n"
            "- LOCAL: Copies mods to a local folder (ideal for server parks, sync tools, or custom pipelines)\n"
            "\n"
            "Why this exists:\n"
            "- Prevents players from being locked out due to outdated server mods\n"
            "- Eliminates manual mod uploads after Steam updates\n"
            "- Solves common PBO mismatch and version desync issues\n"
            "\n"
            "Designed for:\n"
            "- DayZ & Arma server owners\n"
            "- Modded game servers\n"
            "- VPS / dedicated servers\n"
            "- Anyone who needs reliable file-based auto deployment\n"
            "\n"
            "How it works:\n"
            "- Creates a baseline fingerprint of each watched mod\n"
            "- Re-checks mods on a fixed interval or manual scan\n"
            "- If changes are detected, the full mod folder is deployed safely\n"
            "- Optional Discord notifications keep you informed\n"
            "\n"
            "Notes:\n"
            "- This tool does NOT restart servers by design\n"
            "- Restart logic differs per host and is handled elsewhere\n"
            "- Fully usable while you are offline or asleep\n"
            "\n"
            "Folder layout explained:\n"
            "\n"
            "AutomationZ does NOT guess your server layout.\n"
            "You define it once, and the tool follows it exactly.\n"
            "\n"
            "The deploy path is built like this:\n"
            "<Profile Root> + <Remote mods base> + <@ModName>\n"
            "\n"
            "Common setups:\n"
            "\n"
            "1) Vanilla DayZ / Nitrado / most hosts\n"
            "   Mods live in:\n"
            "   /dayzstandalone/@ModName\n"
            "\n"
            "   → Profile Root: /dayzstandalone\n"
            "   → Remote mods base: (leave empty)\n"
            "\n"
            "2) Custom mods folder\n"
            "   Mods live in:\n"
            "   /dayzstandalone/mods/@ModName\n"
            "\n"
            "   → Profile Root: /dayzstandalone\n"
            "   → Remote mods base: mods\n"
            "\n"
            "Important:\n"
            "- Leaving Remote mods base empty is intentional and valid\n"
            "- No folders are duplicated\n"
            "- Missing folders are created automatically\n"
            "\n"
            "AutomationZ Server Backup Scheduler is free and open-source software.\n\n"
            "If this tool helps you automate server tasks, save time,\n"
            "or manage multiple servers more easily,\n"
            "consider supporting development with a donation.\n\n"
            "Donations are optional, but appreciated and help\n"
            "support ongoing development and improvements.\n\n"
            "Support link:\n"
            "https://ko-fi.com/dannyvandenbrande \n\n"
            "dannyautomationz@gmail.com\n"
        )
        t.configure(state="disabled")

def main():
    for p in [CONFIG_DIR, STATE_DIR, LOGS_DIR]:
        p.mkdir(parents=True, exist_ok=True)
    App().mainloop()

if __name__ == "__main__":
    main()
