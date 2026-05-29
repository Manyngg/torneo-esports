from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB="data.json"

################################################

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

################################################
# API REPORT
################################################

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

    score=(25-placement)+teamkills

    db["equipos"][team]["games"][game]={

        "placement":placement,
        "kills":teamkills,
        "score":score

    }

    for i,p in enumerate(players):

        if p not in db["equipos"][team]["players"]:

            db["equipos"][team]["players"][p]={

                "kills":0

            }

        db["equipos"][team]["players"][p]["kills"] += kills[i]

    save(db)

    return jsonify({

        "ok":True

    })


################################################
# WEB
################################################

@app.route("/")

def home():

    db=load()

    equipos=db["equipos"]

    allgames=set()

    for team,data in equipos.items():

        for g in data["games"]:

            allgames.add(g)

    allgames=sorted(
        list(allgames)
    )

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

font-size:12px;

}

th{

background:#3247ff;

padding:6px;

border:1px solid #555;

}

td{

border:1px solid #444;

padding:4px;

text-align:center;

}

.teamtitle{

background:#2a2a2a;

font-weight:bold;

}

.player{

background:#1a1a1a;

}

.score{

background:#333;

font-weight:bold;

}

</style>

</head>

<body>

<h1>

🏆 MANYN ESPORTS

</h1>

<table>

<tr>

<th rowspan='2'>

TEAM

</th>

"""

    for g in allgames:

        html += f"""

<th colspan='4'>

GAME {g}

</th>

"""

    html += """

<th rowspan='2'>

TOTAL SCORE

</th>

<th rowspan='2'>

TOTAL KILLS

</th>

<th rowspan='2'>

INDIVIDUAL KILLS

</th>

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

################################################
# TEAMS
################################################

    for team,data in equipos.items():

        players=list(
            data["players"].items()
        )

        rows=max(
            len(players),
            1
        )

        total_score=0
        total_kills=0

        for g,info in data["games"].items():

            total_score += info["score"]

            total_kills += info["kills"]

        for i in range(rows):

            html+="<tr>"

            if i==0:

                html += f"""

<td class='teamtitle'
rowspan='{rows}'>

{team}

</td>

"""

                for g in allgames:

                    if g in data["games"]:

                        game=data["games"][g]

                        html += f"""

<td>

{game['kills']}

</td>

<td>

{game['placement']}

</td>

<td>

{game['kills']}

</td>

<td class='score'>

{game['score']}

</td>

"""

                    else:

                        html += """

<td>-</td>

<td>-</td>

<td>-</td>

<td>-</td>

"""

                html += f"""

<td rowspan='{rows}'>

{total_score}

</td>

<td rowspan='{rows}'>

{total_kills}

</td>

"""

            if i < len(players):

                pname=players[i][0]

                pkills=players[i][1]["kills"]

                html += f"""

<td class='player'>

{pname}

<br>

{pkills}

</td>

"""

            else:

                html += "<td>-</td>"

            html += "</tr>"

################################################

    html += """

</table>

</body>

</html>

"""

    return html

################################################

if __name__=="__main__":

    app.run(

        host="0.0.0.0",

        port=10000,

        debug=True

    )
