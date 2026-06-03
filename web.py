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

        for p, k in data["players"].items():
            fragger[p] = fragger.get(p, {"team": team, "kills": 0})
            fragger[p]["kills"] += k

    fraggers = sorted(
        fragger.items(),
        key=lambda x: x[1]["kills"],
        reverse=True
    )

    # =========================
    # HTML STYLE PRO
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
color:#b6ff00;
text-shadow:0 0 25px #b6ff00, 0 0 50px #00ff66;
font-size:40px;
text-align:center;
}

/* LINKS */
.links{
text-align:center;
margin:10px 0 25px 0;
}

.links a{
color:#00ff66;
text-decoration:none;
margin:0 15px;
font-weight:bold;
font-size:18px;
padding:8px 15px;
border:1px solid #00ff66;
border-radius:10px;
box-shadow:0 0 15px #00ff66;
transition:0.3s;
}

.links a:hover{
background:#00ff66;
color:black;
box-shadow:0 0 25px #b6ff00;
}

/* TABLA 3D */
table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
background: rgba(20,20,20,0.6);
box-shadow:0 10px 40px rgba(0,255,100,0.2);
border-radius:15px;
overflow:hidden;
transform: perspective(900px) rotateX(2deg);
}

th,td{
padding:10px;
text-align:center;
border:1px solid rgba(255,255,255,0.05);
}

th{
text-shadow:0 0 10px black;
}

/* TEAM */
.team{
color:#00ff66;
font-weight:bold;
text-shadow:0 0 10px #00ff66;
}

/* PLAYERS */
.players{
font-size:12px;
line-height:1.5;
}

/* FRAGGER TITLE */
h2{
text-align:center;
text-shadow:0 0 20px #b6ff00;
}

/* hover filas */
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

    # =========================
    # COLORS GAME (NEON VARIATION)
    # =========================

    colors = [
        "#00ff66", "#b6ff00", "#00ffaa",
        "#aaff00", "#66ff33", "#d4ff00"
    ]

    idx = 0

    for g in allgames:

        color = colors[idx % len(colors)]
        idx += 1

        html += f"""
<th style='background:{color};color:black;box-shadow:0 0 15px {color}'>
GAME {g}<br>PLAYERS
</th>
<th style='background:{color};color:black'>POS</th>
<th style='background:{color};color:black'>SCORE</th>
"""

    html += """
<th>TOTAL SCORE</th>
<th>TOTAL KILLS</th>
</tr>
"""

    # =========================
    # ROWS
    # =========================

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
