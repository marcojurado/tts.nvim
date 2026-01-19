#!/usr/bin/env python3
import asyncio
import concurrent.futures
import os
import signal
import subprocess
import sys
import shlex

import common
import edge_tts

voice = sys.argv[1]
rate = int((float(sys.argv[2]) - 1) * 100)
nvim_data_dir = sys.argv[3]

# Remaining optional args (order from Lua):
# 4: to_file (optional)
# 5: edge.command (optional)
# 6: player.command (optional)
to_file = None
edge_command = None
player_command = None
remaining = sys.argv[4:]
if len(remaining) == 1:
    if remaining[0].endswith((".wav", ".mp3")) or os.path.sep in remaining[0]:
        to_file = remaining[0]
    else:
        edge_command = remaining[0]
elif len(remaining) == 2:
    if remaining[0].endswith((".wav", ".mp3")) or os.path.sep in remaining[0]:
        to_file = remaining[0]
        edge_command = remaining[1]
    else:
        edge_command = remaining[0]
        player_command = remaining[1]
elif len(remaining) >= 3:
    to_file = remaining[0]
    edge_command = remaining[1]
    player_command = remaining[2]

pid_file = os.path.join(nvim_data_dir, "pid.txt")


async def stream_audio(text):
    communicate = edge_tts.Communicate(text, voice, rate="+" + str(rate) + "%")

    common.kill_existing_process(pid_file)

    # Build player command (player_command overrides base player executable)
    if player_command:
        try:
            player_cmd = shlex.split(player_command) + ["-i", "-", "-autoexit"]
        except Exception:
            player_cmd = [player_command, "-i", "-", "-autoexit"]
    else:
        player_cmd = ["ffplay", "-i", "-", "-autoexit"]

    ffplay = subprocess.Popen(
        player_cmd,
        stdin=subprocess.PIPE,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    thispid = os.getpid()
    common.write_pids_to_file(pid_file, thispid, ffplay.pid)

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            try:
                ffplay.stdin.write(chunk["data"])
                ffplay.stdin.flush()
            except BrokenPipeError:
                break
            except Exception as e:
                print(f"Another error occurred: {e}", file=sys.stderr)
        elif chunk["type"] == "WordBoundary":
            pass

    ffplay.stdin.close()


async def save_to_file(text):
    communicate = edge_tts.Communicate(text, voice, rate="+" + str(rate) + "%")
    await communicate.save(to_file)


def listen_to_stdin():
    EOF = "\x1a"
    text = ""
    ex = concurrent.futures.ThreadPoolExecutor()
    while True:
        character = sys.stdin.read(1)
        if character == EOF:
            send_to_file = text[-1] == "F"
            text = text[:-1]
            if send_to_file:
                asyncio.run(save_to_file(text))
            else:
                ex.submit(asyncio.run, stream_audio(text))
            text = ""
        text += character


common.SigTermHandler(pid_file)
listen_to_stdin()
