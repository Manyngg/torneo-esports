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
# WEB
# =========================

@app.route("/")
def home():

    db = load()
    equipos = db["equipos"]

    allgames = sorted({g for t in equipos for g in equipos[t]["games"]})

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

    fragger = {}

    for team, data in equipos.items():
        for g, info in data["games"].items():
            for p, k in info["players"].items():
                fragger[p] = fragger.get(p, {"team": team, "kills": 0})
                fragger[p]["kills"] += k

    fraggers = sorted(fragger.items(), key=lambda x: x[1]["kills"], reverse=True)

    game_colors = ["#00ff66", "#d6ff00", "#00ffaa", "#aaff00"]

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
text-align:center;
color:#00ff66;
text-shadow:0 0 25px #00ff66;
font-size:40px;
margin-bottom:5px;
}

/* =======================
   LINKS
======================= */

.links{
display:flex;
justify-content:center;
gap:20px;
margin-bottom:25px;
}

.link-box{
display:flex;
align-items:center;
gap:10px;
padding:10px 18px;
border-radius:12px;
background:#111;
border:1px solid #00ff66;
box-shadow:0 0 20px rgba(0,255,100,0.4);
}

.link-box a{
color:white;
font-weight:bold;
text-decoration:none;
}

/* =======================
   TABLAS 3D
======================= */

table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
background:linear-gradient(145deg,#111,#1a1a1a);
border-radius:15px;
overflow:hidden;
box-shadow:
0 10px 20px rgba(0,0,0,0.6),
0 0 25px rgba(0,255,100,0.15);
transform:perspective(900px) rotateX(2deg);
}

th{
background:#00ff66;
color:black;
font-weight:bold;
padding:12px;
text-transform:uppercase;
letter-spacing:1px;
box-shadow: inset 0 -3px 0 rgba(0,0,0,0.4);
}

td{
padding:10px;
text-align:center;
border-bottom:1px solid #222;
color:white;
}

/* 🔥 FIX VISIBILIDAD */
thead th, td{
color:white;
font-weight:bold;
}

/* TEAM */
.team{
color:white;
font-weight:bold;
text-shadow:0 0 10px rgba(255,255,255,0.3);
}

/* FRAGGER */
h2{
text-align:center;
color:#d6ff00;
text-shadow:0 0 20px #d6ff00;
font-size:28px;
}

</style>

</head>

<body>

<h1>🏆 LIGA CBS LATAM</h1>
"""

    # LINKS
    html += """
<div class="links">

<div class="link-box">
<a href="https://www.tiktok.com/@manyngg" target="_blank">🎵 TikTok</a>
</div>

<div class="link-box">
<a href="https://www.twitch.tv/manyyn" target="_blank">🎮 Twitch</a>
</div>

</div>
"""

    # =========================
    # RANKING TABLE
    # =========================

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

    # =========================
    # FRAGGER
    # =========================

    html += "<h2>🔥 FRAGGER TABLE</h2>"
    html += "<table><tr><th>POS</th><th>PLAYER</th><th>TEAM</th><th>KILLS</th></tr>"

    pos = 1

    for p, s in fraggers:

        medal = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else ""

        html += f"<tr><td>{medal} {pos}</td><td>{p}</td><td>{s['team']}</td><td>{s['kills']}</td></tr>"
        pos += 1

    html += "</table></body></html>"

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
