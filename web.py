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

```
try:
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        return json.load(f)
except:
    return []
```

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

```
datos = cargar_datos()

html = """
<html>
<head>
    <title>TORNEOS MANYN ESPORTS</title>

    <style>
        body{
            background:#111;
            color:white;
            font-family:Arial;
            text-align:center;
            margin:20px;
        }

        h1{
            color:#ffd700;
        }

        table{
            margin:auto;
            border-collapse:collapse;
            width:95%;
        }

        th, td{
            border:1px solid #444;
            padding:10px;
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

<h1>🏆 TORNEOS MANYN ESPORTS</h1>

<table>
    <tr>
        <th>Equipo</th>
        <th>Puesto</th>

        <th>Jugador 1</th>
        <th>Kills</th>

        <th>Jugador 2</th>
        <th>Kills</th>

        <th>Jugador 3</th>
        <th>Kills</th>

        <th>Puntos</th>
    </tr>
"""

for fila in datos:

    jugadores = fila.get("jugadores", [])
    kills = fila.get("kills", [])

    j1 = jugadores[0] if len(jugadores) > 0 else ""
    j2 = jugadores[1] if len(jugadores) > 1 else ""
    j3 = jugadores[2] if len(jugadores) > 2 else ""

    k1 = kills[0] if len(kills) > 0 else 0
    k2 = kills[1] if len(kills) > 1 else 0
    k3 = kills[2] if len(kills) > 2 else 0

    html += f"""
    <tr>
        <td>{fila.get('equipo')}</td>
        <td>{fila.get('puesto')}</td>

        <td>{j1}</td>
        <td>{k1}</td>

        <td>{j2}</td>
        <td>{k2}</td>

        <td>{j3}</td>
        <td>{k3}</td>

        <td>{fila.get('puntos')}</td>
    </tr>
    """

html += """
</table>

</body>
</html>
"""

return html
```

# =========================

# RECIBIR REPORTE

# =========================

@app.route("/report", methods=["POST"])
def report():

```
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
```

# =========================

# VER DATOS JSON

# =========================

@app.route("/data")
def data():
return jsonify(cargar_datos())

# =========================

# INICIO

# =========================

if **name** == "**main**":
app.run(host="0.0.0.0", port=10000)
