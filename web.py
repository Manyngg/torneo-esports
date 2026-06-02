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
# REPORT
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
# MODIFICAR
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
# WEB
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

/* 🎮 TABLA WARZONE STYLE */
table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;

/* fondo blanco */
background:white;

/* imagen tipo Warzone */
background-image:url("https://images.unsplash.com/photo-1605902711622-cfb43c4437d1");
background-size:cover;
background-position:center;
background-repeat:no-repeat;
}

th,td{
padding:8px;
text-align:center;
border:1px solid #ddd;
color:black;

/* fondo semi transparente para leer bien */
background:rgba(255,255,255,0.85);
}

.team{
color:#00aa44;
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

    for g in allgames:
        html += f"""
<th>GAME {g}</th>
<th>POS</th>
<th>SCORE</th>
"""

    html += """
<th>TOTAL SCORE</th>
<th>TOTAL KILLS</th>
</tr>
"""

    pos = 1

    for r in ranking:

        html += f"""
<tr>
<td>{pos}</td>
<td class='team'>{r['team']}</td>
"""

        for g in allgames:
            if g in r["games"]:
                game = r["games"][g]

                players = ""
                for p, k in game["players"].items():
                    players += f"{p}:{k}<br>"

                html += f"""
<td class='players'>{players}</td>
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

</body>
</html>
"""

    return html

#################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
