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

/* TITULO */
h1{
color:#00ff66;
text-align:center;
text-shadow:0 0 15px #00ff66;
}

/* CAJA LINKS */
.links{
display:flex;
justify-content:center;
gap:20px;
margin:15px 0 25px 0;
}

.link-box{
background:rgba(255,255,255,0.05);
padding:15px 25px;
border-radius:12px;
box-shadow:0 10px 25px rgba(0,0,0,0.5);
text-align:center;
transition:0.3s;
}

.link-box:hover{
transform:scale(1.05);
}

.link-box a{
color:white;
text-decoration:none;
font-weight:bold;
}

/* ICONOS */
.twitch{
color:#a970ff;
font-weight:bold;
}

.tiktok{
color:#ff0050;
font-weight:bold;
}

/* TABLAS */
table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
background:rgba(255,255,255,0.05);
border-radius:12px;
overflow:hidden;
box-shadow:0 10px 25px rgba(0,0,0,0.5);
}

th{
background:rgba(0,255,102,0.2);
color:#00ff66;
padding:10px;
}

td{
padding:10px;
text-align:center;
border-bottom:1px solid rgba(255,255,255,0.1);
}

.team{
color:white;
font-weight:bold;
}

tr:hover{
background:rgba(0,255,102,0.1);
}

h2{
color:#00ff66;
text-shadow:0 0 10px #00ff66;
}

</style>

</head>

<body>

<h1>🏆 Liga CBS</h1>

<!-- 🔗 LINKS -->
<div class="links">

<div class="link-box twitch">
🎮 Twitch<br>
<a href="https://www.twitch.tv/manyyn" target="_blank">Manyyn</a>
</div>

<div class="link-box tiktok">
🎵 TikTok<br>
<a href="https://www.tiktok.com/@manyngg?_r=1&_t=ZS-96tAVhwT6Fr" target="_blank">@manyngg</a>
</div>

</div>
"""

    # TABLA GENERAL
    html += """
<table>
<tr>
<th>POS</th>
<th>TEAM</th>
<th>SCORE</th>
<th>KILLS</th>
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
<td>{r['score']}</td>
<td>{r['kills']}</td>
</tr>
"""
        pos += 1

    html += "</table>"

    # FRAGGER TABLE
    html += """
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
