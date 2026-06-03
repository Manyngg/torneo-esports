from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB = "data.json"

# =========================
# DB LOAD / SAVE SEGURO
# =========================

def load():
    if not os.path.exists(DB):
        return {"equipos": {}}

    with open(DB, "r", encoding="utf8") as f:
        return json.load(f)


def save(data):
    tmp = DB + ".tmp"
    with open(tmp, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    os.replace(tmp, DB)


# =========================
# SCORE SYSTEM
# =========================

def calcular_score(placement, teamkills):

    if placement == 1:
        mult = 1.6
    elif placement <= 5:
        mult = 1.4
    elif placement <= 10:
        mult = 1.2
    else:
        mult = 1

    return round(teamkills * mult, 2)


# =========================
# REPORT MATCH
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
        db["equipos"][team] = {
            "games": {},
            "players": {}
        }

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

    for i, p in enumerate(players):

        if p not in db["equipos"][team]["players"]:
            db["equipos"][team]["players"][p] = {"kills": 0}

        db["equipos"][team]["players"][p]["kills"] += kills[i]

    save(db)

    return jsonify({"ok": True})


# =========================
# MODIFY MATCH
# =========================

@app.route("/modificar", methods=["POST"])
def modificar():

    body = request.json

    team = body["equipo"]
    game = str(body["game"])

    db = load()

    if team not in db["equipos"]:
        return jsonify({"error": "equipo no existe"}), 400

    if game not in db["equipos"][team]["games"]:
        return jsonify({"error": "partida no existe"}), 400

    old = db["equipos"][team]["games"][game]

    # RESTAR kills antiguas
    for p, k in old["players"].items():
        if p in db["equipos"][team]["players"]:
            db["equipos"][team]["players"][p]["kills"] -= k

    placement = int(body["placement"])
    players = body["jugadores"]
    kills = body["kills"]

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

    for i, p in enumerate(players):

        if p not in db["equipos"][team]["players"]:
            db["equipos"][team]["players"][p] = {"kills": 0}

        db["equipos"][team]["players"][p]["kills"] += kills[i]

    save(db)

    return jsonify({"ok": True})


# =========================
# HOME DASHBOARD
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

    # =========================
    # RANKING TEAMS
    # =========================

    ranking = []

    for team, data in equipos.items():

        score = 0
        kills = 0

        for g, info in data["games"].items():
            score += info["score"]
            kills += info["kills"]

        ranking.append({
            "team": team,
            "score": round(score, 2),
            "kills": kills,
            "games": data["games"]
        })

    ranking.sort(key=lambda x: x["score"], reverse=True)

    # =========================
    # FRAGGER GLOBAL (FIXED)
    # =========================

    fragger = {}

    for team, data in equipos.items():

        for p, k in data["players"].items():

            if p not in fragger:
                fragger[p] = {
                    "team": team,
                    "kills": 0
                }

            fragger[p]["kills"] += k   # ✅ FIX REAL

    fraggers = sorted(
        fragger.items(),
        key=lambda x: x[1]["kills"],
        reverse=True
    )

    # =========================
    # HTML
    # =========================

    colors = ["#00ff66", "#d6ff00", "#00ffaa", "#aaff00", "#66ff00", "#ffe600"]

    html = """
<html>
<head>
<meta http-equiv='refresh' content='30'>
<style>
body{
background:#090909;
color:white;
font-family:Arial;
margin:20px;
}

h1{
color:#d6ff00;
text-shadow:0 0 20px #d6ff00;
}

table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
}

th,td{
padding:8px;
text-align:center;
border:1px solid #222;
}

.team{
color:#00ff66;
font-weight:bold;
}

.players{
font-size:12px;
line-height:1.5;
}
</style>
</head>

<body>

<h1>🏆 Liga CBS</h1>

<table>
<tr>
<th>POS</th>
<th>TEAM</th>
"""

    idx = 0

    for g in allgames:

        color = colors[idx % len(colors)]
        idx += 1

        html += f"""
<th style='background:{color};color:black'>
GAME {g}<br>PLAYERS
</th>
<th style='background:{color};color:black'>POS</th>
<th style='background:{color};color:black'>SCORE</th>
"""

    html += """
<th>TOTAL SCORE</th>
<th>TOTAL KILLS</th>
</tr>
"""

    pos = 1

    for r in ranking:

        medal = ""
        if pos == 1:
            medal = "🥇"
        elif pos == 2:
            medal = "🥈"
        elif pos == 3:
            medal = "🥉"

        html += f"""
<tr>
<td>{medal} {pos}</td>
<td class='team'>{r['team']}</td>
"""

        for g in allgames:

            if g in r["games"]:

                game = r["games"][g]

                players_txt = ""
                for p, k in game["players"].items():
                    players_txt += f"{p}:{k}<br>"

                html += f"""
<td class='players'>{players_txt}</td>
<td>{game['placement']}</td>
<td>{game['score']}</td>
"""
            else:
                html += "<td>-</td><td>-</td><td>-</td>"

        html += f"""
<td>{r['score']}</td>
<td>{r['kills']}</td>
</tr>
"""

        pos += 1

    html += """
</table>

<h2 style='color:#00ff66'>🔥 FRAGGER TABLE</h2>

<table>
<tr>
<th>PLAYER</th>
<th>TEAM</th>
<th>KILLS</th>
</tr>
"""

    for p, s in fraggers:

        html += f"""
<tr>
<td>{p}</td>
<td>{s['team']}</td>
<td>{s['kills']}</td>
</tr>
"""

    html += """
</table>

</body>
</html>
"""

    return html


# =========================
# API PARA BOT DISCORD
# =========================

@app.route("/api/leaderboard")
def api_leaderboard():

    db = load()
    result = []

    for team, data in db["equipos"].items():

        score = 0
        kills = 0

        for g, info in data["games"].items():
            score += info["score"]
            kills += info["kills"]

        result.append({
            "team": team,
            "score": score,
            "kills": kills
        })

    result.sort(key=lambda x: x["score"], reverse=True)

    return jsonify(result)


@app.route("/api/fragger")
def api_fragger():

    db = load()
    fragger = {}

    for team, data in db["equipos"].items():

        for p, k in data["players"].items():

            if p not in fragger:
                fragger[p] = {"team": team, "kills": 0}

            fragger[p]["kills"] += k

    result = sorted(
        fragger.items(),
        key=lambda x: x[1]["kills"],
        reverse=True
    )

    return jsonify(result)


# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
