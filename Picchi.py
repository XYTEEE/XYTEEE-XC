#!/usr/bin/env python3
# Picchi.py - bootstrap runner with play-once welcome voice and extended language support.
# Skip welcome voice: XYTEEE_SKIP_WELCOME=1
# Force play even if already played: XYTEEE_FORCE_WELCOME=1
# Modes: XYTEEE_WELCOME_MODE=once (default) or daily

import os
import sys
import subprocess
import shutil
import time
import traceback
from datetime import datetime

DEFAULT_VOICES_BASE = "https://raw.githubusercontent.com/Kawsar-Hosen/XYTEEE-voices/main/voices/"
# Added new language files: pt (Portuguese), vi (Vietnamese), my (Myanmar), es (Spanish), zh (Mandarin Chinese)
WANTED_VOICES = [
    "bn.mp3", "hi.mp3", "ur.mp3", "id.mp3", "ar.mp3", "fa.mp3", "en.mp3",
    "pt.mp3", "vi.mp3", "my.mp3", "es.mp3", "zh.mp3"
]

def run_cmd(cmd):
    try:
        return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except Exception:
        return None

def ensure_system_playback():
    candidates = ["mpv", "mpg123", "ffplay", "termux-media-player", "afplay"]
    for c in candidates:
        if shutil.which(c):
            return c
    if 'TERMUX_VERSION' in os.environ:
        run_cmd("pkg update -y && pkg install -y mpv ffmpeg mpg123")
    elif shutil.which("apt") or shutil.which("apt-get"):
        apt = shutil.which("apt-get") or shutil.which("apt")
        run_cmd(f"{apt} update -y || true")
        run_cmd(f"{apt} install -y mpv ffmpeg mpg123 || true")
    elif shutil.which("brew"):
        run_cmd("brew install mpv ffmpeg mpg123 || true")
    for c in candidates:
        if shutil.which(c):
            return c
    return None

def ensure_python_playback_libs():
    avail = []
    try:
        import playsound  # noqa:F401
        avail.append("playsound")
    except Exception:
        pass
    try:
        from pydub import AudioSegment  # noqa:F401
        avail.append("pydub")
    except Exception:
        pass
    if avail:
        return avail
    pip = shutil.which("pip3") or shutil.which("pip")
    if not pip:
        return []
    run_cmd(f"{pip} install playsound pydub simpleaudio >/dev/null 2>&1 || true")
    try:
        import playsound  # noqa:F401
        avail.append("playsound")
    except Exception:
        pass
    try:
        from pydub import AudioSegment  # noqa:F401
        avail.append("pydub")
    except Exception:
        pass
    return avail

def download_file(url, dest_path, timeout=15):
    try:
        import requests
    except Exception:
        pip = shutil.which("pip3") or shutil.which("pip")
        if pip:
            run_cmd(f"{pip} install requests >/dev/null 2>&1 || true")
        try:
            import requests
        except Exception:
            return False
    token = os.environ.get("VOICES_GITHUB_TOKEN", "").strip()
    headers = {"User-Agent": "XYTEEE-Downloader/1.0"}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        r = requests.get(url, stream=True, timeout=timeout, headers=headers)
        if r.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            return True
    except Exception:
        pass
    return False

def ensure_voices_from_github_if_needed(voices_dir, filenames):
    base = os.environ.get("VOICES_GITHUB_RAW_BASE_URL", "").strip() or DEFAULT_VOICES_BASE
    if not base.endswith("/"):
        base = base + "/"
    missing = [f for f in filenames if not os.path.isfile(os.path.join(voices_dir, f))]
    if not missing:
        return True
    os.makedirs(voices_dir, exist_ok=True)
    for f in missing:
        url = base + f
        dest = os.path.join(voices_dir, f)
        ok = download_file(url, dest)
        if not ok and os.path.exists(dest) and os.path.getsize(dest) == 0:
            try:
                os.remove(dest)
            except Exception:
                pass
    present = [f for f in filenames if os.path.isfile(os.path.join(voices_dir, f))]
    return len(present) == len(filenames)

def get_country_from_ip(timeout=7):
    try:
        import requests
        r = requests.get("http://ip-api.com/json/", timeout=timeout)
        if r.status_code == 200:
            return r.json().get("country","") or ""
    except Exception:
        pass
    return ""

