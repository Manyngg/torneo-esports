from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

ARCHIVO = "data.json"

# =========================
# CARGAR DATOS
# =========================
def cargar_datos():
    if not os.path.exists(ARCHIVO):
        return []

    try:
        with open(ARCHIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# =========================
# GUARDAR DATOS
# =========================
def guardar_datos(datos):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# =========================
# PAGINA PRINCIPAL
# =========================
@app.route("/")
def home():
    datos = cargar_datos()

    html = """
    <html>
    <head>
        <title>Torneo Esports</title>
        <style>
            body{
                background:#111;
                color:white;
                font-family:Arial;
                text-align:center;
            }

            table{
                margin:auto;
                border-collapse:collapse;
                width:90%;
            }

            th,td{
                border:1px solid #444;
                padding:8px;
            }

            th{
                background:#222;
            }

            tr:nth-child(even){
                background:#1a1a1a;
            }
        </style>
    </head>
    <body>

    <h1>🏆 TORNEO ESPORTS</h1>

    <table>
        <tr>
            <th>Equipo</th>
            <th>Puesto</th>
            <th>Jugadores</th>
            <th>Kills</th>
            <th>Puntos</th>
        </tr>
    """

    for fila in datos:

        jugadores = ", ".join(fila.get("jugadores", []))
        kills = ", ".join(str(x) for x in fila.get("kills", []))

        html += f"""
        <tr>
            <td>{fila.get('equipo')}</td>
            <td>{fila.get('puesto')}</td>
            <td>{jugadores}</td>
            <td>{kills}</td>
            <td>{fila.get('puntos')}</td>
        </tr>
        """

    html += """
    </table>

    </body>
    </html>
    """

    return html

# =========================
# RECIBIR REPORTE
# =========================
@app.route("/report", methods=["POST"])
def report():

    try:

        body = request.json

        datos = cargar_datos()

        datos.append({
            "equipo": body.get("equipo"),
            "puesto": body.get("puesto"),
            "jugadores": body.get("jugadores"),
            "kills": body.get("kills"),
            "puntos": body.get("puntos")
        })

        guardar_datos(datos)

        return jsonify({
            "status": "ok"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

# =========================
# API DATOS
# =========================
@app.route("/data")
def data():

    return jsonify(cargar_datos())

# =========================
# INICIO
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)