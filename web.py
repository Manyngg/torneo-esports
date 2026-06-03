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

    html = """
<html>
<head>
<meta http-equiv='refresh' content='30'>

<style>

body{
background: radial-gradient(circle at top, #111, #000);
color:white;
font-family:Arial;
margin:20px;
}

/* TITULO */
h1{
color:#00ff66;
text-align:center;
text-shadow:0 0 15px #00ff66, 0 0 30px #00ff66;
margin-bottom:10px;
}

/* REDES */
.links{
display:flex;
justify-content:center;
gap:20px;
margin-bottom:25px;
}

.link-box{
padding:12px 20px;
border-radius:12px;
background: linear-gradient(145deg, #1a1a1a, #0d0d0d);
box-shadow: 6px 6px 15px #000, -6px -6px 15px #1f1f1f;
transition:0.3s;
}

.link-box:hover{
transform: translateY(-5px);
box-shadow: 0 10px 25px #000;
}

.link-box a{
color:white;
text-decoration:none;
font-weight:bold;
}

.twitch{
color:#a970ff;
}

.tiktok{
color:#ff0050;
}

/* TABLA 3D */
table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
background: linear-gradient(145deg, #121212, #0a0a0a);
border-radius:15px;
overflow:hidden;
box-shadow: 10px 10px 25px #000, -5px -5px 15px #1a1a1a;
}

th{
background:rgba(0,255,102,0.15);
color:#00ff66;
padding:12px;
text-shadow:0 0 10px #00ff66;
}

td{
padding:10px;
text-align:center;
border-bottom:1px solid rgba(255,255,255,0.08);
}

.team{
font-weight:bold;
color:white;
}

tr:hover{
background:rgba(0,255,102,0.08);
transform: scale(1.01);
transition:0.2s;
}

h2{
color:#00ff66;
text-shadow:0 0 10px #00ff66;
}

</style>

</head>

<body>

<h1>🏆 Liga CBS</h1>

<!-- 🔥 REDES -->
<div class="links">

<div class="link-box twitch">
🎮 Twitch:<br>
<a href="https://www.twitch.tv/manyyn" target="_blank">Manyyn</a>
</div>

<div class="link-box tiktok">
🎵 TikTok:<br>
<a href="https://www.tiktok.com/@manyngg" target="_blank">@manyngg</a>
</div>

</div>
"""
