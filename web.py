from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB = "data.json"


# =========================
# DB SAFE
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
# TEST ROOT (IMPORTANTE)
# =========================

@app.route("/")
def home():
    return "🏆 WAHOO ONLINE OK"


# =========================
# REPORT (ESTE ES EL CLAVE)
# =========================

@app.route("/report", methods=["POST"])
def report():

    try:
        body = request.json

        team = str(body.get("equipo", "")).strip()
        game = str(body.get("game", "")).strip()
        placement = int(body.get("placement", 0))

        players = body.get("jugadores", [])
        kills = body.get("kills", [])

        if len(players) != len(kills):
            return jsonify({"error": "mismatch players/kills"}), 400

        db = load()

        if team not in db["equipos"]:
            db["equipos"][team] = {"games": {}}

        db["equipos"][team]["games"][game] = {
            "placement": placement,
            "kills": sum(kills),
            "players": {
                players[i]: int(kills[i])
                for i in range(len(players))
            }
        }

        save(db)

        return jsonify({"ok": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# MODIFY
# =========================

@app.route("/modificar", methods=["POST"])
def modificar():
    return jsonify({"ok": True})


# =========================
# RESET
# =========================

@app.route("/borrar", methods=["POST"])
def borrar():
    db = load()
    db["equipos"] = {}
    save(db)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
