from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB = "data.json"

#################################################

def load():
    if not os.path.exists(DB):
        return {"equipos": {}}

    with open(DB, "r", encoding="utf8") as f:
        return json.load(f)

#################################################

def save(data):
    with open(DB, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

#################################################

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

#################################################

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
        db["equipos"][team] = {"games": {}, "players": {}}

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

#################################################

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
        "players": {players[i]: kills[i] for i in range(len(players))}
    }

    for i, p in enumerate(players):
        if p not in db["equipos"][team]["players"]:
            db["equipos"][team]["players"][p] = {"kills": 0}
        db["equipos"][team]["players"][p]["kills"] += kills[i]

    save(db)
    return jsonify({"ok": True})

#################################################

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
            "score": round(score, 2),
            "kills": kills,
            "games": data["games"]
        })

    ranking = sorted(ranking, key=lambda x: x["score"], reverse=True)

    fragger = {}

    for team, data in equipos.items():
        for p, s in data["players"].items():
            if p not in fragger:
                fragger[p] = {"team": team, "kills": 0}
            fragger[p]["kills"] += s["kills"]

    fraggers = sorted(fragger.items(), key=lambda x: x[1]["kills"], reverse=True)

    html = """
<html>
<head>
<meta http-equiv='refresh' content='30'>

<style>

body{
background:#0a0a0a;
color:white;
font-family:Arial;
margin:20px;
}

h1{
color:#00ff66;
text-shadow:0 0 15px #00ff66;
text-align:center;
}

/* STREAM */
.stream-box{
display:flex;
justify-content:center;
margin:15px 0 25px 0;
}

.stream-box iframe{
width:420px;
height:240px;
border-radius:12px;
border:2px solid #00ff66;
box-shadow:0 0 20px rgba(0,255,102,0.4);
}

/* TABLAS */
table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
background:rgba(255,255,255,0.05);
backdrop-filter: blur(8px);
border-radius:15px;
overflow:hidden;
box-shadow:0 10px 25px rgba(0,0,0,0.5);
}

th{
background:rgba(0,255,102,0.2);
color:#00ff66;
padding:10px;
text-transform:uppercase;
}

td{
padding:8px;
text-align:center;
border-bottom:1px solid rgba(255,255,255,0.1);
}

.team{
color:white;
font-weight:bold;
}

h2{
color:#00ff66;
text-shadow:0 0 10px #00ff66;
}

tr:hover{
background:rgba(0,255,102,0.1);
}

</style>

</head>

<body>

<h1>🏆 Liga CBS</h1>

<!-- 🎥 TU STREAM MANYNN -->
<div class="stream-box">
<iframe
    src="https://player.twitch.tv/?channel=Manynn&parent=localhost"
    allowfullscreen>
</iframe>
</div>

<table>

<tr>
<th>POS</th>
<th>TEAM</th>
"""

    game_colors = ["#00ff66","#d6ff00","#00ffaa","#aaff00","#66ff00","#ffe600"]

    idx = 0

    for g in allgames:
        color = game_colors[idx % len(game_colors)]
        idx += 1

        html += f"""
<th style="background:{color};color:black;">GAME {g}</th>
<th style="background:{color};color:black;">POS</th>
<th style="background:{color};color:black;">SCORE</th>
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

                players = ""
                for p, k in game["players"].items():
                    players += f"{p}:{k}<br>"

                html += f"""
<td>{players}</td>
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

<h2>🔥 FRAGGER TABLE</h2>

<table>

<tr>
<th>POS</th>
<th>PLAYER</th>
<th>TEAM</th>
<th>KILLS</th>
</tr>
"""

    pos = 1

    for p, s in fraggers:

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
<td>{p}</td>
<td>{s['team']}</td>
<td>{s['kills']}</td>
</tr>
"""

        pos += 1

    html += """
</table>

</body>
</html>
"""

    return html

#################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
