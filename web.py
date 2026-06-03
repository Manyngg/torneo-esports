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
        "players": {players[i]: kills[i] for i in range(len(players))}
    }

    save(db)

    return jsonify({"ok": True})


# =========================
# MODIFY (REEMPLAZO TOTAL)
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

    db["equipos"][team]["games"][game] = {
        "placement": placement,
        "kills": teamkills,
        "score": score,
        "players": {players[i]: kills[i] for i in range(len(players))}
    }

    save(db)

    return jsonify({"ok": True})


# =========================
# HOME (UI RESTAURADA + 3D)
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
    # RANKING
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
    # FRAGGER (FIX FINAL)
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
    # HTML (TU ESTILO RESTAURADO)
    # =========================

    html = """
<html>
<head>
<meta http-equiv='refresh' content='30'>

<style>

body{
background: radial-gradient(circle at top, #0f0f0f, #050505);
color:white;
font-family:Arial;
margin:20px;
}

h1{
text-align:center;
color:#b6ff00;
text-shadow:0 0 25px #00ff66, 0 0 40px #b6ff00;
font-size:42px;
}

/* LINKS */
.links{
text-align:center;
margin:15px 0;
}

.links a{
color:#00ff66;
text-decoration:none;
margin:0 12px;
padding:10px 18px;
border:2px solid #00ff66;
border-radius:12px;
box-shadow:0 0 20px #00ff66;
transition:0.3s;
font-weight:bold;
}

.links a:hover{
background:#00ff66;
color:black;
box-shadow:0 0 30px #b6ff00;
}

/* TABLE 3D */
table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
background: rgba(20,20,20,0.7);
box-shadow:0 15px 50px rgba(0,255,100,0.25);
border-radius:15px;
overflow:hidden;
transform: perspective(900px) rotateX(2deg);
}

th,td{
padding:10px;
text-align:center;
border:1px solid rgba(255,255,255,0.05);
}

.team{
color:#00ff66;
font-weight:bold;
text-shadow:0 0 10px #00ff66;
}

.players{
font-size:12px;
line-height:1.5;
}

h2{
text-align:center;
color:#b6ff00;
text-shadow:0 0 20px #b6ff00;
}

tr:hover{
background:rgba(0,255,102,0.08);
}

</style>

</head>

<body>

<h1>🏆 LIGA CBS</h1>

<div class="links">
<a href="https://www.tiktok.com/@manyngg" target="_blank">🎵 TikTok</a>
<a href="https://www.twitch.tv/manyyn" target="_blank">🎮 Twitch</a>
</div>

<table>
<tr>
<th>POS</th>
<th>TEAM</th>
"""

    colors = ["#00ff66", "#b6ff00", "#00ffaa", "#aaff00", "#66ff33", "#d4ff00"]

    idx = 0

    for g in allgames:

        color = colors[idx % len(colors)]
        idx += 1

        html += f"""
<th style='background:{color};color:black'>GAME {g}<br>PLAYERS</th>
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

        medal = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else ""

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

<h2>🔥 FRAGGER TABLE</h2>

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
