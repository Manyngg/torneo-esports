from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

ARCHIVO = "data.json"

# =========================
def cargar():
    if not os.path.exists(ARCHIVO):
        return {}
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# =========================
def guardar(data):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# =========================
@app.route("/")
def home():
    data = cargar()

    jugadores_global = {}

    # =========================
    # APLANAR TODOS LOS EQUIPOS
    # =========================
    for equipo, info in data.items():
        for jugador, stats in info.get("jugadores", {}).items():

            if jugador not in jugadores_global:
                jugadores_global[jugador] = {
                    "kills": 0,
                    "partidas": 0,
                    "equipo": equipo
                }

            jugadores_global[jugador]["kills"] += stats.get("kills", 0)
            jugadores_global[jugador]["partidas"] += stats.get("partidas", 0)

    # =========================
    # FRAGGER GLOBAL
    # =========================
    fragger = max(jugadores_global.items(), key=lambda x: x[1]["kills"], default=(None, None))

    # ordenar ranking
    ranking = sorted(jugadores_global.items(), key=lambda x: x[1]["kills"], reverse=True)

    html = """
    <html>
    <head>
        <title>TORNEO MANYN ESPORTS</title>

        <style>
            body{
                background:#0b0f19;
                color:white;
                font-family:Arial;
                text-align:center;
            }

            table{
                margin:auto;
                border-collapse:collapse;
                width:85%;
            }

            th,td{
                border:1px solid #333;
                padding:10px;
            }

            th{
                background:#222;
            }

            .fragger{
                margin:20px auto;
                padding:15px;
                width:60%;
                background:#111;
                border:1px solid #444;
                border-radius:10px;
                color:#ff4d4d;
                font-size:18px;
            }
        </style>
    </head>

    <body>

    <h1>🏆 TORNEO MANYN ESPORTS</h1>
    """

    # =========================
    # FRAGGER GLOBAL
    # =========================
    if fragger[0]:
        html += f"""
        <div class="fragger">
            🔥 FRAGGER GLOBAL: <b>{fragger[0]}</b> con <b>{fragger[1]['kills']}</b> kills
        </div>
        """

    # =========================
    # TABLA GLOBAL
    # =========================
    html += """
    <table>
        <tr>
            <th>Jugador</th>
            <th>Equipo</th>
            <th>Kills</th>
            <th>Partidas</th>
        </tr>
    """

    for jugador, stats in ranking:
        html += f"""
        <tr>
            <td>{jugador}</td>
            <td>{stats['equipo']}</td>
            <td>{stats['kills']}</td>
            <td>{stats['partidas']}</td>
        </tr>
        """

    html += "</table></body></html>"

    return html

# =========================
@app.route("/report", methods=["POST"])
def report():
    body = request.json

    equipo = body.get("equipo")
    puesto = int(body.get("puesto"))
    jugadores = body.get("jugadores")
    kills = body.get("kills")

    puntos_base = (25 - puesto) + sum(kills)

    data = cargar()

    if equipo not in data:
        data[equipo] = {
            "puntos": 0,
            "jugadores": {}
        }

    data[equipo]["puntos"] += puntos_base

    for i in range(len(jugadores)):
        j = jugadores[i]
        k = kills[i]

        if j not in data[equipo]["jugadores"]:
            data[equipo]["jugadores"][j] = {
                "kills": 0,
                "partidas": 0
            }

        data[equipo]["jugadores"][j]["kills"] += k
        data[equipo]["jugadores"][j]["partidas"] += 1

    guardar(data)

    return jsonify({"status": "ok"})

# =========================
@app.route("/data")
def data():
    return jsonify(cargar())

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
