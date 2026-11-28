#!/usr/bin/env python3
"""Exercise 03: Minimal Hackathon Output Receiver (UDP JSON from 02_basic_bci.py).

Copy and adapt these 35 lines to trigger:
  - Browser visuals (via WebSockets / Three.js / p5.js)
  - Game engines (Unity / Godot / Unreal UDP socket)
  - Audio synths (Sonic Pi / SuperCollider / Ableton OSC)
  - Hardware actuators (Arduino / ESP32 serial port)
"""

from __future__ import annotations

import argparse
import json
import socket


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5005, help="UDP port matching 02_basic_bci.py --udp-port")
    parser.add_argument("--max-packets", type=int, default=0, help="Exit after N packets (0 = run forever)")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", args.port))
    print(f"[Hackathon Receiver] Listening on udp://127.0.0.1:{args.port} ... (Ctrl+C to stop)")

    seen = 0
    try:
        while True:
            raw, _ = sock.recvfrom(4096)
            msg = json.loads(raw.decode("utf-8"))
            p1 = float(msg["prob_class1"])
            cls = int(msg["class"])
            action = "TRIGGER_ACTION()" if cls == 1 and p1 >= 0.70 else "idle"
            print(f"  class={cls}  prob={p1:.2f}  clf={msg.get('clf')}  -> {action}")
            seen += 1
            if args.max_packets > 0 and seen >= args.max_packets:
                break
    except KeyboardInterrupt:
        print("\n[Hackathon Receiver] Closed.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
