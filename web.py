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
        try:
            return json.load(f)
        except:
            return {"equipos": {}}


def save(data):
    tmp = DB + ".tmp"

    with open(tmp, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    os.replace(tmp, DB)


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
# REPORT
# =========================

@app.route("/report", methods=["POST"])
def report():

    body = request.json

    team = body["equipo"]
    game = str(body["game"])
    placement = int(body["placement"])
    players = body["jugadores"]
    kills = body["kills"]

    db = load()

    if team not in db["equipos"]:
        db["equipos"][team] = {"games": {}}

    if game in db["equipos"][team]["games"]:
        return jsonify({"error": "game repetida"}), 400

    teamkills = sum(kills)
    score = calcular_score(placement, teamkills)

    db["equipos"][team]["games"][game] = {
        "placement": placement,
        "kills": teamkills,
        "score": score,
        "players": {
            players[i]: kills[i] for i in range(len(players))
        }
    }

    save(db)

    return jsonify({"ok": True})


# =========================
# MODIFY (REEMPLAZO TOTAL, NO SUMA)
# =========================

@app.route("/modificar", methods=["POST"])
def modificar():

    body = request.json

    team = body["equipo"]
    game = str(body["game"])
    placement = int(body["placement"])
    players = body["jugadores"]
    kills = body["kills"]

    db = load()

    if team not in db["equipos"]:
        return jsonify({"error": "equipo no existe"}), 400

    if game not in db["equipos"][team]["games"]:
        return jsonify({"error": "partida no existe"}), 400

    teamkills = sum(kills)
    score = calcular_score(placement, teamkills)

    # 🔥 SOLO REEMPLAZA TODO (NO SUMA NI RESTA)
    db["equipos"][team]["games"][game] = {
        "placement": placement,
        "kills": teamkills,
        "score": score,
        "players": {
            players[i]: kills[i] for i in range(len(players))
        }
    }

    save(db)

    return jsonify({"ok": True})


# =========================
# HOME (FRAGGER CORREGIDO)
# =========================

@app.route("/")
def home():

    db = load()
    equipos = db["equipos"]

    allgames = set()

    for t, d in equipos.items():
        for g in d["games"]:
            allgames.add(g)

    allgames = sorted(list(allgames))

    ranking = []

    for team, data in equipos.items():

        score = 0
        kills = 0

        for g, info in data["games"].items():
            score += info["score"]
            kills += info["kills"]

        ranking.append({
            "team": team,
            "score": score,
            "kills": kills,
            "games": data["games"]
        })

    ranking.sort(key=lambda x: x["score"], reverse=True)

    # =========================
    # 🔥 FRAGGER CORRECTO (SIN DUPLICAR NUNCA)
    # =========================

    fragger = {}

    for team, data in equipos.items():

        for g, info in data["games"].items():

            for p, k in info["players"].items():

                fragger[p] = fragger.get(p, {"team": team, "kills": 0})
                fragger[p]["kills"] += k

    fraggers = sorted(
        fragger.items(),
        key=lambda x: x[1]["kills"],
        reverse=True
    )

    # =========================
    # HTML SIMPLE (NO TOCAR LÓGICA)
    # =========================

    html = "<h1>LIGA CBS OK</h1>"

    html += "<h2>FRAGGER</h2>"

    for p, s in fraggers:
        html += f"{p} ({s['team']}) - {s['kills']}<br>"

    return html


# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
