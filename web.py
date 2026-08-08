```python
from flask import Flask, request, jsonify
import json
import os
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload


app = Flask(__name__)

DB = "data.json"

# ============================================================
# GOOGLE DRIVE
# ============================================================

GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")

DRIVE_FOLDER_NAME = "TORNEOS MANYN"
DRIVE_FILE_NAME = "data.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


def get_drive_service():

    if not GOOGLE_CREDENTIALS:
        print("ERROR: No existe GOOGLE_CREDENTIALS en Render.")
        return None

    try:

        credentials_info = json.loads(GOOGLE_CREDENTIALS)

        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=SCOPES
        )

        service = build(
            "drive",
            "v3",
            credentials=credentials,
            cache_discovery=False
        )

        return service

    except Exception as e:

        print("ERROR conectando con Google Drive:")
        print(e)

        return None


def find_drive_folder():

    service = get_drive_service()

    if service is None:
        return None

    try:

        query = (
            "name = '" + DRIVE_FOLDER_NAME + "' "
            "and mimeType = 'application/vnd.google-apps.folder' "
            "and trashed = false"
        )

        results = service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            pageSize=100
        ).execute()

        folders = results.get("files", [])

        if not folders:

            print("ERROR: No se encontró la carpeta TORNEOS MANYN.")

            return None

        folder_id = folders[0]["id"]

        print("Carpeta Google Drive encontrada:")
        print(DRIVE_FOLDER_NAME)
        print("ID:", folder_id)

        return folder_id

    except Exception as e:

        print("ERROR buscando carpeta de Google Drive:")
        print(e)

        return None


def find_drive_backup():

    service = get_drive_service()

    if service is None:
        return None

    folder_id = find_drive_folder()

    if folder_id is None:
        return None

    try:

        query = (
            "'" + folder_id + "' in parents "
            "and name = '" + DRIVE_FILE_NAME + "' "
            "and trashed = false"
        )

        results = service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name, modifiedTime)",
            orderBy="modifiedTime desc",
            pageSize=10
        ).execute()

        files = results.get("files", [])

        if not files:
            return None

        return files[0]["id"]

    except Exception as e:

        print("ERROR buscando respaldo:")
        print(e)

        return None


def restore_from_drive():

    service = get_drive_service()

    if service is None:
        return False

    file_id = find_drive_backup()

    if file_id is None:

        print("No existe todavía un respaldo en Google Drive.")

        return False

    try:

        request_drive = service.files().get_media(
            fileId=file_id
        )

        fh = io.BytesIO()

        downloader = MediaIoBaseDownload(
            fh,
            request_drive
        )

        done = False

        while not done:

            status, done = downloader.next_chunk()

        fh.seek(0)

        content = fh.read().decode("utf-8")

        data = json.loads(content)

        with open(DB, "w", encoding="utf8") as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

        print("RESPALDO RESTAURADO DESDE GOOGLE DRIVE")

        return True

    except Exception as e:

        print("ERROR restaurando respaldo:")
        print(e)

        return False


def backup_to_drive():

    service = get_drive_service()

    if service is None:

        print("No se pudo conectar con Google Drive.")

        return False

    folder_id = find_drive_folder()

    if folder_id is None:

        return False

    try:

        with open(DB, "rb") as f:

            file_content = f.read()

        media = MediaIoBaseUpload(
            io.BytesIO(file_content),
            mimetype="application/json",
            resumable=False
        )

        existing_file_id = find_drive_backup()

        if existing_file_id:

            service.files().update(
                fileId=existing_file_id,
                media_body=media
            ).execute()

            print("Respaldo actualizado en Google Drive.")

        else:

            file_metadata = {
                "name": DRIVE_FILE_NAME,
                "parents": [folder_id]
            }

            service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()

            print("Primer respaldo creado en Google Drive.")

        return True

    except Exception as e:

        print("ERROR creando respaldo:")
        print(e)

        return False


# ============================================================
# DB
# ============================================================

def load():

    if os.path.exists(DB):

        try:

            with open(DB, "r", encoding="utf8") as f:

                return json.load(f)

        except Exception as e:

            print("ERROR leyendo data.json:")
            print(e)

            return {"equipos": {}}

    print("data.json no existe localmente.")

    return {"equipos": {}}


def save(data):

    tmp = DB + ".tmp"

    with open(tmp, "w", encoding="utf8") as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

    os.replace(tmp, DB)

    backup_to_drive()


# ============================================================
# SCORE SYSTEM
# ============================================================

def calcular_score(placement, kills):

    if placement == 1:

        mult = 1.6

    elif placement <= 5:

        mult = 1.4

    elif placement <= 10:

        mult = 1.2

    else:

        mult = 1

    return round(kills * mult, 2)


# ============================================================
# REPORT
# ============================================================

@app.route("/report", methods=["POST"])
def report():

    body = request.json

    team = str(body.get("equipo", "")).strip()
    game = str(body.get("game", "")).strip()

    placement = int(
        body.get("placement", 0)
    )

    players = body.get(
        "jugadores",
        []
    )

    kills = body.get(
        "kills",
        []
    )

    db = load()

    if team not in db["equipos"]:

        db["equipos"][team] = {
            "games": {}
        }

    db["equipos"][team]["games"][game] = {

        "placement": placement,

        "kills": sum(kills),

        "score": calcular_score(
            placement,
            sum(kills)
        ),

        "players": {

            players[i]: int(kills[i])

            for i in range(
                min(
                    len(players),
                    len(kills)
                )
            )

        }

    }

    save(db)

    return jsonify({
        "ok": True
    })


# ============================================================
# MODIFY
# ============================================================

@app.route("/modificar", methods=["POST"])
def modificar():

    body = request.json

    team = str(body.get("equipo", "")).strip()
    game = str(body.get("game", "")).strip()

    placement = int(
        body.get("placement", 0)
    )

    players = body.get(
        "jugadores",
        []
    )

    kills = body.get(
        "kills",
        []
    )

    db = load()

    if team not in db["equipos"]:

        return jsonify({
            "error": "equipo no existe"
        }), 400

    if game not in db["equipos"][team]["games"]:

        return jsonify({
            "error": "partida no existe"
        }), 400

    db["equipos"][team]["games"][game] = {

        "placement": placement,

        "kills": sum(kills),

        "score": calcular_score(
            placement,
            sum(kills)
        ),

        "players": {

            players[i]: int(kills[i])

            for i in range(
                min(
                    len(players),
                    len(kills)
                )
            )

        }

    }

    save(db)

    return jsonify({
        "ok": True
    })


# ============================================================
# BORRAR
# ============================================================

@app.route("/borrar", methods=["POST"])
def borrar():

    db = load()

    db["equipos"] = {}

    save(db)

    return jsonify({
        "ok": True
    })


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    db = load()

    equipos = db["equipos"]

    allgames = sorted(
        {
            g
            for t in equipos
            for g in equipos[t]["games"]
        }
    )

    ranking = []

    posiciones_por_game = {}

    for team, data in equipos.items():

        for g, info in data["games"].items():

            pos = info["placement"]

            posiciones_por_game.setdefault(
                g,
                {}
            )

            posiciones_por_game[g].setdefault(
                pos,
                0
            )

            posiciones_por_game[g][pos] += 1

    for team, data in equipos.items():

        score = 0
        kills = 0

        for g, info in data["games"].items():

            score += info["score"]
            kills += info["kills"]

        ranking.append({

            "team": team,

            "score": round(
                score,
                2
            ),

            "kills": kills,

            "games": data["games"]

        })

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # ========================================================
    # FRAGGER
    # ========================================================

    fragger = {}

    for team, data in equipos.items():

        for g, info in data["games"].items():

            for p, k in info["players"].items():

                fragger[p] = fragger.get(
                    p,
                    {
                        "team": team,
                        "kills": 0
                    }
                )

                fragger[p]["kills"] += k

    fraggers = sorted(
        fragger.items(),
        key=lambda x: x[1]["kills"],
        reverse=True
    )

    # ========================================================
    # COLORES GAMES
    # ========================================================

    game_colors = [
        "#a855f7",
        "#c026d3",
        "#7c3aed",
        "#9333ea",
        "#d946ef",
        "#8b5cf6"
    ]

    # ========================================================
    # HTML + CSS NEON ESPORTS
    # ========================================================

    html = """
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>TORNEOS MANYN</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    padding: 18px;

    background:
        radial-gradient(
            circle at top,
            #241044 0%,
            #10091c 32%,
            #050508 75%
        );

    color: #ffffff;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    min-height: 100vh;

}

/* ==========================================================
   TITLE
   ========================================================== */

.title {

    text-align: center;

    margin: 8px 0 22px 0;

    font-family:
        "Arial Black",
        Arial,
        sans-serif;

    font-size: clamp(
        30px,
        4vw,
        58px
    );

    font-weight: 900;

    letter-spacing: 5px;

    text-transform: uppercase;

    color: #ffffff;

    text-shadow:
        0 0 5px #ffffff,
        0 0 12px #a855f7,
        0 0 25px #a855f7,
        0 0 45px #7c3aed;

}

/* ==========================================================
   TABLE CONTAINER
   ========================================================== */

.table-wrap {

    width: 100%;

    overflow-x: auto;

    padding: 8px 5px 15px 5px;

}

/* ==========================================================
   TABLE
   ========================================================== */

table {

    border-collapse: separate;

    border-spacing: 5px;

    width: max-content;

    min-width: 100%;

}

/* ==========================================================
   CELLS
   ========================================================== */

th,
td {

    border: 1px solid rgba(
        168,
        85,
        247,
        0.55
    );

    border-radius: 8px;

    padding: 5px 7px;

    text-align: center;

    white-space: nowrap;

    font-weight: 700;

}

/* ==========================================================
   HEADERS
   ========================================================== */

th {

    background:
        linear-gradient(
            145deg,
            #6d28d9,
            #3b0764
        );

    color: #ffffff;

    font-size: 11px;

    letter-spacing: 0.6px;

    box-shadow:
        0 3px 10px rgba(
            168,
            85,
            247,
            0.35
        );

}

/* ==========================================================
   NORMAL CELLS
   ========================================================== */

td {

    background:
        linear-gradient(
            145deg,
            #17121f,
            #0d0a12
        );

    font-size: 11px;

    box-shadow:
        0 3px 9px rgba(
            0,
            0,
            0,
            0.75
        ),
        0 0 5px rgba(
            168,
            85,
            247,
            0.10
        );

    transition:
        transform 0.15s ease,
        box-shadow 0.15s ease;

}

/* ==========================================================
   FLOATING EFFECT
   ========================================================== */

tbody tr:hover td {

    transform:
        translateY(-2px);

    box-shadow:
        0 7px 16px rgba(
            0,
            0,
            0,
            0.9
        ),
        0 0 10px rgba(
            168,
            85,
            247,
            0.40
        );

}

/* ==========================================================
   TEAM COLUMN
   ========================================================== */

td:nth-child(2) {

    color: #e9d5ff;

    font-size: 12px;

    letter-spacing: 0.3px;

}

/* ==========================================================
   POS
   ========================================================== */

td:first-child {

    color: #d8b4fe;

    font-size: 12px;

    min-width: 42px;

}

/* ==========================================================
   DUPLICATE POSITIONS
   ========================================================== */

.duplicate-pos {

    background:
        linear-gradient(
            145deg,
            #7f1d1d,
            #450a0a
        ) !important;

    color: #ffffff !important;

    border-color: #ef4444 !important;

    box-shadow:
        0 0 8px rgba(
            239,
            68,
            68,
            0.75
        ) !important;

}

/* ==========================================================
   SECTION TITLES
   ========================================================== */

.section-title {

    margin-top: 35px;

    margin-bottom: 5px;

    text-align: center;

    font-size: 21px;

    letter-spacing: 2px;

    color: #e9d5ff;

    text-shadow:
        0 0 8px #a855f7,
        0 0 18px #7c3aed;

}

/* ==========================================================
   FRAGGER
   ========================================================== */

.fragger-table th {

    background:
        linear-gradient(
            145deg,
            #9333ea,
            #4c1d95
        );

}

.fragger-table td {

    font-size: 12px;

}

.fragger-table td:nth-child(2) {

    color: #f5d0fe;

    font-weight: 900;

}

/* ==========================================================
   SCROLLBAR
   ========================================================== */

.table-wrap::-webkit-scrollbar {

    height: 7px;

}

.table-wrap::-webkit-scrollbar-track {

    background: #09070d;

    border-radius: 10px;

}

.table-wrap::-webkit-scrollbar-thumb {

    background:
        linear-gradient(
            90deg,
            #7c3aed,
            #d946ef
        );

    border-radius: 10px;

}

/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 800px) {

    body {

        padding: 8px;

    }

    .title {

        font-size: 29px;

        letter-spacing: 3px;

        margin-bottom: 12px;

    }

    table {

        border-spacing: 3px;

    }

    th,
    td {

        padding: 4px 5px;

        font-size: 9px;

    }

    td:nth-child(2) {

        font-size: 10px;

    }

    .section-title {

        font-size: 18px;

    }

}

</style>

</head>

<body>

<div class="title">
TORNEOS MANYN
</div>

"""

    # ========================================================
    # GENERAL TABLE
    # ========================================================

    html += """
<div class="table-wrap">

<table>

<thead>

<tr>

<th>POS</th>

<th>TEAM</th>

"""

    for g in allgames:

        color = (
            game_colors[
                int(g) % len(game_colors)
            ]
            if str(g).isdigit()
            else "#9333ea"
        )

        html += (

            f"<th style='background:"
            f"linear-gradient(145deg,"
            f"{color},#26063d);'>"
            f"GAME {g}"
            f"</th>"

            f"<th style='background:"
            f"linear-gradient(145deg,"
            f"{color},#26063d);'>"
            f"POS"
            f"</th>"

            f"<th style='background:"
            f"linear-gradient(145deg,"
            f"{color},#26063d);'>"
            f"SCORE"
            f"</th>"

        )

    html += """

<th>TOTAL</th>

<th>KILLS</th>

</tr>

</thead>

<tbody>

"""

    pos = 1

    for r in ranking:

        medal = (

            "🥇"
            if pos == 1
            else "🥈"
            if pos == 2
            else "🥉"
            if pos == 3
            else ""

        )

        html += (

            f"<tr>"

            f"<td>"
            f"{medal} {pos}"
            f"</td>"

            f"<td>"
            f"{r['team']}"
            f"</td>"

        )

        for g in allgames:

            if g in r["games"]:

                game = r["games"][g]

                cls = ""

                if (
                    g in posiciones_por_game
                    and posiciones_por_game[g].get(
                        game["placement"],
                        0
                    ) > 1
                ):

                    cls = "duplicate-pos"

                players_txt = ""

                for p, k in game["players"].items():

                    players_txt += (
                        f"{p}: {k}<br>"
                    )

                html += (

                    f"<td>"
                    f"{players_txt}"
                    f"</td>"

                    f"<td class='{cls}'>"
                    f"{game['placement']}"
                    f"</td>"

                    f"<td>"
                    f"{game['score']}"
                    f"</td>"

                )

            else:

                html += (

                    "<td>-</td>"
                    "<td>-</td>"
                    "<td>-</td>"

                )

        html += (

            f"<td>"
            f"{r['score']}"
            f"</td>"

            f"<td>"
            f"{r['kills']}"
            f"</td>"

            f"</tr>"

        )

        pos += 1

    html += """

</tbody>

</table>

</div>

"""

    # ========================================================
    # FRAGGER TABLE
    # ========================================================

    html += """

<div class="section-title">

🔥 FRAGGER TABLE

</div>

<div class="table-wrap">

<table class="fragger-table">

<thead>

<tr>

<th>POS</th>

<th>PLAYER</th>

<th>TEAM</th>

<th>KILLS</th>

</tr>

</thead>

<tbody>

"""

    ppos = 1

    for p, s in fraggers:

        medal = (

            "🥇"
            if ppos == 1
            else "🥈"
            if ppos == 2
            else "🥉"
            if ppos == 3
            else ""

        )

        html += (

            f"<tr>"

            f"<td>"
            f"{medal} {ppos}"
            f"</td>"

            f"<td>"
            f"{p}"
            f"</td>"

            f"<td>"
            f"{s['team']}"
            f"</td>"

            f"<td>"
            f"{s['kills']}"
            f"</td>"

            f"</tr>"

        )

        ppos += 1

    html += """

</tbody>

</table>

</div>

</body>

</html>

"""

    return html


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
```
