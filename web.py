from flask import Flask, request, jsonify

import json
import os

app = Flask(__name__)

DB="data.json"


###########################

def load():

    if not os.path.exists(DB):

        return {

            "equipos":{}

        }

    with open(DB,"r",encoding="utf8") as f:

        return json.load(f)


def save(data):

    with open(DB,"w",encoding="utf8") as f:

        json.dump(

            data,

            f,

            indent=4,

            ensure_ascii=False

        )


###########################
# REPORT API
###########################

@app.route("/report",methods=["POST"])

def report():

    body=request.json

    team=body["equipo"]

    game=str(body["game"])

    placement=int(body["placement"])

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

        })


    teamkills=sum(kills)

    score=(25-placement)+teamkills


    db["equipos"][team]["games"][game]={

        "placement":placement,

        "kills":teamkills,

        "score":score

    }


    for i,name in enumerate(players):

        if name not in db["equipos"][team]["players"]:

            db["equipos"][team]["players"][name]={

                "kills":0,

                "matches":0

            }

        db["equipos"][team]["players"][name]["kills"]+=kills[i]

        db["equipos"][team]["players"][name]["matches"]+=1


    save(db)

    return jsonify({"ok":True})


###########################
# WEB
###########################

@app.route("/")

def home():

    db=load()

    equipos=db["equipos"]


    allgames=set()

    fragger={}


    ranking=[]


    for team,data in equipos.items():

        total_score=0

        total_kills=0


        for g,info in data["games"].items():

            allgames.add(g)

            total_score+=info["score"]

            total_kills+=info["kills"]


        ranking.append({

            "team":team,

            "score":total_score,

            "kills":total_kills,

            "games":data["games"]

        })


        for p,s in data["players"].items():

            if p not in fragger:

                fragger[p]={

                    "kills":0,

                    "team":team

                }

            fragger[p]["kills"]+=s["kills"]


    ranking=sorted(

        ranking,

        key=lambda x:x["score"],

        reverse=True

    )


    fraggers=sorted(

        fragger.items(),

        key=lambda x:x[1]["kills"],

        reverse=True

    )


    allgames=sorted(list(allgames))


    html="""

<html>

<head>

<style>

body{

background:#0a0a0a;

color:white;

font-family:Arial;

margin:20px;

}

.wrapper{

display:flex;

gap:20px;

align-items:flex-start;

}

.left{

width:75%;

overflow:auto;

}

.right{

width:25%;

}

table{

border-collapse:collapse;

width:100%;

background:#161616;

}

th{

background:#3247ff;

padding:8px;

font-size:13px;

}

td{

border:1px solid #333;

padding:8px;

text-align:center;

}

.team{

background:#222;

font-weight:bold;

}

.fragger{

background:#111;

}

</style>

</head>

<body>

<h1>🏆 MANYN ESPORTS</h1>

<div class='wrapper'>

<div class='left'>

<table>

<tr>

<th>TEAM</th>

"""

    for g in allgames:

        html+=f"""

<th>{g} K</th>

<th>{g} P</th>

<th>{g} S</th>

"""

    html+="""

<th>TOTAL SCORE</th>

<th>TOTAL KILLS</th>

</tr>

"""

    for r in ranking:

        html+=f"""

<tr>

<td class='team'>{r['team']}</td>

"""

        for g in allgames:

            if g in r["games"]:

                game=r["games"][g]

                html+=f"""

<td>{game['kills']}</td>

<td>{game['placement']}</td>

<td>{game['score']}</td>

"""

            else:

                html+="<td>-</td><td>-</td><td>-</td>"


        html+=f"""

<td>{r['score']}</td>

<td>{r['kills']}</td>

</tr>

"""


    html+="</table></div>"


    html+="""


<div class='right'>

<table>

<tr>

<th>PLAYER</th>

<th>TEAM</th>

<th>KILLS</th>

</tr>

"""

    for name,s in fraggers:

        html+=f"""

<tr class='fragger'>

<td>{name}</td>

<td>{s['team']}</td>

<td>{s['kills']}</td>

</tr>

"""

    html+="</table></div></div></body></html>"


    return html


###########################

if __name__=="__main__":

    app.run(

        host="0.0.0.0",

        port=10000,

        debug=True

    )
