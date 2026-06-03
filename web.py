from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB = "data.json"


# =========================
# DB
# =========================

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
# REPORT
# =========================

@app.route("/report", methods=["POST"])
def report():

    body = request.json

    team = str(body.get("equipo", "")).strip()
    game = str(body.get("game", "")).strip()
    placement = int(body.get("placement", 0))

    players = body.get("jugadores", [])
    kills = body.get("kills", [])

    db = load()

    if team not in db["equipos"]:
        db["equipos"][team] = {"games": {}}

    db["equipos"][team]["games"][game] = {
        "placement": placement,
        "kills": sum(kills),
        "score": calcular_score(placement, sum(kills)),
        "players": {
            players[i]: int(kills[i])
            for i in range(min(len(players), len(kills)))
        }
    }

    save(db)
    return jsonify({"ok": True})


# =========================
# MODIFICAR
# =========================

@app.route("/modificar", methods=["POST"])
def modificar():

    body = request.json

    team = str(body.get("equipo", "")).strip()
    game = str(body.get("game", "")).strip()
    placement = int(body.get("placement", 0))

    players = body.get("jugadores", [])
    kills = body.get("kills", [])

    db = load()

    db["equipos"][team]["games"][game] = {
        "placement": placement,
        "kills": sum(kills),
        "score": calcular_score(placement, sum(kills)),
        "players": {
            players[i]: int(kills[i])
            for i in range(min(len(players), len(kills)))
        }
    }

    save(db)
    return jsonify({"ok": True})


# =========================
# BORRAR
# =========================

@app.route("/borrar", methods=["POST"])
def borrar():
    db = load()
    db["equipos"] = {}
    save(db)
    return jsonify({"ok": True})


# =========================
# WEB
# =========================

@app.route("/")
def home():

    db = load()
    equipos = db["equipos"]

    allgames = sorted({g for t in equipos for g in equipos[t]["games"]})

    ranking = []

    total_kills_global = 0

    for team, data in equipos.items():

        score = 0
        kills = 0

        for g, info in data["games"].items():
            score += info["score"]
            kills += info["kills"]
            total_kills_global += info["kills"]

        ranking.append({
            "team": team,
            "score": round(score, 2),
            "kills": kills,
            "games": data["games"]
        })

    ranking.sort(key=lambda x: x["score"], reverse=True)

    top_team = ranking[0]["team"] if ranking else "-"
    top_score = ranking[0]["score"] if ranking else 0

    fragger = {}

    for team, data in equipos.items():
        for g, info in data["games"].items():
            for p, k in info["players"].items():
                fragger[p] = fragger.get(p, {"team": team, "kills": 0})
                fragger[p]["kills"] += k

    fraggers = sorted(fragger.items(), key=lambda x: x[1]["kills"], reverse=True)

    game_colors = ["#00ff66", "#d6ff00", "#00ffaa", "#aaff00"]

    # =========================
    # HTML
    # =========================

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

/* HEADER */
h1{
text-align:center;
color:#00ff66;
text-shadow:0 0 25px #00ff66;
font-size:44px;
margin-bottom:5px;
}

.live{
text-align:center;
color:red;
font-weight:bold;
animation:blink 1s infinite;
margin-bottom:10px;
}

@keyframes blink{
50%{opacity:0.3;}
}

/* STREAM BUTTONS */
.stream-links{
text-align:center;
margin:10px 0;
display:flex;
justify-content:center;
gap:15px;
}

.btn{
padding:10px 18px;
border-radius:10px;
text-decoration:none;
font-weight:bold;
color:white;
transition:0.2s;
box-shadow:0 0 15px rgba(0,0,0,0.5);
display:flex;
align-items:center;
gap:6px;
}

.btn:hover{
transform:scale(1.08);
}

/* TikTok */
.tiktok{
background:linear-gradient(45deg,#00ff66,#00ffaa);
color:black;
}

/* Twitch */
.twitch{
background:linear-gradient(45deg,#d6ff00,#aaff00);
color:black;
}

/* Discord */
.discord{
background:linear-gradient(45deg,#5865F2,#7289DA);
color:white;
}

/* CARDS */
.cards{
display:flex;
justify-content:center;
gap:15px;
margin:20px 0;
}

.card{
background:#111;
border:1px solid #00ff66;
padding:10px 15px;
border-radius:12px;
box-shadow:0 0 15px rgba(0,255,100,0.3);
min-width:140px;
text-align:center;
}

.card h3{
margin:0;
color:#d6ff00;
}

/* TABLE */
table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
background:linear-gradient(145deg,#111,#1a1a1a);
border-radius:15px;
overflow:hidden;
box-shadow:0 12px 30px rgba(0,0,0,0.6);
transform:perspective(900px) rotateX(2deg);
}

th{
background:#00ff66;
color:black;
font-weight:bold;
padding:12px;
text-transform:uppercase;
}

td{
padding:10px;
text-align:center;
border-bottom:1px solid #222;
color:white;
}

tr:hover{
background:rgba(0,255,100,0.08);
transition:0.2s;
}

.team{
color:white;
font-weight:bold;
}

h2{
text-align:center;
color:#d6ff00;
text-shadow:0 0 20px #d6ff00;
}

</style>
</head>

<body>

<h1>🏆 LIGA CBS LATAM</h1>

<div class="stream-links">

<a href="https://www.tiktok.com/@manyngg" target="_blank" class="btn tiktok">
🎵 TikTok
</a>

<a href="https://www.twitch.tv/manyyn" target="_blank" class="btn twitch">
🎮 Twitch
</a>

<a href="https://discord.com" target="_blank" class="btn discord">
💬 Discord
</a>

</div>

<div class='live'>🔴 LIVE TOURNAMENT</div>

<div class="cards">
<div class="card"><h3>TOP TEAM</h3>""" + str(top_team) + """</div>
<div class="card"><h3>SCORE</h3>""" + str(top_score) + """</div>
<div class="card"><h3>TOTAL KILLS</h3>""" + str(total_kills_global) + """</div>
<div class="card"><h3>GAMES</h3>""" + str(len(allgames)) + """</div>
</div>
"""

    # TABLE
    html += "<table><tr><th>POS</th><th>TEAM</th>"

    for g in allgames:
        color = game_colors[int(g) % len(game_colors)] if str(g).isdigit() else "#00ff66"
        html += f"<th style='background:{color}'>GAME {g}</th><th style='background:{color}'>POS</th><th style='background:{color}'>SCORE</th>"

    html += "<th>TOTAL</th><th>KILLS</th></tr>"

    pos = 1

    for r in ranking:

        medal = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else ""

        html += f"<tr><td>{medal} {pos}</td><td class='team'>{r['team']}</td>"

        for g in allgames:

            if g in r["games"]:
                game = r["games"][g]

                players_txt = ""
                for p, k in game["players"].items():
                    players_txt += f"{p}: {k}<br>"

                html += f"<td>{players_txt}</td><td>{game['placement']}</td><td>{game['score']}</td>"
            else:
                html += "<td>-</td><td>-</td><td>-</td>"

        html += f"<td>{r['score']}</td><td>{r['kills']}</td></tr>"
        pos += 1

    html += "</table>"

    # FRAGGER
    html += "<h2>🔥 FRAGGER TABLE</h2>"
    html += "<table><tr><th>PLAYER</th><th>TEAM</th><th>KILLS</th></tr>"

    for p, s in fraggers:
        html += f"<tr><td>{p}</td><td>{s['team']}</td><td>{s['kills']}</td></tr>"

    html += "</table></body></html>"

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    
