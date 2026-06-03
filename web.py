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

    team = body["equipo"].strip()
    game = str(body["game"])
    placement = int(body["placement"])

    players = [p.strip() for p in body["jugadores"]]
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
        "players": {
            players[i].strip(): int(kills[i])
            for i in range(len(players))
        }
    }

    save(db)

    return jsonify({"ok": True})


# =========================
# MODIFY
# =========================

@app.route("/modificar", methods=["POST"])
def modificar():

    body = request.json

    team = body["equipo"].strip()
    game = str(body["game"])
    placement = int(body["placement"])

    players = [p.strip() for p in body["jugadores"]]
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
        "players": {
            players[i].strip(): int(kills[i])
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
    # FRAGGER
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

h1{
text-align:center;
color:#b6ff00;
text-shadow:0 0 20px #00ff66;
}

table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
background:#111;
box-shadow:0 0 25px rgba(0,255,100,0.2);
}

th,td{
padding:10px;
text-align:center;
border:1px solid #222;
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

/* EVITA DOBLES :: VISUALMENTE */
.players br{
display:block;
margin:2px 0;
}

h2{
text-align:center;
color:#b6ff00;
text-shadow:0 0 20px #b6ff00;
}

</style>

</head>

<body>

<h1>🏆 LIGA CBS</h1>

<table>
<tr>
<th>POS</th>
<th>TEAM</th>
"""

    for g in allgames:

        html += f"""
<th>GAME {g}<br>PLAYERS</th>
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
                    players_txt += f"{p.strip()} : {k}<br>"

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
<td>{p.strip()}</td>
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
    app.run(host="0.0.0.0", port=10000, debug=True)
