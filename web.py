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

    colores = ["#1f2937", "#111827", "#0f172a", "#1c1917"]

    html = """
    <html>
    <head>
        <title>TORNEOS MANYN ESPORTS</title>

        <style>
            body{
                background:#0b0f19;
                color:white;
                font-family:Arial;
                text-align:center;
            }

            .team-box{
                margin:30px auto;
                width:90%;
                border-radius:12px;
                padding:15px;
            }

            .team-title{
                font-size:26px;
                font-weight:bold;
                padding:10px;
                color:#ffd700;
            }

            table{
                margin:auto;
                border-collapse:collapse;
                width:100%;
            }

            th,td{
                border:1px solid #333;
                padding:10px;
            }

            th{
                background:#222;
            }

            .fragger-box{
                margin-top:10px;
                background:#111;
                padding:10px;
                border-radius:10px;
                border:1px solid #444;
            }

            .fragger-title{
                color:#ff4d4d;
                font-weight:bold;
            }
        </style>
    </head>

    <body>

    <h1>🏆 TORNEOS MANYN ESPORTS</h1>
    """

    i_color = 0

    for equipo, info in data.items():

        jugadores = info.get("jugadores", {})
        puntos = info.get("puntos", 0)

        sorted_players = sorted(jugadores.items(), key=lambda x: x[1], reverse=True)

        fragger = sorted_players[0] if sorted_players else ("", 0)

        bg = colores[i_color % len(colores)]
        i_color += 1

        html += f"""
        <div class="team-box" style="background:{bg}">
        
            <div class="team-title">{equipo} - PUNTOS: {puntos}</div>

            <table>
                <tr>
                    <th>Jugador</th>
                    <th>Kills</th>
                </tr>
        """

        for jugador, kills in sorted_players:
            html += f"""
                <tr>
                    <td>{jugador}</td>
                    <td>{kills}</td>
                </tr>
            """

        html += """
            </table>

            <div class="fragger-box">
                <div class="fragger-title">🔥 FRAGGER DEL EQUIPO</div>
        """

        html += f"""
                <div>{fragger[0]} con {fragger[1]} kills</div>
            </div>

        </div>
        """

    html += "</body></html>"

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
        data[equipo]["jugadores"][j] = data[equipo]["jugadores"].get(j, 0) + k

    guardar(data)

    return jsonify({"status": "ok"})

# =========================
@app.route("/data")
def data():
    return jsonify(cargar())

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
