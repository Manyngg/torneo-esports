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


def clean(x):
    return str(x).replace(":", "").strip()


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

    team = clean(body["equipo"])
    game = str(body["game"])
    placement = int(body["placement"])

    players = [clean(p) for p in body["jugadores"]]
    kills = body["kills"]

    db = load()

    if team not in db["equipos"]:
        db["equipos"][team] = {"games": {}}

    db["equipos"][team]["games"][game] = {
        "placement": placement,
        "kills": sum(kills),
        "score": calcular_score(placement, sum(kills)),
        "players": {
            players[i]: int(kills[i])
            for i in range(len(players))
        }
    }

    save(db)

    return jsonify({"ok": True})


# =========================
# MODIFY
# =========================

@app.route("/modificar")
def modificar():

    body = request.json

    team = clean(body["equipo"])
    game = str(body["game"])
    placement = int(body["placement"])

    players = [clean(p) for p in body["jugadores"]]
    kills = body["kills"]

    db = load()

    db["equipos"][team]["games"][game] = {
        "placement": placement,
        "kills": sum(kills),
        "score": calcular_score(placement, sum(kills)),
        "players": {
            players[i]: int(kills[i])
            for i in range(len(players))
        }
    }

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
                p = clean(p)
                fragger[p] = fragger.get(p, {"team": team, "kills": 0})
                fragger[p]["kills"] += k

    fraggers = sorted(fragger.items(), key=lambda x: x[1]["kills"], reverse=True)

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

/* TITULO */
h1{
text-align:center;
color:#00ff66;
text-shadow:0 0 25px #00ff66;
font-size:38px;
margin-bottom:5px;
}

/* LINKS */
.links{
text-align:center;
margin-bottom:20px;
}

.links a{
color:#fff;
margin:0 15px;
text-decoration:none;
font-weight:bold;
}

.links a:hover{
color:#00ff66;
text-shadow:0 0 10px #00ff66;
}

/* TABLA PRINCIPAL */
table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
background:linear-gradient(145deg,#0f0f0f,#151515);
box-shadow:0 10px 40px rgba(0,255,100,0.25);
border-radius:12px;
overflow:hidden;
}

/* HEADERS */
th{
background:#00ff66;
color:#000;
padding:12px;
font-size:14px;
text-transform:uppercase;
letter-spacing:1px;
}

/* CELDAS */
td{
padding:10px;
text-align:center;
border-bottom:1px solid #222;
}

/* EQUIPOS EN BLANCO */
.team{
color:white;
font-weight:bold;
text-shadow:0 0 10px rgba(255,255,255,0.2);
}

/* PLAYERS */
.players{
font-size:12px;
line-height:1.5;
color:#ccc;
}

/* EFECTO 3D */
table:hover{
transform:scale(1.01);
transition:0.3s;
}

/* FRAGGER */
h2{
text-align:center;
color:#d6ff00;
text-shadow:0 0 20px #d6ff00;
}

</style>

</head>

<body>

<h1>🏆 LIGA CBS</h1>

<div class="links">
<a href="https://www.tiktok.com/@manyngg" target="_blank">TikTok</a>
<a href="https://www.twitch.tv/manyyn" target="_blank">Twitch</a>
</div>
"""

    # =========================
    # RANKING
    # =========================

    html += "<table><tr><th>POS</th><th>TEAM</th>"

    for g in allgames:
        html += "<th>GAME</th><th>POS</th><th>SCORE</th>"

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
                    players_txt += f"{p} : {k}<br>"

                html += f"<td class='players'>{players_txt}</td><td>{game['placement']}</td><td>{game['score']}</td>"
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
