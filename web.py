from flask import Flask, request, jsonify
import os
import json

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


@app.route("/")
def home():
    return "🏆 WAHOO ONLINE - SERVER OK"


@app.route("/report", methods=["POST"])
def report():
    try:
        body = request.json

        team = body.get("equipo")
        game = str(body.get("game"))
        placement = int(body.get("placement", 0))

        players = body.get("jugadores", [])
        kills = body.get("kills", [])

        if not team:
            return jsonify({"error": "no team"}), 400

        db = load()

        if team not in db["equipos"]:
            db["equipos"][team] = {"games": {}}

        db["equipos"][team]["games"][game] = {
            "placement": placement,
            "kills": sum(kills),
            "players": {
                players[i]: kills[i]
                for i in range(min(len(players), len(kills)))
            }
        }

        save(db)

        return jsonify({"ok": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/modificar", methods=["POST"])
def modificar():
    return jsonify({"ok": True})


@app.route("/borrar", methods=["POST"])
def borrar():
    db = load()
    db["equipos"] = {}
    save(db)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
