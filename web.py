from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB="data.json"

#################################################

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

#################################################

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

#################################################
# REPORT API
#################################################

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

#################################################

    if team not in db["equipos"]:

        db["equipos"][team]={

            "games":{},

            "players":{}

        }

#################################################

    if game in db["equipos"][team]["games"]:

        return jsonify({

            "error":"game repetida"

        }),400

#################################################

    teamkills=sum(kills)

#################################################

    if placement==1:

        mult=1.6

    elif placement<=5:

        mult=1.4

    elif placement<=10:

        mult=1.2

    else:

        mult=1

#################################################

    score=round(

        teamkills*mult,

        2

    )

#################################################

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

#################################################

    for i,p in enumerate(players):

        if p not in db["equipos"][team]["players"]:

            db["equipos"][team]["players"][p]={

                "kills":0

            }

        db["equipos"][team]["players"][p]["kills"]+=kills[i]

#################################################

    save(db)

    return jsonify({

        "ok":True

    })

#################################################
# WEB
#################################################

@app.route("/")

def home():

    db=load()

    equipos=db["equipos"]

#################################################

    allgames=set()

    for t,d in equipos.items():

        for g in d["games"]:

            allgames.add(g)

    allgames=sorted(

        list(allgames)

    )

#################################################

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

#################################################

    ranking=sorted(

        ranking,

        key=lambda x:x["score"],

        reverse=True

    )

#################################################

    fragger={}

    for team,data in equipos.items():

        for p,s in data["players"].items():

            if p not in fragger:

                fragger[p]={

                    "team":team,

                    "kills":0

                }

            fragger[p]["kills"]+=s["kills"]

#################################################

    fraggers=sorted(

        fragger.items(),

        key=lambda x:x[1]["kills"],

        reverse=True

    )

#################################################

    colors=[

"#00ff66",

"#c8ff00",

"#00ffcc",

"#d0ff00",

"#66ff00",

"#ffe600"

]

#################################################

    html="""

<html>

<head>

<meta http-equiv='refresh' content='30'>

<style>

body{

background:#090909;

color:white;

font-family:Arial;

margin:20px;

}

h1{

color:#d4ff00;

text-shadow:0 0 20px #d4ff00;

}

table{

width:100%;

border-collapse:collapse;

margin-bottom:30px;

}

th{

padding:10px;

border:1px solid #00ff66;

}

td{

padding:8px;

border:1px solid #1f1f1f;

text-align:center;

}

.team{

font-weight:bold;

color:#00ff66;

}

.players{

font-size:12px;

line-height:1.6;

}

.top1{

background:#404000;

}

.top2{

background:#1d331d;

}

.top3{

background:#223300;

}

</style>

</head>

<body>

<h1>

🏆 Liga CBS

</h1>

<table>

<tr>

<th>POS</th>

<th>TEAM</th>

"""

#################################################

    idx=0

    for g in allgames:

        color=colors[

            idx%

            len(colors)

        ]

        idx+=1

        html+=f"""

<th style='background:{color};color:black'>

GAME {g}

<br>

PLAYERS

</th>

<th style='background:{color};color:black'>

POS

</th>

<th style='background:{color};color:black'>

SCORE

</th>

"""

#################################################

    html+="""

<th>TOTAL SCORE</th>

<th>TOTAL KILLS</th>

</tr>

"""

#################################################

    pos=1

    for r in ranking:

        cls=""

        medal=""

        if pos==1:

            medal="🥇"

            cls="top1"

        elif pos==2:

            medal="🥈"

            cls="top2"

        elif pos==3:

            medal="🥉"

            cls="top3"

#################################################

        html+=f"""

<tr class='{cls}'>

<td>

{medal} {pos}

</td>

<td class='team'>

{r['team']}

</td>

"""

#################################################

        for g in allgames:

            if g in r["games"]:

                game=r["games"][g]

                players=""

                for p,k in game["players"].items():

                    players+=f"""

{p}: {k}<br>

"""

                html+=f"""

<td class='players'>

{players}

</td>

<td>

{game['placement']}

</td>

<td>

{game['score']}

</td>

"""

            else:

                html+="""

<td>-</td>

<td>-</td>

<td>-</td>

"""

#################################################

        html+=f"""

<td>

{r['score']}

</td>

<td>

{r['kills']}

</td>

</tr>

"""

        pos+=1

#################################################

    html+="""

</table>

<h2 style='color:#00ff66'>

🔥 FRAGGER TABLE

</h2>

<table>

<tr>

<th>PLAYER</th>

<th>TEAM</th>

<th>KILLS</th>

</tr>

"""

#################################################

    for p,s in fraggers:

        html+=f"""

<tr>

<td>{p}</td>

<td>{s['team']}</td>

<td>{s['kills']}</td>

</tr>

"""

#################################################

    html+="""

</table>

</body>

</html>

"""

    return html

#################################################

if __name__=="__main__":

    app.run(

        host="0.0.0.0",

        port=10000,

        debug=True

    )
