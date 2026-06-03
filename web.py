from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB = "data.json"


def load():
    if not os.path.exists(DB):
        return {"equipos": {}}
    with open(DB, "r", encoding="utf8") as f:
        return json.load(f)


def save(data):
    with open(DB, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


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
# REPORT (ARREGLADO)
# =========================

@app.route("/report", methods=["POST"])
def report():

    try:
        body = request.json

        team = str(body["equipo"]).strip()
        game = str(body["game"]).strip()
        placement = int(body["placement"])

        players = body["jugadores"]
        kills = body["kills"]

        # 🔥 FIX: asegurar int
        kills = [int(k) for k in kills]

        if len(players) != len(kills):
            return jsonify({"error": "players/kills mismatch"}), 400

        db = load()

        if team not in db["equipos"]:
            db["equipos"][team] = {"games": {}}

        db["equipos"][team]["games"][game] = {
            "placement": placement,
            "kills": sum(kills),
            "score": calcular_score(placement, sum(kills)),
            "players": {
                players[i].strip(): kills[i]
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

    try:
        body = request.json

        team = str(body["equipo"]).strip()
        game = str(body["game"]).strip()
        placement = int(body["placement"])

        players = body["jugadores"]
        kills = [int(k) for k in body["kills"]]

        db = load()

        db["equipos"][team]["games"][game] = {
            "placement": placement,
            "kills": sum(kills),
            "score": calcular_score(placement, sum(kills)),
            "players": {
                players[i].strip(): kills[i]
                for i in range(len(players))
            }
        }

        save(db)

        return jsonify({"ok": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
