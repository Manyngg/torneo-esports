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


# =========================
# REPORTES
# =========================
@app.route("/report", methods=["POST"])
def report():
    try:
        body = request.json

        team = body["equipo"]
        game = str(body["game"])
        placement = int(body["placement"])
        players = body["jugadores"]
        kills = body["kills"]

        db = load()

        if team not in db["equipos"]:
            db["equipos"][team] = {"games": {}, "players": {}}

        if game in db["equipos"][team]["games"]:
            return jsonify({"error": "game repetida"}), 400

        teamkills = sum(kills)
        score = (25 - placement) + teamkills

        db["equipos"][team]["games"][game] = {
            "placement": placement,
            "kills": teamkills,
            "score": score
        }

        for i, p in enumerate(players):
            if p not in db["equipos"][team]["players"]:
                db["equipos"][team]["players"][p] = {"kills": 0}

            db["equipos"][team]["players"][p]["kills"] += kills[i]

        save(db)

        return jsonify({"ok": True})

    except Exception as e:
        print("ERROR REPORT:", e)
        return jsonify({"error": str(e)}), 500


# =========================
# CORRECCIÓN
# =========================
@app.route("/corregir", methods=["POST"])
def corregir():
    try:
        body = request.json

        team = body["equipo"]
        game = str(body["game"])
        placement = int(body["placement"])
        players = body["jugadores"]
        kills = body["kills"]

        db = load()

        if team not in db["equipos"]:
            return jsonify({"error": "equipo no existe"}), 400

        # borrar partida anterior
        if game in db["equipos"][team]["games"]:
            del db["equipos"][team]["games"][game]

        teamkills = sum(kills)
        score = (25 - placement) + teamkills

        db["equipos"][team]["games"][game] = {
            "placement": placement,
            "kills": teamkills,
            "score": score
        }

        for i, p in enumerate(players):
            if p not in db["equipos"][team]["players"]:
                db["equipos"][team]["players"][p] = {"kills": 0}

            db["equipos"][team]["players"][p]["kills"] += kills[i]

        save(db)

        return jsonify({"ok": True})

    except Exception as e:
        print("ERROR CORREGIR:", e)
        return jsonify({"error": str(e)}), 500


# =========================
# WEB
# =========================
@app.route("/")
def home():
    db = load()
    equipos = db["equipos"]

    ranking = []

    for team, data in equipos.items():

        total_score = 0
        total_kills = 0

        for g, info in data["games"].items():
            total_score += info["score"]
            total_kills += info["kills"]

        ranking.append({
            "team": team,
            "score": total_score,
            "kills": total_kills
        })

    ranking = sorted(ranking, key=lambda x: x["score"], reverse=True)

    html = """
    <html>
    <head>
    <style>
    body { background:#111; color:white; font-family:Arial; }
    table { width:80%; margin:auto; border-collapse:collapse; }
    th,td { border:1px solid #444; padding:10px; text-align:center; }
    th { background:#3247ff; }
    </style>
    </head>
    <body>
    <h1 style="text-align:center;">🏆 TORNEO ESPORTS</h1>

    <table>
    <tr>
    <th>TEAM</th>
    <th>SCORE</th>
    <th>KILLS</th>
    </tr>
    """

    for r in ranking:
        html += f"""
        <tr>
        <td>{r['team']}</td>
        <td>{r['score']}</td>
        <td>{r['kills']}</td>
        </tr>
        """

    html += """
    </table>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
