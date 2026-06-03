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

    fraggers = {}

    for team, data in equipos.items():
        for p, s in data["players"].items():
            if p not in fraggers:
                fraggers[p] = {"team": team, "kills": 0}
            fraggers[p]["kills"] += s["kills"]

    fraggers = sorted(fraggers.items(), key=lambda x: x[1]["kills"], reverse=True)

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
text-align:center;
text-shadow:0 0 15px #00ff66;
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
padding:8px;
text-align:center;
border-bottom:1px solid rgba(255,255,255,0.1);
}

/* STREAM */
.stream{
display:flex;
justify-content:center;
margin-top:20px;
}

.stream iframe{
width:420px;
height:240px;
border-radius:12px;
border:2px solid #00ff66;
}

</style>

</head>

<body>

<h1>🏆 Liga CBS</h1>
"""

    # TABLA GENERAL
    html += "<table><tr><th>TEAM</th><th>SCORE</th><th>KILLS</th></tr>"

    for r in ranking:
        html += f"""
<tr>
<td>{r['team']}</td>
<td>{r['score']}</td>
<td>{r['kills']}</td>
</tr>
"""

    html += "</table>"

    # FRAGGER
    html += "<h2 style='color:#00ff66'>🔥 FRAGGER</h2><table><tr><th>PLAYER</th><th>TEAM</th><th>KILLS</th></tr>"

    for p, s in fraggers:
        html += f"""
<tr>
<td>{p}</td>
<td>{s['team']}</td>
<td>{s['kills']}</td>
</tr>
"""

    html += "</table>"

    # 🎥 STREAM CORRECTO
    html += """
<div class="stream">
<iframe
src="https://player.twitch.tv/?channel=manyyn&parent=localhost"
allowfullscreen>
</iframe>
</div>

</body>
</html>
"""

    return html

#################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
