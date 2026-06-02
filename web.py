from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB="data.json"

#########################################

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

#########################################
# REPORT API
#########################################

@app.route(

"/report",

methods=["POST"]

)

def report():

    body=request.json

    team=body["equipo"]

    game=str(

        body["game"]

    )

    placement=int(

        body["placement"]

    )

    players=body["jugadores"]

    kills=body["kills"]

    db=load()

    if team not in db["equipos"]:

        db["equipos"][team]={

            "games":{},

            "players":{}

        }

    if game in db["equipos"][team]["games"]:

        return jsonify({

            "error":"game repetida"

        }),400

    teamkills=sum(kills)

#########################################
# MULTIPLICADORES
#########################################

    if placement == 1:

        mult=1.6

    elif placement <=5:

        mult=1.4

    elif placement <=10:

        mult=1.2

    else:

        mult=1

#########################################

    score=round(

        teamkills*mult,

        2

    )

#########################################

    db["equipos"][team]["games"][game]={

        "placement":placement,

        "kills":teamkills,

        "score":score

    }

#########################################

    for i,p in enumerate(players):

        if p not in db["equipos"][team]["players"]:

            db["equipos"][team]["players"][p]={

                "kills":0

            }

        db["equipos"][team]["players"][p]["kills"] += kills[i]

#########################################

    save(db)

    return jsonify({

        "ok":True

    })

#########################################
# WEB
#########################################

@app.route("/")

def home():

    db=load()

    equipos=db["equipos"]

#########################################

    fragger={}

    for team,data in equipos.items():

        for player,stats in data["players"].items():

            if player not in fragger:

                fragger[player]={

                    "team":team,

                    "kills":0

                }

            fragger[player]["kills"] += stats["kills"]

#########################################

    fraggers=sorted(

        fragger.items(),

        key=lambda x:x[1]["kills"],

        reverse=True

    )

#########################################

    allgames=set()

    for team,data in equipos.items():

        for g in data["games"]:

            allgames.add(g)

#########################################

    allgames=sorted(

        list(allgames)

    )

#########################################

    html="""

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

</style>

</head>

<body>

<h1>

🏆 Liga CBS

</h1>

<table>

<tr>

<th rowspan='2'>POS</th>

<th rowspan='2'>TEAM</th>

"""

#########################################

    for g in allgames:

        html += f"""

<th colspan='3'>

GAME {g}

</th>

"""

#########################################

    html += """

<th rowspan='2'>TOTAL SCORE</th>

<th rowspan='2'>TOTAL KILLS</th>

</tr>

<tr>

"""

#########################################

    for g in allgames:

        html += """

<th>PLACEMENT</th>

<th>KILLS</th>

<th>SCORE</th>

"""

#########################################

    html += "</tr>"

#########################################

    ranking=[]

    for team,data in equipos.items():

        total_score=0

        total_kills=0

        for g,info in data["games"].items():

            total_score += info["score"]

            total_kills += info["kills"]

        ranking.append({

            "team":team,

            "score":round(
                total_score,
                2
            ),

            "kills":total_kills,

            "games":data["games"]

        })

#########################################

    ranking=sorted(

        ranking,

        key=lambda x:x["score"],

        reverse=True

    )

#########################################

    posicion=1

    for r in ranking:

        html += f"""

<tr>

<td>{posicion}</td>

<td class='teamtitle'>

{r['team']}

</td>

"""

        posicion += 1

#########################################

        for g in allgames:

            if g in r["games"]:

                game=r["games"][g]

                html += f"""

<td>{game['placement']}</td>

<td>{game['kills']}</td>

<td class='score'>

{game['score']}

</td>

"""

            else:

                html += """

<td>-</td>

<td>-</td>

<td>-</td>

"""

#########################################

        html += f"""

<td>

{r['score']}

</td>

<td>

{r['kills']}

</td>

</tr>

"""

#########################################

    html += """

</table>

<h2>

🔥 FRAGGER TABLE

</h2>

<table>

<tr>

<th>PLAYER</th>

<th>TEAM</th>

<th>TOTAL KILLS</th>

</tr>

"""

#########################################

    for player,stats in fraggers:

        html += f"""

<tr>

<td>{player}</td>

<td>{stats['team']}</td>

<td>{stats['kills']}</td>

</tr>

"""

#########################################

    html += """

</table>

</body>

</html>

"""

    return html

#########################################

if __name__=="__main__":

    app.run(

        host="0.0.0.0",

        port=10000,

        debug=True

    )
