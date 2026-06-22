#!/usr/bin/env python3
"""
mini_sel.py Simuliert den SEL-Server.
robot_main.py verbindet sich als Client, dieser Script antwortet mit Goals.
"""
import socket, json, threading, time

HOST, PORT = "127.0.0.1", 3004

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)
print(f"Warte auf robot_main.py auf {HOST}:{PORT} ...")

conn, addr = server.accept()
print(f"Roboter verbunden: {addr}")

# Start-Signal (dein receiveMessages wartet darauf)
conn.send(b"start")
print("'start' gesendet. Roboter luft.\n")
# Status-Empfang im Hintergrund (publishMessages sendet hierher)
def receive_status():
    while True:
        try:
            data = conn.recv(4096)
            if data:
                for line in data.decode().splitlines():
                     if line.strip():
                        try:
                            msg = json.loads(line)
                            robot = msg.get("robot", {})
                            x     = robot.get("xPos", "?")
                            y     = robot.get("yPos", "?")
                            theta = robot.get("theta", "?")
                            speed    = robot.get("speed", "?")
                            rotspeed = robot.get("rotationSpeed", "?")
                            print(f"[STATUS] x={x:.3f} y={y:.3f} theta={theta:.3f} speed={speed:.3f} rot={rotspeed:.3f}")
                        except (json.JSONDecodeError, TypeError):
                            pass
        except:
            break

threading.Thread(target=receive_status, daemon=True).start()

# Interaktive Goal-Eingabe
print("Goal eingeben: x y state  (z.B.: 1.5 2.0 driving)")
print("Beenden mit Ctrl+C\n")

while True:
    try:
        raw = input("> ").strip()
        if not raw:
            continue
        parts = raw.split()
        goal = {
            "xTarget": float(parts[0]),
            "yTarget": float(parts[1]),
            "state":   parts[2] if len(parts) > 2 else "driving"
        }
        conn.send((json.dumps(goal) + "\n").encode())
        print(f" gesendet: {goal}")
    except (IndexError, ValueError):
        print("  Format: x y state  (z.B.: 1.5 2.0 driving)")
    except KeyboardInterrupt:
        print("\nBeendet.")
        break

conn.close()
server.close()