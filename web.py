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

    # duplicados
    posiciones_por_game = {}

    for team, data in equipos.items():
        for g, info in data["games"].items():
            pos = info["placement"]
            posiciones_por_game.setdefault(g, {})
            posiciones_por_game[g].setdefault(pos, 0)
            posiciones_por_game[g][pos] += 1

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
background:#f2eee6;
color:#111;
font-family:Arial;
margin:20px;
}

h1{
text-align:center;
color:#00aa55;
text-shadow:0 2px 10px rgba(0,0,0,0.15);
font-size:44px;
}

/* LIVE ANIMATION */
.live{
text-align:center;
color:#d60000;
font-weight:bold;
animation:blink 1s infinite;
}

@keyframes blink{
50%{opacity:0.3;}
}

/* STREAM LINKS (NO SE ELIMINA NUNCA) */
.stream-links{
text-align:center;
margin:10px 0;
display:flex;
justify-content:center;
gap:15px;
}

.btn{
padding:10px 18px;
border-radius:12px;
text-decoration:none;
font-weight:bold;
color:black;
box-shadow:0 6px 15px rgba(0,0,0,0.2);
}

.tiktok{background:linear-gradient(45deg,#00ff66,#00ffaa);}
.twitch{background:linear-gradient(45deg,#d6ff00,#aaff00);}

/* CARDS (RESTAURADO COMPLETO) */
.cards{
display:flex;
justify-content:center;
gap:15px;
margin:20px 0;
}

.card{
background:#1e1e1e;
color:white;
border-radius:14px;
padding:12px 18px;
min-width:140px;
text-align:center;
box-shadow:0 6px 0 #111, 0 12px 25px rgba(0,0,0,0.25);
}

/* TABLAS 3D */
table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
background:#e6e6e6;
border-radius:16px;
overflow:hidden;
box-shadow:0 10px 0 #bdbdbd, 0 18px 35px rgba(0,0,0,0.25);
transform:perspective(1000px) rotateX(2deg);
}

th{
background:#00ff66;
color:black;
padding:12px;
text-transform:uppercase;
}

td{
padding:10px;
text-align:center;
border-bottom:1px solid #cfcfcf;
color:#111;
}

/* DUPLICADOS */
.duplicate-pos{
color:red !important;
font-weight:bold;
}

/* FRAGGER */
h2{
text-align:center;
color:#b59a00;
}

</style>
</head>

<body>

<h1>🏆 LIGA CBS LATAM</h1>

<div class='live'>🔴 LIVE TOURNAMENT</div>

<!-- CARDS RESTAURADOS -->
<div class="cards">

<div class="card">
TOP TEAM<br>
""" + str(top_team) + """
</div>

<div class="card">
SCORE<br>
""" + str(top_score) + """
</div>

<div class="card">
KILLS<br>
""" + str(total_kills_global) + """
</div>

<div class="card">
GAMES<br>
""" + str(len(allgames)) + """
</div>

</div>

<!-- STREAM LINKS RESTAURADOS (NO SE TOCAN MÁS) -->
<div class="stream-links">

<a href="https://www.tiktok.com/@manyngg" target="_blank" class="btn tiktok">🎵 TikTok</a>
<a href="https://www.twitch.tv/manyyn" target="_blank" class="btn twitch">🎮 Twitch</a>

</div>
"""

    # =========================
    # TABLA GENERAL
    # =========================

    html += "<table><tr><th>POS</th><th>TEAM</th>"

    for g in allgames:
        color = game_colors[int(g) % len(game_colors)] if str(g).isdigit() else "#00ff66"
        html += f"<th style='background:{color}'>GAME {g}</th><th style='background:{color}'>POS</th><th style='background:{color}'>SCORE</th>"

    html += "<th>TOTAL</th><th>KILLS</th></tr>"

    pos = 1

    for r in ranking:

        medal = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else ""

        html += f"<tr><td>{medal} {pos}</td><td>{r['team']}</td>"

        for g in allgames:

            if g in r["games"]:
                game = r["games"][g]

                cls = ""
                if g in posiciones_por_game and posiciones_por_game[g].get(game["placement"], 0) > 1:
                    cls = "duplicate-pos"

                players_txt = ""
                for p, k in game["players"].items():
                    players_txt += f"{p}: {k}<br>"

                html += f"<td>{players_txt}</td><td class='{cls}'>{game['placement']}</td><td>{game['score']}</td>"
            else:
                html += "<td>-</td><td>-</td><td>-</td>"

        html += f"<td>{r['score']}</td><td>{r['kills']}</td></tr>"
        pos += 1

    html += "</table>"

    # =========================
    # FRAGGER (SIN CAMBIOS)
    # =========================

    html += "<h2>🔥 FRAGGER TABLE</h2>"
    html += "<table><tr><th>POS</th><th>PLAYER</th><th>TEAM</th><th>KILLS</th></tr>"

    ppos = 1
    for p, s in fraggers:

        medal = "🥇" if ppos == 1 else "🥈" if ppos == 2 else "🥉" if ppos == 3 else ""

        html += f"<tr><td>{medal} {ppos}</td><td>{p}</td><td>{s['team']}</td><td>{s['kills']}</td></tr>"
        ppos += 1

    html += "</table></body></html>"

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
