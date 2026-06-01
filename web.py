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

#########################################
# WEB
#########################################

@app.route("/")

def home():

    db=load()

    equipos=db["equipos"]

#########################################
# FRAGGER TABLE DATA
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

🏆 MANYN ESPORTS

</h1>

<table>

<tr>

<th rowspan='2'>

TEAM

</th>

"""

#########################################
# HEADERS GAME
#########################################

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

</tr>

<tr>

"""

    for g in allgames:

        html += """

<th>

KILLS

</th>

<th>

PLACEMENT

</th>

<th>

TEAM KILLS

</th>

<th>

SCORE

</th>

"""

    html += "</tr>"

#########################################
# TEAMS
#########################################

    ranking=[]

    for team,data in equipos.items():

        total_score=0

        total_kills=0

        for g,info in data["games"].items():

            total_score+=info["score"]

            total_kills+=info["kills"]

        ranking.append({

            "team":team,

            "score":total_score,

            "kills":total_kills,

            "games":data["games"]

        })

    ranking=sorted(

        ranking,

        key=lambda x:x["score"],

        reverse=True

    )

#########################################

    for r in ranking:

        html += f"""

<tr>

<td class='teamtitle'>

{r['team']}

</td>

"""

        for g in allgames:

            if g in r["games"]:

                game=r["games"][g]

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

<td>

{r['score']}

</td>

<td>

{r['kills']}

</td>

</tr>

"""

#########################################
# FRAGGER TABLE
#########################################

    html += """

</table>

<h2>

🔥 FRAGGER TABLE

</h2>

<table>

<tr>

<th>

PLAYER

</th>

<th>

TEAM

</th>

<th>

TOTAL KILLS

</th>

</tr>

"""

    for player,stats in fraggers:

        html += f"""

<tr>

<td>

{player}

</td>

<td>

{stats['team']}

</td>

<td>

{stats['kills']}

</td>

</tr>

"""

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

 _BOY

import discord
import requests

TOKEN = "MTUwOTY4NzM2MjA4NTU4NDk2Ng.GXdFAO.C4m6QvO5NTdy50n7GZz1c-7BqDHZAZlA390DFk"
URL = "https://torneo-esports.onrender.com"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


def enviar(data, endpoint):
    try:
        r = requests.post(URL + endpoint, json=data, timeout=10)

        print("WEB STATUS:", r.status_code)
        print("WEB RESPONSE:", r.text)

        return r.status_code == 200

    except Exception as e:
        print("ERROR REQUEST:", e)
        return False


@client.event
async def on_message(message):

    if message.author == client.user:
        return

    print("RECIBI:", repr(message.content))

    # =========================
    # REPORTE
    # =========================
    if message.content.startswith("!reporte"):

        try:
            lineas = message.content.splitlines()

            partida = int(lineas[0].replace("!reporte", "").strip())
            posicion = int(lineas[1].replace("Posicion:", "").strip())
            equipo = lineas[2].replace("Equipo:", "").strip()

            jugadores = []
            kills = []

            for linea in lineas[3:]:
                p = linea.split()
                if len(p) < 2:
                    continue

                try:
                    jugadores.append(p[0])
                    kills.append(int(p[1]))
                except:
                    continue

            data = {
                "equipo": equipo,
                "game": partida,
                "placement": posicion,
                "jugadores": jugadores,
                "kills": kills
            }

            ok = enviar(data, "/report")

            if ok:
                await message.channel.send(
                    f"✅ Reporte Guardado\n"
                    f"Equipo: {equipo}\n"
                    f"Partida: {partida}"
                )
            else:
                await message.channel.send("❌ Error enviando")

        except Exception as e:
            await message.channel.send(f"❌ Error formato\n{e}")

    # =========================
    # CORRECCIÓN COMPLETA
    # =========================
    if message.content.startswith("!corregir"):

        try:
            lineas = message.content.splitlines()

            equipo = lineas[1].replace("Equipo:", "").strip()
            partida = lineas[2].replace("Partida:", "").strip()
            posicion = int(lineas[3].replace("Posicion:", "").strip())

            jugadores = []
            kills = []

            for linea in lineas[4:]:
                p = linea.split()
                if len(p) < 2:
                    continue

                try:
                    jugadores.append(p[0])
                    kills.append(int(p[1]))
                except:
                    continue

            data = {
                "equipo": equipo,
                "game": partida,
                "placement": posicion,
                "jugadores": jugadores,
                "kills": kills
            }

            ok = enviar(data, "/corregir")

            if ok:
                await message.channel.send("✅ Corrección aplicada correctamente")
            else:
                await message.channel.send("❌ Error corrigiendo")

        except Exception as e:
            await message.channel.send(f"❌ Error formato\n{e}")


client.run(TOKEN)



