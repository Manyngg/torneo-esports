from flask import Flask, request, jsonify
import json
import os
import re

app = Flask(__name__)

DB = "data.json"

# =========================
# DB
# =========================

def load():
    if not os.path.exists(DB):
        return {"equipos": {}}

    with open(DB, "r", encoding="utf8") as f:
        return json.load(f)

def save(data):
    with open(DB, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# =========================
# SCORE
# =========================

def calcular_score(placement, kills):
    if placement == 1:
        mult = 1.6
    elif placement <= 5:
        mult = 1.4
    elif placement <= 10:
        mult = 1.2
    else:
        mult = 1
    return round(kills * mult, 2)

# =========================
# PARSER
# =========================

def parse_text(text):
    lines = text.strip().split("\n")

    header = lines[0].strip()

    # 🔥 FIX IMPORTANTE: game = número de reporte
    game_match = re.findall(r'\d+', header)
    game = str(game_match[0]) if game_match else "1"

    equipo = ""
    placement = 0
    players = []
    kills = []

    for line in lines[1:]:
        line = line.strip()

        if line.startswith("Equipo:"):
            equipo = line.split(":")[1].strip()

        elif line.startswith("Posicion:"):
            placement = int(line.split(":")[1].strip())

        elif ":" in line:
            p, k = line.split(":")
            players.append(p.strip())
            kills.append(int(k.strip()))

    return game, equipo, placement, players, kills

# =========================
# REPORT
# =========================

@app.route("/report", methods=["POST"])
def report():
    text = request.json["text"]

    game, team, placement, players, kills = parse_text(text)

    db = load()

    if team not in db["equipos"]:
        db["equipos"][team] = {"games": {}, "players": {}}

    # ⚠️ IMPORTANTE: cada reporte1,2,3 es único
    if game in db["equipos"][team]["games"]:
        return jsonify({"error": "game repetida"}), 400

    teamkills = sum(kills)
    score = calcular_score(placement, teamkills)

    db["equipos"][team]["games"][game] = {
        "placement": placement,
        "kills": teamkills,
        "score": score,
        "players": {players[i]: kills[i] for i in range(len(players))}
    }

    for i, p in enumerate(players):
        if p not in db["equipos"][team]["players"]:
            db["equipos"][team]["players"][p] = {"kills": 0}
        db["equipos"][team]["players"][p]["kills"] += kills[i]

    save(db)
    return jsonify({"ok": True})

# =========================
# MODIFICAR
# =========================

@app.route("/modificar", methods=["POST"])
def modificar():
    text = request.json["text"]

    game, team, placement, players, kills = parse_text(text)

    db = load()

    if team not in db["equipos"]:
        return jsonify({"error": "equipo no existe"}), 400

    if game not in db["equipos"][team]["games"]:
        return jsonify({"error": "game no existe"}), 400

    old = db["equipos"][team]["games"][game]

    # revertir kills
    for p, k in old["players"].items():
        if p in db["equipos"][team]["players"]:
            db["equipos"][team]["players"][p]["kills"] -= k

    teamkills = sum(kills)
    score = calcular_score(placement, teamkills)

    db["equipos"][team]["games"][game] = {
        "placement": placement,
        "kills": teamkills,
        "score": score,
        "players": {players[i]: kills[i] for i in range(len(players))}
    }

    for i, p in enumerate(players):
        if p not in db["equipos"][team]["players"]:
            db["equipos"][team]["players"][p] = {"kills": 0}
        db["equipos"][team]["players"][p]["kills"] += kills[i]

    save(db)
    return jsonify({"ok": True})

# =========================
# BORRAR
# =========================

@app.route("/borrar", methods=["POST"])
def borrar():
    text = request.json["text"]

    lines = text.strip().split("\n")
    header = lines[0]

    game_match = re.findall(r'\d+', header)
    game = str(game_match[0]) if game_match else None

    equipo = ""

    for line in lines:
        if "Equipo:" in line:
            equipo = line.split(":")[1].strip()

    db = load()

    if equipo not in db["equipos"]:
        return jsonify({"error": "equipo no existe"}), 400

    if game not in db["equipos"][equipo]["games"]:
        return jsonify({"error": "game no existe"}), 400

    old = db["equipos"][equipo]["games"][game]

    for p, k in old["players"].items():
        if p in db["equipos"][equipo]["players"]:
            db["equipos"][equipo]["players"][p]["kills"] -= k

    del db["equipos"][equipo]["games"][game]

    save(db)
    return jsonify({"ok": True})

# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
