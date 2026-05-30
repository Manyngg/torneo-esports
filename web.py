@app.route("/")
def home():
    db = load()
    equipos = db["equipos"]

    # =========================
    # ALL GAMES
    # =========================
    allgames = set()

    for team, data in equipos.items():
        for g in data["games"]:
            allgames.add(g)

    allgames = sorted(list(allgames))

    # =========================
    # FRAGGER TABLE
    # =========================
    fragger = {}

    for team, data in equipos.items():
        for player, stats in data["players"].items():

            if player not in fragger:
                fragger[player] = {
                    "team": team,
                    "kills": 0
                }

            fragger[player]["kills"] += stats["kills"]

    fraggers = sorted(
        fragger.items(),
        key=lambda x: x[1]["kills"],
        reverse=True
    )

    # =========================
    # RANKING TEAMS
    # =========================
    ranking = []

    for team, data in equipos.items():

        total_score = 0
        total_kills = 0

        for g, info in data["games"].items():
            total_score += info["score"]
            total_kills += info["kills"]

        ranking.append({
            "team": team,
            "score": total_score,
            "kills": total_kills,
            "games": data["games"]
        })

    ranking = sorted(ranking, key=lambda x: x["score"], reverse=True)

    # =========================
    # HTML
    # =========================
    html = """
<html>
<head>
<style>
body{
background:#111;
color:white;
font-family:Arial;
margin:20px;
}

table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
}

th{
background:#3247ff;
padding:8px;
border:1px solid #555;
}

td{
border:1px solid #444;
padding:6px;
text-align:center;
}

.teamtitle{
background:#222;
font-weight:bold;
}

.score{
background:#2d2d2d;
font-weight:bold;
}

.fragger{
background:#1c1c1c;
}

</style>
</head>
<body>

<h1>🏆 MANYN ESPORTS</h1>

<!-- ===================== -->
<!-- TABLA GENERAL -->
<!-- ===================== -->
<table>

<tr>
<th rowspan='2'>TEAM</th>
"""

    # headers games
    for g in allgames:
        html += f"<th colspan='4'>GAME {g}</th>"

    html += """
<th rowspan='2'>TOTAL SCORE</th>
<th rowspan='2'>TOTAL KILLS</th>
<th rowspan='2'>INDIVIDUAL KILLS</th>
</tr>

<tr>
"""

    for g in allgames:
        html += """
<th>KILLS</th>
<th>PLACEMENT</th>
<th>TEAM KILLS</th>
<th>SCORE</th>
"""

    html += "</tr>"

    # =========================
    # TEAMS DATA
    # =========================
    for r in ranking:

        html += f"<tr><td class='teamtitle'>{r['team']}</td>"

        individual_kills = 0

        for g in allgames:

            if g in r["games"]:
                game = r["games"][g]
                individual_kills += game["kills"]

                html += f"""
<td>{game['kills']}</td>
<td>{game['placement']}</td>
<td>{game['kills']}</td>
<td class='score'>{game['score']}</td>
"""
            else:
                html += "<td>-</td><td>-</td><td>-</td><td>-</td>"

        html += f"""
<td>{r['score']}</td>
<td>{r['kills']}</td>
<td>{individual_kills}</td>
</tr>
"""

    html += """
</table>

<!-- ===================== -->
<!-- FRAGGER TABLE -->
<!-- ===================== -->

<h2>🔥 FRAGGER TABLE</h2>

<table>
<tr>
<th>PLAYER</th>
<th>TEAM</th>
<th>TOTAL KILLS</th>
</tr>
"""

    for player, stats in fraggers:

        html += f"""
<tr class='fragger'>
<td>{player}</td>
<td>{stats['team']}</td>
<td>{stats['kills']}</td>
</tr>
"""

    html += """
</table>

</body>
</html>
"""

    return html
