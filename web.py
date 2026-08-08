from flask import Flask, request, jsonify
import json
import os
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload


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

        print("==========================================")
        print("RESPALDO RESTAURADO DESDE GOOGLE DRIVE")
        print("==========================================")

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
        print("No se encontró TORNEOS MANYN.")
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
# DB SAFE
# ============================================================

def load():

    # Si existe data.json localmente, lo usamos.
    if os.path.exists(DB):

        try:

            with open(DB, "r", encoding="utf8") as f:

                return json.load(f)

        except Exception as e:

            print("ERROR leyendo data.json:")
            print(e)

            # Intentamos recuperar desde Google Drive
            restored = restore_from_drive()

            if restored:

                try:

                    with open(DB, "r", encoding="utf8") as f:
                        return json.load(f)

                except Exception:
                    pass

            return {"equipos": {}}

    # Si Render perdió data.json después de reiniciarse,
    # intentamos recuperarlo desde Google Drive.
    print("data.json no existe localmente.")
    print("Buscando respaldo en Google Drive...")

    restored = restore_from_drive()

    if restored:

        try:

            with open(DB, "r", encoding="utf8") as f:
                return json.load(f)

        except Exception as e:

            print("ERROR leyendo respaldo restaurado:")
            print(e)

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

    # Después de guardar localmente,
    # actualizamos el respaldo de Google Drive.
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
# REPORT MATCH
# ============================================================

@app.route("/report", methods=["POST"])
def report():

    body = request.json

    team = str(body.get("equipo", "")).strip()
    game = str(body.get("game", "")).strip()
    placement = int(body.get("placement", 0))

    players = body.get("jugadores", [])
    kills = body.get("kills", [])

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
# MODIFY MATCH
# ============================================================

@app.route("/modificar", methods=["POST"])
def modificar():

    body = request.json

    team = str(body.get("equipo", "")).strip()
    game = str(body.get("game", "")).strip()
    placement = int(body.get("placement", 0))

    players = body.get("jugadores", [])
    kills = body.get("kills", [])

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
# HOME WEB UI
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

    total_kills_global = 0

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

            total_kills_global += info["kills"]

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

    top_team = (
        ranking[0]["team"]
        if ranking
        else "-"
    )

    top_score = (
        ranking[0]["score"]
        if ranking
        else 0
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
    # HTML
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

    body {

        font-family: Arial, sans-serif;

        background: #f5f5f0;

        margin: 0;

        padding: 20px;

    }

    h1 {

        text-align: center;

        font-size: 34px;

    }

    h2 {

        text-align: center;

        margin-top: 45px;

    }

    table {

        width: 100%;

        border-collapse: collapse;

        margin-top: 20px;

        background: #eeeeee;

    }

    th,
    td {

        border: 1px solid #222;

        padding: 10px;

        text-align: center;

        font-weight: bold;

    }

    th {

        background: #d6ff00;

    }

    .duplicate-pos {

        background: red;

        color: white;

        font-weight: bold;

    }

    </style>

    </head>

    <body>

    <h1>TORNEOS MANYN</h1>

    """

    html += "<table><tr><th>POS</th><th>TEAM</th>"

    for g in allgames:

        color = (
            game_colors[int(g) % len(game_colors)]
            if str(g).isdigit()
            else "#00ff66"
        )

        html += (
            f"<th style='background:{color}'>"
            f"GAME {g}"
            f"</th>"

            f"<th style='background:{color}'>"
            f"POS"
            f"</th>"

            f"<th style='background:{color}'>"
            f"SCORE"
            f"</th>"
        )

    html += (
        "<th>TOTAL</th>"
        "<th>KILLS</th>"
        "</tr>"
    )

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
            f"<td>{medal} {pos}</td>"
            f"<td>{r['team']}</td>"
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
                    f"<td>{players_txt}</td>"

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
            f"<td>{r['score']}</td>"
            f"<td>{r['kills']}</td>"
            f"</tr>"
        )

        pos += 1

    html += "</table>"

    # ========================================================
    # FRAGGER TABLE
    # ========================================================

    html += (
        "<h2>🔥 FRAGGER TABLE</h2>"
        "<table>"
        "<tr>"
        "<th>POS</th>"
        "<th>PLAYER</th>"
        "<th>TEAM</th>"
        "<th>KILLS</th>"
        "</tr>"
    )

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
            f"<td>{medal} {ppos}</td>"
            f"<td>{p}</td>"
            f"<td>{s['team']}</td>"
            f"<td>{s['kills']}</td>"
            f"</tr>"
        )

        ppos += 1

    html += (
        "</table>"
        "</body>"
        "</html>"
    )

    return html


# ============================================================
# RUN - RENDER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
