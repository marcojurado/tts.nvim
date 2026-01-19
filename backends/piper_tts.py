#!/usr/bin/env python3
import concurrent.futures
import os
import subprocess
import sys
import wave
import shlex

import common
import piper

# Required args
model = sys.argv[1]
speed = float(sys.argv[2])
nvim_data_dir = sys.argv[3]

# Remaining optional args (order from Lua):
# 4: to_file (optional)
# 5: piper.command (optional)
# 6: player.command (optional)
to_file = None
base_command = None
player_command = None
remaining = sys.argv[4:]
if len(remaining) == 1:
    # Could be either to_file or base_command
    if remaining[0].endswith((".wav", ".mp3")) or os.path.sep in remaining[0]:
        to_file = remaining[0]
    else:
        base_command = remaining[0]
elif len(remaining) == 2:
    # If first looks like a file, then treat it as to_file
    if remaining[0].endswith((".wav", ".mp3")) or os.path.sep in remaining[0]:
        to_file = remaining[0]
        base_command = remaining[1]
    else:
        base_command = remaining[0]
        player_command = remaining[1]
elif len(remaining) >= 3:
    to_file = remaining[0]
    base_command = remaining[1]
    player_command = remaining[2]

pid_file = os.path.join(nvim_data_dir, "pid.txt")

voices_dir = os.path.join(nvim_data_dir, "piper_voices")
os.makedirs(voices_dir, exist_ok=True)


def stream_audio(text, send_to_file=False):
    common.kill_existing_process(pid_file)

    # Adjust speed for piper (piper uses --length-scale, where values < 1.0 = faster, > 1.0 = slower)
    # Convert speed (where 1.0 = normal, 2.0 = 2x faster) to length_scale
    length_scale = 1.0 / speed if speed > 0 else 1.0
    syn_config = piper.SynthesisConfig(length_scale=length_scale, normalize_audio=True)
    model_path = os.path.join(voices_dir, model + ".onnx")
    voice = piper.PiperVoice.load(model_path=model_path)

    if send_to_file:
        with wave.open(to_file, "wb") as wav_file:
            voice.synthesize_wav(text=text, wav_file=wav_file, syn_config=syn_config)
    else:
        iterable = voice.synthesize(text, syn_config=syn_config)

        # Build player command
        if player_command:
            player_cmd = shlex.split(player_command) + [
                "-f",
                "s16le",
                "-ar",
                "22050",
                "-i",
                "-",
                "-autoexit",
            ]
        else:
            player_cmd = [
                "ffplay",
                "-f",
                "s16le",
                "-ar",
                "22050",
                "-i",
                "-",
                "-autoexit",
            ]

        ffplay_proc = subprocess.Popen(
            player_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        thispid = os.getpid()
        common.write_pids_to_file(pid_file, thispid, ffplay_proc.pid)

        for chunk in iterable:
            ffplay_proc.stdin.write(chunk.audio_int16_bytes)
            ffplay_proc.stdin.flush()

        ffplay_proc.stdin.close()


def download_voice_if_needed():
    if not os.path.exists(os.path.join(voices_dir, model + ".onnx")):
        print(f"Downloading voice model '{model}'...", file=sys.stderr)
        if base_command:
            try:
                cmd = shlex.split(base_command) + ["--download-dir", voices_dir, model]
            except Exception:
                cmd = [base_command, "--download-dir", voices_dir, model]
        else:
            cmd = [
                "python3",
                "-m",
                "piper.download_voices",
                "--download-dir",
                voices_dir,
                model,
            ]
        voice_download = subprocess.run(cmd)
        if voice_download.returncode != 0:
            print(f"Warning: downloading voice model failed (returncode={voice_download.returncode})", file=sys.stderr)


def listen_to_stdin():
    EOF = "\x1a"
    text = ""
    ex = concurrent.futures.ThreadPoolExecutor()
    while True:
        character = sys.stdin.read(1)
        if character == EOF:
            send_to_file = text[-1] == "F"
            text = text[:-1]
            ex.submit(stream_audio, text, send_to_file)
            text = ""
        text += character


common.SigTermHandler(pid_file)
download_voice_if_needed()
listen_to_stdin()
