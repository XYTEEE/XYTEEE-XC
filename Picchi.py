#!/usr/bin/env python3
# Picchi.py - bootstrap runner that handles voice startup (download + play) then calls xcmain.email_verification_system()
# Place this in your project root. Set VOICES_GITHUB_RAW_BASE_URL if you use a different repo/branch.
# Skip welcome voice with: XYTEEE_SKIP_WELCOME=1

import os
import sys
import subprocess
import shutil
import time
import traceback
import importlib

DEFAULT_VOICES_BASE = "https://raw.githubusercontent.com/Kawsar-Hosen/XYTEEE/main/voices/"
WANTED_VOICES = ["bn.mp3", "hi.mp3", "ur.mp3", "id.mp3", "ar.mp3", "fa.mp3", "en.mp3"]

def run_cmd(cmd):
    try:
        return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except Exception as e:
        return None

def ensure_package_install(cmd_install):
    """Best-effort install using provided shell command (e.g., 'pkg install -y mpv' or 'pip install playsound')."""
    try:
        rc = run_cmd(cmd_install)
        return rc and rc.returncode == 0
    except Exception:
        return False

def ensure_system_playback():
    """Ensure at least one system playback tool available. Return first available player command or None."""
    candidates = ["mpv", "mpg123", "ffplay", "termux-media-player", "afplay"]
    for c in candidates:
        if shutil.which(c):
            return c
    # Try to install common players on Termux / Debian / Brew (best-effort)
    if 'TERMUX_VERSION' in os.environ:
        ensure_package_install("pkg update -y && pkg install -y mpv ffmpeg mpg123")
    elif shutil.which("apt") or shutil.which("apt-get"):
        apt = shutil.which("apt-get") or shutil.which("apt")
        ensure_package_install(f"{apt} update -y || true")
        ensure_package_install(f"{apt} install -y mpv ffmpeg mpg123 || true")
    elif shutil.which("brew"):
        ensure_package_install("brew install mpv ffmpeg mpg123 || true")
    # re-check
    for c in candidates:
        if shutil.which(c):
            return c
    return None

def ensure_python_playback_libs():
    """Ensure Python playback libs exist (playsound, pydub). Returns list of available modules."""
    avail = []
    try:
        import playsound  # noqa: F401
        avail.append("playsound")
    except Exception:
        pass
    try:
        from pydub import AudioSegment  # noqa: F401
        avail.append("pydub")
    except Exception:
        pass
    if avail:
        return avail
    # try to install
    pip = shutil.which("pip3") or shutil.which("pip")
    if not pip:
        return []
    run_cmd(f"{pip} install playsound pydub simpleaudio >/dev/null 2>&1 || true")
    try:
        import playsound  # noqa: F401
        avail.append("playsound")
    except Exception:
        pass
    try:
        from pydub import AudioSegment  # noqa: F401
        avail.append("pydub")
    except Exception:
        pass
    return avail

def download_file(url, dest_path, timeout=15):
    """Download using requests with optional token. Returns True on success."""
    try:
        import requests
    except Exception:
        # try to install requests quickly
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
        else:
            # non-200
            return False
    except Exception:
        return False

def ensure_voices_from_github_if_needed(voices_dir, filenames):
    base = os.environ.get("VOICES_GITHUB_RAW_BASE_URL", "").strip() or DEFAULT_VOICES_BASE
    if not base.endswith("/"):
        base = base + "/"
    missing = [f for f in filenames if not os.path.isfile(os.path.join(voices_dir, f))]
    if not missing:
        return True
    # attempt downloads
    ok_any = False
    for f in missing:
        url = base + f
        dest = os.path.join(voices_dir, f)
        try:
            os.makedirs(voices_dir, exist_ok=True)
            success = download_file(url, dest)
            if success:
                ok_any = True
            else:
                # ensure no empty file left
                if os.path.exists(dest) and os.path.getsize(dest) == 0:
                    try:
                        os.remove(dest)
                    except Exception:
                        pass
        except Exception:
            pass
    # return True if at least some files present (or none missing)
    present = [f for f in filenames if os.path.isfile(os.path.join(voices_dir, f))]
    return len(present) == len(filenames)

def get_country_from_ip(timeout=7):
    try:
        import requests
        r = requests.get("http://ip-api.com/json/", timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            return data.get("country", "") or ""
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
    return "en.mp3"

def try_play_audio(file_path):
    # Try system players first
    player = ensure_system_playback()
    if player:
        try:
            if player == "termux-media-player":
                run_cmd(f"termux-media-player play '{file_path}'")
                return True
            else:
                # mpv/ffplay/mpg123/afplay
                run_cmd(f"{player} --no-video --really-quiet '{file_path}'")
                return True
        except Exception:
            pass
    # Python fallback
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

def play_welcome_voice(voices_dir):
    if os.environ.get("XYTEEE_SKIP_WELCOME", "").strip() in ("1","true","yes"):
        return False
    country = get_country_from_ip()
    voice_file = country_to_voice_file(country)
    path = os.path.join(voices_dir, voice_file)
    if not os.path.isfile(path):
        # fallback to en.mp3 if exists
        alt = os.path.join(voices_dir, "en.mp3")
        if os.path.isfile(alt):
            path = alt
        else:
            return False
    try:
        try_play_audio(path)
        return True
    except Exception:
        return False

def ensure_runtime_deps():
    # Ensure httpx + requests installed, best-effort
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
        # 1) ensure python deps
        ensure_runtime_deps()

        # 2) ensure voices exist (download from github if needed)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        voices_dir = os.path.join(script_dir, "voices")
        os.makedirs(voices_dir, exist_ok=True)
        ensure_voices_from_github_if_needed(voices_dir, WANTED_VOICES)

        # 3) try play welcome voice (non-blocking best-effort)
        play_welcome_voice(voices_dir)

        # 4) attempt git pull to update code (best-effort)
        try:
            if os.path.isdir(os.path.join(script_dir, ".git")):
                run_cmd("git pull")
        except Exception:
            pass

        # 5) finally call xcmain.email_verification_system()
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
            # print traceback to help debugging then exit with message
            traceback.print_exc()
            sys.exit(str(e))

    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
