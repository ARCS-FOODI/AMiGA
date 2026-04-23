#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from typing import List, Optional

DEBUG = True  # set False to quiet logs

ADB = os.environ.get("ADB", "adb")
SERIAL = os.environ.get("ANDROID_SERIAL")  # e.g. "192.168.240.42:5555"

def log(msg: str):
    if DEBUG:
        print(f"[DEBUG] {msg}", flush=True)

def run(cmd: List[str], check: bool = True, input_bytes: Optional[bytes] = None):
    """Run a command and return CompletedProcess. Always capture output for debugging."""
    log(f"RUN: {' '.join(cmd)}")
    proc = subprocess.run(
        cmd,
        input=input_bytes,
        capture_output=True,
        text=True if input_bytes is None else False,
        check=False,
    )
    if DEBUG and proc.stdout:
        print(proc.stdout, end="")
    if proc.returncode != 0:
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")
        if check:
            raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stdout, proc.stderr)
    return proc

def adb_cmd(args: List[str], check: bool = True, input_bytes: Optional[bytes] = None):
    cmd = [ADB]
    if SERIAL:
        cmd += ["-s", SERIAL]
    cmd += args
    return run(cmd, check=check, input_bytes=input_bytes)

def adb_shell(*args: str, check: bool = True):
    return adb_cmd(["shell", *args], check=check)

def tap(x: int, y: int):
    adb_shell("input", "tap", str(x), str(y))

def tap_n_fast(x: int, y: int, n: int):
    """
    Fast taps using a portable while-loop pushed over stdin.
    Falls back to chunked taps if the device shell rejects the loop.
    """
    # Portable shell script (mksh/sh compatible on Android):
    # Uses only while + [ test ] + arithmetic $((i+1))
    script = f"""i=0
while [ $i -lt {n} ]; do
  input tap {x} {y}
  i=$((i+1))
done
"""
    try:
        # Feed the script via stdin; sh -s reads from stdin
        adb_cmd(["shell", "sh", "-s"], input_bytes=script.encode("utf-8"))
        log(f"tap_n_fast OK: {n} taps at ({x},{y})")
        return
    except subprocess.CalledProcessError as e:
        log("tap_n_fast fast-path failed; falling back to chunked taps")

    # Fallback: chunk into smaller loops to avoid too many ADB round trips
    # Chunk size can be tuned; 50 is a good balance between speed and safety.
    CHUNK = 50
    remaining = n
    while remaining > 0:
        chunk = min(CHUNK, remaining)
        # Build one-liner with chunk taps to reduce overhead
        # (Avoid shell loops entirely here.)
        one_liner = " ; ".join([f"input tap {x} {y}"] * chunk)
        try:
            adb_shell("sh", "-c", one_liner)
        except subprocess.CalledProcessError:
            # As a last resort, send individual taps for this chunk
            for _ in range(chunk):
                tap(x, y)
        remaining -= chunk
    log(f"tap_n_fast fallback OK: {n} taps at ({x},{y})")

def main():
    # Step 1: input tap 826 636
    tap(826, 636)
    time.sleep(4)

    # Step 2: input tap 826 610
    tap(826, 610)
    time.sleep(5)

    # Power toggle test: press, wait 2s, press
    tap(961, 474)
    time.sleep(3)
    tap(961, 474)
    time.sleep(3)

    # Minus temp test: change by 10.00 (0.01 per tap => 1000 taps)
    # Fast path (stdin shell script); falls back if needed.
    tap_n_fast(1061, 753, 100)
    time.sleep(2)

    # Plus temp test: change by 10.00 (back up by 1000 taps)
    tap_n_fast(1171, 753, 100)
    time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("\n[ERROR] Command failed.", file=sys.stderr)
        print(f"Command: {' '.join(e.cmd) if isinstance(e.cmd, list) else e.cmd}", file=sys.stderr)
        if e.stdout:
            print(f"STDOUT:\n{e.stdout}", file=sys.stderr)
        if e.stderr:
            print(f"STDERR:\n{e.stderr}", file=sys.stderr)
        sys.exit(e.returncode)