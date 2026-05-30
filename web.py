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
# REPORT
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
# WEB (TU TABLA ORIGINAL RESTAURADA)
# =========================
@app.route("/")
def home():
    db = load()
    equipos = db["equipos"]

    allgames = set()

    for team, data in equipos.items():
        for g in data["games"]:
            allgames.add(g)

    allgames = sorted(list(allgames))

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
            "kills": total_kills,
            "games": data["games"]
        })

    ranking = sorted(ranking, key=lambda x: x["score"], reverse=True)

    html = """
<html>
<head>
<style>
body{
background:#111;
color:white;
font-family:Arial;
margin:20px;
}

table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
}

th{
background:#3247ff;
padding:8px;
border:1px solid #555;
}

td{
border:1px solid #444;
padding:6px;
text-align:center;
}

.teamtitle{
background:#222;
font-weight:bold;
}

.score{
background:#2d2d2d;
font-weight:bold;
}
</style>
</head>
<body>

<h1>🏆 MANYN ESPORTS</h1>

<table>
<tr>
<th rowspan='2'>TEAM</th>
"""

    # headers games
    for g in allgames:
        html += f"<th colspan='4'>GAME {g}</th>"

    html += """
<th rowspan='2'>TOTAL SCORE</th>
<th rowspan='2'>TOTAL KILLS</th>
</tr>
<tr>
"""

    for g in allgames:
        html += """
<th>KILLS</th>
<th>PLACEMENT</th>
<th>TEAM KILLS</th>
<th>SCORE</th>
"""

    html += "</tr>"

    # teams
    for r in ranking:

        html += f"<tr><td class='teamtitle'>{r['team']}</td>"

        for g in allgames:

            if g in r["games"]:
                game = r["games"][g]

                html += f"""
<td>{game['kills']}</td>
<td>{game['placement']}</td>
<td>{game['kills']}</td>
<td class='score'>{game['score']}</td>
"""
            else:
                html += "<td>-</td><td>-</td><td>-</td><td>-</td>"

        html += f"""
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
