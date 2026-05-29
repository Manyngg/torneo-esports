from flask import Flask
import pandas as pd

app = Flask(__name__)

ARCHIVO = "torneo.xlsx"

@app.route("/")
def home():

    try:
        df = pd.read_excel(ARCHIVO)

        # =========================
        # RANKING EQUIPOS
        # =========================

        equipos = {}

        for _, row in df.iterrows():

            equipo = str(row["Equipo"]).strip()

            puntos = float(row["Puntos"])

            equipos[equipo] = equipos.get(equipo, 0) + puntos

        ranking_equipos = sorted(
            equipos.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # =========================
        # FRAGGERS
        # =========================

        fraggers = {}

        for _, row in df.iterrows():

            jugadores = [
                (row["Jugador1"], row["Kills1"]),
                (row["Jugador2"], row["Kills2"]),
                (row["Jugador3"], row["Kills3"])
            ]

            for nombre, kills in jugadores:

                nombre = str(nombre).strip()

                kills = int(kills)

                fraggers[nombre] = fraggers.get(nombre, 0) + kills

        ranking_fraggers = sorted(
            fraggers.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # =========================
        # HTML
        # =========================

        html = f"""
        <html>

        <head>

        <title>TORNEO WARZONE</title>

        <meta http-equiv="refresh" content="10">

        <style>

        body{{
            background:#0b0b0b;
            color:white;
            font-family:Arial;
            margin:0;
            padding:40px;
        }}

        h1{{
            text-align:center;
            color:gold;
            font-size:50px;
            margin-bottom:40px;
        }}

        .container{{
            display:flex;
            gap:30px;
        }}

        .box{{
            flex:1;
            background:#161616;
            padding:20px;
            border-radius:15px;
            box-shadow:0 0 20px rgba(255,215,0,0.2);
        }}

        h2{{
            color:#00ffcc;
            text-align:center;
        }}

        table{{
            width:100%;
            border-collapse:collapse;
        }}

        th{{
            background:gold;
            color:black;
            padding:12px;
        }}

        td{{
            padding:10px;
            border-bottom:1px solid #333;
            text-align:center;
        }}

        tr:hover{{
            background:#222;
        }}

        .top1{{
            color:gold;
            font-weight:bold;
        }}

        </style>

        </head>

        <body>

        <h1>🏆 WARZONE TOURNAMENT</h1>

        <div class="container">

        <div class="box">

        <h2>🔥 RANKING EQUIPOS</h2>

        <table>

        <tr>
        <th>#</th>
        <th>Equipo</th>
        <th>Puntos</th>
        </tr>
        """

        for i, (equipo, pts) in enumerate(ranking_equipos):

            clase = "top1" if i == 0 else ""

            html += f"""
            <tr class="{clase}">
            <td>{i+1}</td>
            <td>{equipo}</td>
            <td>{pts:.1f}</td>
            </tr>
            """

        html += """
        </table>
        </div>

        <div class="box">

        <h2>🎯 TOP FRAGGERS</h2>

        <table>

        <tr>
        <th>#</th>
        <th>Jugador</th>
        <th>Kills</th>
        </tr>
        """

        for i, (jugador, kills) in enumerate(ranking_fraggers):

            clase = "top1" if i == 0 else ""

            html += f"""
            <tr class="{clase}">
            <td>{i+1}</td>
            <td>{jugador}</td>
            <td>{kills}</td>
            </tr>
            """

        html += """

        </table>

        </div>

        </div>

        </body>

        </html>
        """

        return html

    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)