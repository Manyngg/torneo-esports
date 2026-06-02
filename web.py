from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB="data.json"

##################################################

def load():

    if not os.path.exists(DB):

        return {

            "equipos":{}

        }

    with open(

        DB,

        "r",

        encoding="utf8"

    ) as f:

        return json.load(f)

##################################################

def save(data):

    with open(

        DB,

        "w",

        encoding="utf8"

    ) as f:

        json.dump(

            data,

            f,

            indent=4,

            ensure_ascii=False

        )

##################################################
# REPORT API
##################################################

@app.route(

"/report",

methods=["POST"]

)

def report():

    body=request.json

    team=body["equipo"]

    game=str(body["game"])

    placement=int(

        body["placement"]

    )

    players=body["jugadores"]

    kills=body["kills"]

    db=load()

##################################################

    if team not in db["equipos"]:

        db["equipos"][team]={

            "games":{},

            "players":{}

        }

##################################################

    if game in db["equipos"][team]["games"]:

        return jsonify({

            "error":"game repetida"

        }),400

##################################################

    teamkills=sum(kills)

##################################################

    if placement == 1:

        mult=1.6

    elif placement <=5:

        mult=1.4

    elif placement <=10:

        mult=1.2

    else:

        mult=1

##################################################

    score=round(

        teamkills*mult,

        2

    )

##################################################

    db["equipos"][team]["games"][game]={

        "placement":placement,

        "kills":teamkills,

        "score":score,

        "players":{

            players[i]:kills[i]

            for i in range(

                len(players)

            )

        }

    }

##################################################

    for i,p in enumerate(players):

        if p not in db["equipos"][team]["players"]:

            db["equipos"][team]["players"][p]={

                "kills":0

            }

        db["equipos"][team]["players"][p]["kills"] += kills[i]

##################################################

    save(db)

    return jsonify({"ok":True})

##################################################
# WEB
##################################################

@app.route("/")

def home():

    db=load()

    equipos=db["equipos"]

##################################################

    allgames=set()

    for team,data in equipos.items():

        for g in data["games"]:

            allgames.add(g)

    allgames=sorted(

        list(allgames)

    )

##################################################

    fragger={}

    for team,data in equipos.items():

        for player,stats in data["players"].items():

            if player not in fragger:

                fragger[player]={

                    "team":team,

                    "kills":0

                }

            fragger[player]["kills"] += stats["kills"]

##################################################

    fraggers=sorted(

        fragger.items(),

        key=lambda x:x[1]["kills"],

        reverse=True

    )

##################################################

    ranking=[]

    for team,data in equipos.items():

        total_score=0

        total_kills=0

        for g,info in data["games"].items():

            total_score+=info["score"]

            total_kills+=info["kills"]

        ranking.append({

            "team":team,

            "score":round(total_score,2),

            "kills":total_kills,

            "games":data["games"]

        })

##################################################

    ranking=sorted(

        ranking,

        key=lambda x:x["score"],

        reverse=True

    )

##################################################

    html="""

<html>

<head>

<meta http-equiv='refresh' content='30'>

<style>

body{
background:#0f0f0f;
color:white;
font-family:Arial;
margin:20px;
}

h1{
color:#ffe600;
}

.stats{
display:flex;
gap:20px;
margin-bottom:20px;
}

.box{
background:#1d1d1d;
padding:12px;
border-radius:10px;
box-shadow:0 0 15px rgba(0,255,255,.2);
}

table{
width:100%;
border-collapse:collapse;
margin-bottom:30px;
}

th{
background:#3247ff;
padding:10px;
}

td{
padding:8px;
border:1px solid #333;
text-align:center;
}

.top1{
background:#594400;
}

.top2{
background:#3b3b3b;
}

.top3{
background:#5d3f21;
}

.playerbox{
font-size:12px;
line-height:1.5;
}

</style>

</head>

<body>

<h1>🏆 Liga CBS</h1>

<div class='stats'>

<div class='box'>
Equipos:
<br>
""" + str(len(equipos)) + """

</div>

<div class='box'>
Partidas:
<br>
""" + str(len(allgames)) + """

</div>

</div>

<table>

<tr>

<th>POS</th>

<th>TEAM</th>

<th>PLAYERS</th>

"""

##################################################

    for g in allgames:

        html += f"""

<th>G{g} POS</th>

<th>G{g} KILLS</th>

<th>G{g} SCORE</th>

"""

##################################################

    html += """

<th>TOTAL SCORE</th>

<th>TOTAL KILLS</th>

</tr>

"""

##################################################

    posicion=1

    for r in ranking:

        clase=""

        medal=""

        if posicion==1:

            medal="🥇"

            clase="top1"

        elif posicion==2:

            medal="🥈"

            clase="top2"

        elif posicion==3:

            medal="🥉"

            clase="top3"

##################################################

        playershtml=""

        teamplayers=equipos[

            r["team"]

        ]["players"]

        for p,s in teamplayers.items():

            playershtml += f"""

{p}: {s['kills']}<br>

"""

##################################################

        html += f"""

<tr class='{clase}'>

<td>

{medal} {posicion}

</td>

<td>

{r['team']}

</td>

<td class='playerbox'>

{playershtml}

</td>

"""

##################################################

        for g in allgames:

            if g in r["games"]:

                game=r["games"][g]

                html += f"""

<td>{game['placement']}</td>

<td>{game['kills']}</td>

<td>{game['score']}</td>

"""

            else:

                html += """

<td>-</td>

<td>-</td>

<td>-</td>

"""

##################################################

        html += f"""

<td>

{r['score']}

</td>

<td>

{r['kills']}

</td>

</tr>

"""

        posicion+=1

##################################################

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

##################################################

    for player,stats in fraggers:

        html += f"""

<tr>

<td>{player}</td>

<td>{stats['team']}</td>

<td>{stats['kills']}</td>

</tr>

"""

##################################################

    html += """

</table>

</body>

</html>

"""

    return html

##################################################

if __name__=="__main__":

    app.run(

        host="0.0.0.0",

        port=10000,

        debug=True

    )
