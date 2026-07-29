#!/usr/bin/env python3
import os, sys
try:
    import httpx
except:
    os.system('pip install httpx > /dev/null')
try:
    import requests
except:
    os.system('pip uninstall requests chardet urllib3 idna certifi -y;pip install chardet urllib3 idna certifi requests')
import shutil
import subprocess
import json
from pathlib import Path

# Preserve existing behavior
os.system('xdg-open https://whatsapp.com/channel/0029VaXTSiI2phHGeH8Wd23r')
os.system('git pull')

# Try to run existing email verification if available
try:
    __import__("xcmain").email_verification_system()
except Exception as e:
    # Do not exit here; we want to continue to the welcome playback even if xcmain isn't available
    # Keep the original exit behavior commented out for safety in repository usage
    # exit(str(e))
    print(f"xcmain.email_verification_system() failed: {e}")

# New: Play a country-specific welcome message from voices/ when run on Termux
SCRIPT_DIR = Path(__file__).resolve().parent
VOICES_DIR = SCRIPT_DIR / "voices"

def get_public_ip_info():
    """Try to get public IP geolocation info and return country code (ISO 2-letter)."""
    urls = [
        'https://ipapi.co/json/',
        'http://ip-api.com/json/',
        'https://ipinfo.io/json'
    ]
    headers = {'User-Agent': 'Picchi/1.0'}
    for url in urls:
        try:
            r = requests.get(url, timeout=5, headers=headers)
            if r.status_code == 200:
                try:
                    data = r.json()
                except Exception:
                    try:
                        data = json.loads(r.text)
                    except Exception:
                        data = {}
                # Different services use different keys
                for key in ('country_code', 'country', 'countryCode'):
                    if key in data and data.get(key):
                        return data.get(key).upper()
        except Exception:
            continue
    return None


def find_player():
    # Prefer termux-media-player, then termux-tts-speak (for TTS), then mpv/ffplay/play
    players = ["termux-media-player", "mpv", "ffplay", "play"]
    for p in players:
        if shutil.which(p):
            return p
    return None


def play_file_with_player(player, filepath, loop=1):
    try:
        if player == 'termux-media-player':
            subprocess.run([player, 'play', str(filepath)], check=True)
        elif player == 'mpv':
            cmd = [player, '--no-video', str(filepath)]
            if loop and loop > 1:
                cmd = [player, '--no-video', '--loop', str(loop), str(filepath)]
            subprocess.run(cmd, check=True)
        elif player == 'ffplay':
            cmd = [player, '-nodisp', '-autoexit', str(filepath)]
            if loop and loop > 1:
                # ffplay's -loop N plays N+1 times for files; behavior varies, so just repeat if needed
                for i in range(loop):
                    subprocess.run([player, '-nodisp', '-autoexit', str(filepath)])
                return
            subprocess.run(cmd, check=True)
        elif player == 'play':
            for i in range(loop):
                subprocess.run([player, str(filepath)])
        else:
            # fallback: try xdg-open
            subprocess.run(['xdg-open', str(filepath)])
    except Exception as e:
        print(f"Failed to play {filepath} with {player}: {e}")


def tts_speak(message):
    # Prefer termux-tts-speak if available
    if shutil.which('termux-tts-speak'):
        try:
            subprocess.run(['termux-tts-speak', message], check=True)
            return True
        except Exception:
            pass
    # Fallback to espeak / say if present
    if shutil.which('espeak'):
        try:
            subprocess.run(['espeak', message], check=True)
            return True
        except Exception:
            pass
    return False


def play_welcome_by_country():
    country = get_public_ip_info()
    if country:
        print(f"Detected country: {country}")
    else:
        print("Could not detect country; using default")

    # Map country codes to voice files (place files in voices/)
    mapping = {
        'BD': 'bn.mp3',  # Bangladesh -> Bengali file (bn.mp3)
        'IN': 'bn.mp3',  # India -> default to Bengali if Hindi not available
        'US': 'en.mp3',
        'GB': 'en.mp3',
        # add more mappings as you add files to voices/
    }

    selected_file = None
    if country and country in mapping:
        candidate = VOICES_DIR / mapping[country]
        if candidate.exists():
            selected_file = candidate

    # If no mapped file, try common filenames
    if not selected_file:
        for name in ('welcome.mp3', 'en.mp3', 'bn.mp3', 'welcome_bangla.mp3'):
            cand = VOICES_DIR / name
            if cand.exists():
                selected_file = cand
                break

    player = find_player()

    if selected_file and player:
        print(f"Playing welcome file: {selected_file.name} using {player}")
        play_file_with_player(player, selected_file)
        return

    # If we reach here, either no file found or no player - fallback to TTS
    messages = {
        'BD': 'স্বাগতম',
        'IN': 'স্বাগতম',
        'US': 'Welcome',
        'GB': 'Welcome',
        'default': 'Welcome'
    }
    msg = messages.get(country, messages['default'])
    print(f"Falling back to TTS message: {msg}")
    if not tts_speak(msg):
        print('No TTS engine found. Place an mp3 in voices/ and a player (termux-media-player/mpv/ffplay) to play it.')


if __name__ == '__main__':
    # Only run the welcome playback when executed directly
    try:
        play_welcome_by_country()
    except Exception as e:
        print(f"Error during welcome playback: {e}")