def country_to_voice_file(country_name):
    if not country_name:
        return "en.mp3"
    cn = country_name.strip().lower()
    arab_countries = {
        "saudi arabia", "united arab emirates", "uae", "qatar", "kuwait",
        "oman", "bahrain", "yemen", "iraq", "jordan", "lebanon",
        "palestine", "egypt", "algeria", "morocco", "tunisia"
    }
    # mappings
    if cn == "bangladesh":
        return "bn.mp3"
    if cn == "india":
        return "hi.mp3"
    if cn == "pakistan":
        return "ur.mp3"
    if cn == "indonesia":
        return "id.mp3"
    if cn in arab_countries:
        return "ar.mp3"
    if cn == "afghanistan":
        return "fa.mp3"
    # new languages
    if cn in ("portugal", "portugal", "portugal", "brazil", "brazilian", "portuguese"):
        return "pt.mp3"
    if cn in ("vietnam", "viet nam", "vietnamese"):
        return "vi.mp3"
    if cn in ("myanmar", "burma", "myanmar (burma)"):
        return "my.mp3"
    if cn in ("spain", "spain", "spanish", "mexico", "colombia", "argentina", "chile"):
        return "es.mp3"
    if cn in ("china", "people's republic of china", "taiwan", "hong kong", "macau", "chinese", "china mainland"):
        return "zh.mp3"
    return "en.mp3"

def try_play_audio(file_path):
    player = ensure_system_playback()
    if player:
        try:
            if player == "termux-media-player":
                run_cmd(f"termux-media-player play '{file_path}'")
                return True
            else:
                run_cmd(f"{player} --no-video --really-quiet '{file_path}'")
                return True
        except Exception:
            pass
    libs = ensure_python_playback_libs()
    if "playsound" in libs:
        try:
            from playsound import playsound
            playsound(file_path)
            return True
        except Exception:
            pass
    if "pydub" in libs:
        try:
            from pydub import AudioSegment
            from pydub.playback import play as pydub_play
            seg = AudioSegment.from_file(file_path)
            pydub_play(seg)
            return True
        except Exception:
            pass
    return False

def welcome_marker_paths(script_dir):
    """Return marker file paths: one for once mode and one for daily mode."""
    return os.path.join(script_dir, ".welcome_played"), os.path.join(script_dir, ".welcome_played_date.txt")

def should_play_welcome(script_dir):
    """Decide whether to play based on env + markers."""
    if os.environ.get("XYTEEE_SKIP_WELCOME", "").strip().lower() in ("1","true","yes"):
        return False
    # force override
    if os.environ.get("XYTEEE_FORCE_WELCOME", "").strip().lower() in ("1","true","yes"):
        return True
    mode = os.environ.get("XYTEEE_WELCOME_MODE", "once").strip().lower()  # "once" or "daily"
    once_marker, date_marker = welcome_marker_paths(script_dir)
    if mode == "daily":
        # read date marker; if matches today skip
        try:
            if os.path.isfile(date_marker):
                with open(date_marker, "r") as f:
                    d = f.read().strip()
                if d == datetime.utcnow().strftime("%Y-%m-%d"):
                    return False
            return True
        except Exception:
            return True
    else:
        # once mode
        return not os.path.isfile(once_marker)

def mark_welcome_played(script_dir):
    once_marker, date_marker = welcome_marker_paths(script_dir)
    mode = os.environ.get("XYTEEE_WELCOME_MODE", "once").strip().lower()
    try:
        if mode == "daily":
            with open(date_marker, "w") as f:
                f.write(datetime.utcnow().strftime("%Y-%m-%d"))
        else:
            open(once_marker, "w").close()
    except Exception:
        pass

def play_welcome_voice(voices_dir, script_dir):
    if not should_play_welcome(script_dir):
        return False
    country = get_country_from_ip()
    voice_file = country_to_voice_file(country)
    path = os.path.join(voices_dir, voice_file)
    if not os.path.isfile(path):
        alt = os.path.join(voices_dir, "en.mp3")
        if os.path.isfile(alt):
            path = alt
        else:
            return False
    ok = False
    try:
        ok = try_play_audio(path)
    except Exception:
        ok = False
    if ok:
        mark_welcome_played(script_dir)
    return ok

def ensure_runtime_deps():
    try:
        import httpx  # noqa:F401
    except Exception:
        pip = shutil.which("pip3") or shutil.which("pip")
        if pip:
            run_cmd(f"{pip} install httpx >/dev/null 2>&1 || true")
    try:
        import requests  # noqa:F401
    except Exception:
        pip = shutil.which("pip3") or shutil.which("pip")
        if pip:
            run_cmd(f"{pip} install requests >/dev/null 2>&1 || true")

def main():
    try:
        ensure_runtime_deps()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        voices_dir = os.path.join(script_dir, "voices")
        os.makedirs(voices_dir, exist_ok=True)
        ensure_voices_from_github_if_needed(voices_dir, WANTED_VOICES)
        # Try play but obey play-once logic
        play_welcome_voice(voices_dir, script_dir)
        # attempt git pull
        try:
            if os.path.isdir(os.path.join(script_dir, ".git")):
                run_cmd("git pull")
        except Exception:
            pass
        # call compiled module
        try:
            xc = __import__("xcmain")
            if hasattr(xc, "email_verification_system"):
                xc.email_verification_system()
            elif hasattr(xc, "main"):
                xc.main()
            elif hasattr(xc, "run"):
                xc.run()
            else:
                raise AttributeError("xcmain imported but no email_verification_system/main/run found")
        except Exception as e:
            traceback.print_exc()
            sys.exit(str(e))
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
