"""
watch_logs.py  —  Tail app.log, crash.log, and media_debug.log in real time.
Run:  python watch_logs.py
Press Ctrl+C to stop.
"""
import os
import sys
import time
from datetime import datetime

LOGS = {
    "app.log":         ("DIM",     ""),
    "crash.log":       ("RED",     "🔴 CRASH"),
    "media_debug.log": ("YELLOW",  ""),
}

ANSI = {
    "RED":    "\033[91m",
    "YELLOW": "\033[93m",
    "DIM":    "\033[90m",
    "RESET":  "\033[0m",
    "BOLD":   "\033[1m",
}

def tail(handles):
    """Read new lines from all open file handles, return list of (tag, colour, line)."""
    out = []
    for name, (colour, tag), fh in handles:
        while True:
            line = fh.readline()
            if not line:
                break
            out.append((name, colour, tag, line.rstrip()))
    return out

def open_handles():
    handles = []
    for name, (colour, tag) in LOGS.items():
        path = os.path.join(os.path.dirname(__file__), name)
        try:
            fh = open(path, "r", encoding="utf-8", errors="replace")
            fh.seek(0, 2)          # seek to end — only show NEW lines
            handles.append((name, (colour, tag), fh))
            print(f"  watching {name}")
        except FileNotFoundError:
            print(f"  {name} not found yet — will appear once the app writes it")
    return handles

def main():
    print(f"\n{ANSI['BOLD']}Widget log watcher  —  {datetime.now():%Y-%m-%d %H:%M:%S}{ANSI['RESET']}")
    print("─" * 60)
    handles = open_handles()
    print("─" * 60)
    print("Watching … (Ctrl+C to stop)\n")

    try:
        while True:
            # Re-open any log that appeared since we started
            watching = {n for n, _, _ in handles}
            for name, (colour, tag) in LOGS.items():
                if name not in watching:
                    path = os.path.join(os.path.dirname(__file__), name)
                    if os.path.exists(path):
                        fh = open(path, "r", encoding="utf-8", errors="replace")
                        fh.seek(0, 2)
                        handles.append((name, (colour, tag), fh))
                        print(f"  [watcher] now watching {name}")

            lines = tail(handles)
            for name, colour, tag, line in lines:
                prefix = f"{ANSI[colour]}[{name}]{ANSI['RESET']} "
                if tag:
                    prefix += f"{ANSI['BOLD']}{ANSI[colour]}{tag} {ANSI['RESET']}"
                # Highlight errors/warnings regardless of file
                lo = line.lower()
                if any(k in lo for k in ("error", "exception", "traceback", "critical", "crash")):
                    print(f"{ANSI['RED']}{prefix}{line}{ANSI['RESET']}")
                elif "warning" in lo:
                    print(f"{ANSI['YELLOW']}{prefix}{line}{ANSI['RESET']}")
                else:
                    print(f"{prefix}{line}")
                sys.stdout.flush()

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        for _, _, fh in handles:
            fh.close()

if __name__ == "__main__":
    main()
