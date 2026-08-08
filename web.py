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

            print("No existe todavía la carpeta TORNEOS MANYN.")

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
# DATABASE
# ============================================================

def load():

    if not os.path.exists(DB):

        print("data.json no existe localmente.")

        print("Buscando respaldo en Google Drive...")

        if restore_from_drive():

            try:

                with open(DB, "r", encoding="utf8") as f:

                    return json.load(f)

            except Exception:

                return {
                    "equipos": {}
                }

        return {
            "equipos": {}
        }

    try:

        with open(
            DB,
            "r",
            encoding="utf8"
        ) as f:

            return json.load(f)

    except Exception as e:

        print("ERROR leyendo data.json:")

        print(e)

        return {
            "equipos": {}
        }


def save(data):

    tmp = DB + ".tmp"

    with open(
        tmp,
        "w",
        encoding="utf8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

    os.replace(
        tmp,
        DB
    )

    backup_to_drive()


# ============================================================
# SCORE SYSTEM
# ============================================================

def calcular_score(
    placement,
    kills
):

    if placement == 1:

        mult = 1.6

    elif placement <= 5:

        mult = 1.4

    elif placement <= 10:

        mult = 1.2

    else:

        mult = 1

    return round(
        kills * mult,
        2
    )


# ============================================================
# REPORT
# ============================================================

@app.route(
    "/report",
    methods=["POST"]
)
def report():

    body = request.json

    team = str(
        body.get(
            "equipo",
            ""
        )
    ).strip()

    game = str(
        body.get(
            "game",
            ""
        )
    ).strip()

    placement = int(
        body.get(
            "placement",
            0
        )
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

            players[i]: int(
                kills[i]
            )

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

@app.route(
    "/modificar",
    methods=["POST"]
)
def modificar():

    body = request.json

    team = str(
        body.get(
            "equipo",
            ""
        )
    ).strip()

    game = str(
        body.get(
            "game",
            ""
        )
    ).strip()

    placement = int(
        body.get(
            "placement",
            0
        )
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

            players[i]: int(
                kills[i]
            )

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
# DELETE
# ============================================================

@app.route(
    "/borrar",
    methods=["POST"]
)
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

    equipos = db.get(
        "equipos",
        {}
    )

    allgames = sorted(
        {
            g
            for team in equipos
            for g in equipos[team].get(
                "games",
                {}
            )
        },
        key=lambda x: (
            int(x)
            if str(x).isdigit()
            else str(x)
        )
    )

    # ========================================================
    # DUPLICATE POSITIONS
    # ========================================================

    posiciones_por_game = {}

    for team, data in equipos.items():

        for g, info in data.get(
            "games",
            {}
        ).items():

            pos = info.get(
                "placement",
                0
            )

            posiciones_por_game.setdefault(
                g,
                {}
            )

            posiciones_por_game[g].setdefault(
                pos,
                0
            )

            posiciones_por_game[g][pos] += 1

    # ========================================================
    # RANKING
    # ========================================================

    ranking = []

    for team, data in equipos.items():

        score = 0

        kills = 0

        games = data.get(
            "games",
            {}
        )

        for g, info in games.items():

            score += float(
                info.get(
                    "score",
                    0
                )
            )

            kills += int(
                info.get(
                    "kills",
                    0
                )
            )

        ranking.append({

            "team": team,

            "score": round(
                score,
                2
            ),

            "kills": kills,

            "games": games

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

        for g, info in data.get(
            "games",
            {}
        ).items():

            for p, k in info.get(
                "players",
                {}
            ).items():

                if isinstance(
                    k,
                    dict
                ):

                    k = k.get(
                        "kills",
                        0
                    )

                if p not in fragger:

                    fragger[p] = {
                        "team": team,
                        "kills": 0
                    }

                fragger[p]["kills"] += int(k)

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

<html lang="es">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>TORNEOS MANYN</title>

<style>

/* ==========================================================
   BASE
   ========================================================== */

* {
    box-sizing: border-box;
}

html {
    background: #0d1113;
}

body {

    margin: 0;

    padding: 18px 12px 40px;

    background:
        radial-gradient(
            circle at 50% -20%,
            #263136 0%,
            #141a1c 34%,
            #0d1113 75%
        );

    color: #f4f4f4;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    min-height: 100vh;

}


/* ==========================================================
   TITLE
   ========================================================== */

.main-title {

    text-align: center;

    margin:
        5px 0
        22px;

    font-family:
        Impact,
        "Arial Black",
        Arial,
        sans-serif;

    font-size:
        clamp(
            34px,
            5vw,
            64px
        );

    letter-spacing: 5px;

    color: #ffffff;

    text-transform: uppercase;

    text-shadow:
        0 2px 0 #000000,
        0 0 8px rgba(
            255,
            255,
            255,
            0.25
        );

}


/* ==========================================================
   RANK CARD
   ========================================================== */

.rank-card {

    width: 100%;

    min-height: 185px;

    margin-bottom: 10px;

    display: grid;

    grid-template-columns:
        90px
        270px
        minmax(
            500px,
            1fr
        );

    gap: 0;

    background:
        linear-gradient(
            135deg,
            #20282b 0%,
            #1b2326 50%,
            #182023 100%
        );

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.06
        );

    border-radius: 20px;

    overflow: hidden;

    box-shadow:
        0 8px 22px
        rgba(
            0,
            0,
            0,
            0.65
        ),
        inset 0 1px 0
        rgba(
            255,
            255,
            255,
            0.035
        );

}


/* ==========================================================
   TOP 1 / 2 / 3 COLORS
   ========================================================== */

.rank-card.top1 {
    --accent: #ffd21a;
    --accent-dark: #a98200;
    --accent-bg: #26261a;
}

.rank-card.top2 {
    --accent: #8ee600;
    --accent-dark: #4f8700;
    --accent-bg: #1d2918;
}

.rank-card.top3 {
    --accent: #ff1493;
    --accent-dark: #9c0758;
    --accent-bg: #2a1823;
}

.rank-card.other {
    --accent: #9ca3a8;
    --accent-dark: #4b5155;
    --accent-bg: #202427;
}


/* ==========================================================
   RANK BOX
   ========================================================== */

.rank-box {

    background:
        linear-gradient(
            180deg,
            rgba(
                255,
                255,
                255,
                0.025
            ),
            rgba(
                0,
                0,
                0,
                0.10
            )
        );

    border-radius: 14px;

    margin: 7px;

    display: flex;

    flex-direction: column;

    align-items: center;

    justify-content: center;

    position: relative;

}


/* ==========================================================
   LABEL
   ========================================================== */

.rank-label {

    position: absolute;

    top: 0;
    left: 0;
    right: 0;

    height: 23px;

    display: flex;

    align-items: center;

    justify-content: center;

    background:
        var(--accent);

    color:
        #101010;

    font-size: 9px;

    font-weight: 900;

    letter-spacing: 0.5px;

    text-transform: uppercase;

    border-radius:
        13px 13px 0 0;

}


/* ==========================================================
   RANK NUMBER
   ========================================================== */

.rank-number {

    margin-top: 15px;

    font-size: 38px;

    line-height: 1;

    font-weight: 900;

    color:
        var(--accent);

    text-shadow:
        0 0 8px
        color-mix(
            in srgb,
            var(--accent) 35%,
            transparent
        );

}


/* ==========================================================
   POINTS
   ========================================================== */

.rank-points {

    margin-top: 17px;

    color:
        var(--accent);

    font-size: 16px;

    font-weight: 900;

}

.rank-points-label {

    color: #c4c9cc;

    font-size: 9px;

    margin-top: 1px;

}

.rank-kills {

    margin-top: 10px;

    color: #ffffff;

    font-size: 13px;

    font-weight: 800;

}

.rank-kills-label {

    color: #aeb5b8;

    font-size: 9px;

}


/* ==========================================================
   TEAM / PLAYERS
   ========================================================== */

.players-area {

    padding:
        15px 12px
        10px 12px;

    min-width: 0;

}


.player-header {

    display: grid;

    grid-template-columns:
        minmax(120px, 1fr)
        55px
        55px;

    color: #727b80;

    font-size: 8px;

    margin-bottom: 4px;

    text-transform: uppercase;

}


.player-row {

    display: grid;

    grid-template-columns:
        minmax(120px, 1fr)
        55px
        55px;

    height: 27px;

    align-items: center;

    border-bottom:
        1px solid
        rgba(
            255,
            255,
            255,
            0.05
        );

}


.player-name {

    color: #ffffff;

    font-size: 13px;

    font-weight: 800;

    letter-spacing: 0.4px;

}


.player-avg {

    color: #aab2b6;

    font-size: 11px;

    text-align: center;

}


.player-kills {

    color: #dfe3e5;

    font-size: 11px;

    text-align: center;

}


/* ==========================================================
   GAME AREA
   ========================================================== */

.games-area {

    padding:
        15px 10px
        10px 10px;

    overflow-x: auto;

}


/* ==========================================================
   GAMES GRID
   ========================================================== */

.games-grid {

    display: grid;

    grid-template-columns:
        repeat(
            var(--game-count),
            minmax(
                42px,
                1fr
            )
        );

    min-width:
        calc(
            var(--game-count) * 42px
        );

    gap: 3px;

}


/* ==========================================================
   GAME HEADERS
   ========================================================== */

.game-header {

    color: #727b80;

    font-size: 8px;

    text-align: center;

    margin-bottom: 5px;

}


/* ==========================================================
   GAME DATA
   ========================================================== */

.game-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--game-count),
            minmax(
                42px,
                1fr
            )
        );

    gap: 3px;

}


.game-column {

    min-width: 42px;

    text-align: center;

    color: #c8ced1;

    font-size: 9px;

}


.game-position {

    color: #f3f3f3;

    font-size: 10px;

    font-weight: 800;

}


.game-score {

    margin-top: 4px;

    color: #aeb7bb;

    font-size: 9px;

}


/* ==========================================================
   SUMMARY
   ========================================================== */

.summary-area {

    grid-column:
        2 / 4;

    border-top:
        1px solid
        rgba(
            255,
            255,
            255,
            0.08
        );

    margin:
        0 12px;

    padding:
        9px 0 10px;

    display: grid;

    grid-template-columns:
        220px
        1fr;

    align-items: center;

}


.summary-team {

    display: flex;

    align-items: center;

    gap: 10px;

}


.team-mark {

    width: 40px;

    height: 28px;

    border-radius: 8px;

    display: flex;

    align-items: center;

    justify-content: center;

    background:
        var(--accent-bg);

    color:
        var(--accent);

    font-size: 12px;

    font-weight: 900;

}


.summary-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--game-count),
            minmax(
                42px,
                1fr
            )
        );

    gap: 3px;

}


.summary-item {

    text-align: center;

    font-size: 9px;

    color: #9ca5a9;

}


.summary-label {

    color: #ffffff;

    font-weight: 800;

    font-size: 9px;

}


/* ==========================================================
   DUPLICATE
   ========================================================== */

.duplicate-pos {

    color: #ff4d4d !important;

    font-weight: 900;

    text-shadow:
        0 0 6px
        rgba(
            255,
            50,
            50,
            0.7
        );

}


/* ==========================================================
   FRAGGER SECTION
   ========================================================== */

.section-title {

    margin:
        32px 0 12px;

    text-align: center;

    font-family:
        "Arial Black",
        Arial,
        sans-serif;

    font-size: 24px;

    letter-spacing: 3px;

    color: #ffffff;

    text-shadow:
        0 0 10px
        rgba(
            255,
            20,
            147,
            0.55
        );

}


/* ==========================================================
   FRAGGER CARD
   ========================================================== */

.fragger-card {

    background:
        linear-gradient(
            135deg,
            #20282b,
            #171d20
        );

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.06
        );

    border-radius: 16px;

    overflow: hidden;

    box-shadow:
        0 7px 20px
        rgba(
            0,
            0,
            0,
            0.55
        );

}


.fragger-row {

    display: grid;

    grid-template-columns:
        55px
        minmax(
            180px,
            1fr
        )
        minmax(
            160px,
            1fr
        )
        90px;

    min-height: 39px;

    align-items: center;

    padding:
        0 15px;

    border-bottom:
        1px solid
        rgba(
            255,
            255,
            255,
            0.045
        );

}


.fragger-row.header {

    min-height: 32px;

    color: #777f83;

    font-size: 9px;

    text-transform: uppercase;

}


.fragger-pos {

    font-size: 14px;

    font-weight: 900;

}


.fragger-player {

    color: #ffffff;

    font-size: 12px;

    font-weight: 900;

}


.fragger-team {

    color: #9fa7ab;

    font-size: 11px;

}


.fragger-kills {

    color: #ffffff;

    font-size: 13px;

    font-weight: 900;

    text-align: right;

}


/* ==========================================================
   TOP 3 FRAGGER COLORS
   ========================================================== */

.fragger-row:nth-child(2)
.fragger-pos {

    color: #ffd21a;

}

.fragger-row:nth-child(3)
.fragger-pos {

    color: #8ee600;

}

.fragger-row:nth-child(4)
.fragger-pos {

    color: #ff1493;

}


/* ==========================================================
   SCROLLBAR
   ========================================================== */

.games-area::-webkit-scrollbar {

    height: 5px;

}

.games-area::-webkit-scrollbar-track {

    background: #111618;

}

.games-area::-webkit-scrollbar-thumb {

    background: #596166;

    border-radius: 10px;

}


/* ==========================================================
   RESPONSIVE
   ========================================================== */

@media (
    max-width: 1000px
) {

    body {

        padding:
            10px 6px 30px;

    }

    .rank-card {

        grid-template-columns:
            70px
            220px
            minmax(
                430px,
                1fr
            );

    }

    .player-name {

        font-size: 11px;

    }

}


@media (
    max-width: 700px
) {

    .main-title {

        font-size: 30px;

        letter-spacing: 3px;

    }

    .rank-card {

        grid-template-columns:
            70px
            210px
            minmax(
                420px,
                1fr
            );

        min-height: 170px;

    }

    .rank-number {

        font-size: 32px;

    }

    .player-row {

        height: 25px;

    }

    .player-name {

        font-size: 10px;

    }

    .player-avg,
    .player-kills {

        font-size: 9px;

    }

    .fragger-row {

        grid-template-columns:
            45px
            minmax(
                140px,
                1fr
            )
            minmax(
                120px,
                1fr
            )
            60px;

        padding:
            0 9px;

    }

}

</style>

</head>

<body>


<div class="main-title">

    TORNEOS MANYN

</div>

"""


    # ========================================================
    # RANK CARDS
    # ========================================================

    for pos, r in enumerate(
        ranking,
        start=1
    ):

        if pos == 1:

            rank_class = "top1"
            label = "WINNERS"

        elif pos == 2:

            rank_class = "top2"
            label = "MATCH POINT"

        elif pos == 3:

            rank_class = "top3"
            label = "TOP 3"

        else:

            rank_class = "other"
            label = "RANKING"

        medal = (

            "🥇"
            if pos == 1
            else
            "🥈"
            if pos == 2
            else
            "🥉"
            if pos == 3
            else
            ""

        )

        html += f"""

<div
    class="rank-card {rank_class}"
    style="--game-count:{max(len(allgames), 1)};"
>


    <!-- RANK -->

    <div class="rank-box">

        <div class="rank-label">

            {label}

        </div>

        <div class="rank-number">

            {medal} {pos}

        </div>

        <div class="rank-points">

            {r["score"]}

        </div>

        <div class="rank-points-label">

            Points

        </div>

        <div class="rank-kills">

            {r["kills"]}

        </div>

        <div class="rank-kills-label">

            Kills

        </div>

    </div>


    <!-- PLAYERS -->

    <div class="players-area">

        <div class="player-header">

            <div>PLAYER</div>
            <div>AVG KILLS</div>
            <div>KILLS</div>

        </div>

"""

        # Get players from all games
        player_stats = {}

        for g, info in r["games"].items():

            for p, k in info.get(
                "players",
                {}
            ).items():

                if isinstance(
                    k,
                    dict
                ):

                    k = k.get(
                        "kills",
                        0
                    )

                if p not in player_stats:

                    player_stats[p] = {
                        "kills": 0,
                        "games": 0
                    }

                player_stats[p]["kills"] += int(k)
                player_stats[p]["games"] += 1

        sorted_players = sorted(
            player_stats.items(),
            key=lambda x: x[1]["kills"],
            reverse=True
        )

        for p, stats in sorted_players[:3]:

            avg = (
                stats["kills"]
                /
                stats["games"]
                if stats["games"]
                else 0
            )

            html += f"""

        <div class="player-row">

            <div class="player-name">

                {p}

            </div>

            <div class="player-avg">

                {avg:.1f}

            </div>

            <div class="player-kills">

                {stats["kills"]}

            </div>

        </div>

"""

        # ====================================================
        # GAMES
        # ====================================================

        html += """

    </div>


    <div class="games-area">

        <div class="game-header">

"""

        for g in allgames:

            html += f"""

            <span>

                M{g}

            </span>

"""

        html += """

        </div>


        <div class="game-values">

"""

        for g in allgames:

            info = r["games"].get(
                g
            )

            if info:

                placement = info.get(
                    "placement",
                    "-"
                )

                score = info.get(
                    "score",
                    0
                )

                duplicate = ""

                if (
                    posiciones_por_game
                    .get(g, {})
                    .get(
                        placement,
                        0
                    ) > 1
                ):

                    duplicate = (
                        "duplicate-pos"
                    )

                html += f"""

            <div class="game-column">

                <div class="game-position {duplicate}">

                    {placement}

                </div>

                <div class="game-score">

                    {score}

                </div>

            </div>

"""

            else:

                html += """

            <div class="game-column">

                <div class="game-position">

                    -

                </div>

                <div class="game-score">

                    -

                </div>

            </div>

"""

        html += """

        </div>

    </div>


    <!-- SUMMARY -->

    <div class="summary-area">

        <div class="summary-team">

            <div class="team-mark">

                M

            </div>

            <div>

                <div
                    style="
                    color:#ffffff;
                    font-weight:900;
                    font-size:11px;
                    "
                >

                    TOTAL

                </div>

                <div
                    style="
                    color:#8f989c;
                    font-size:9px;
                    "
                >

                    RESULTADO GENERAL

                </div>

            </div>

        </div>

        <div class="summary-values">

"""

        for g in allgames:

            info = r["games"].get(
                g
            )

            if info:

                html += f"""

            <div class="summary-item">

                <div class="summary-label">

                    {info.get(
                        "kills",
                        0
                    )}

                </div>

                <div>

                    Kills

                </div>

            </div>

"""

            else:

                html += """

            <div class="summary-item">

                -

            </div>

"""

        html += """

        </div>

    </div>

</div>

"""


    # ========================================================
    # FRAGGER
    # ========================================================

    html += """

<div class="section-title">

    🔥 FRAGGER TABLE

</div>


<div class="fragger-card">


    <div class="fragger-row header">

        <div>POS</div>

        <div>PLAYER</div>

        <div>TEAM</div>

        <div style="text-align:right;">

            KILLS

        </div>

    </div>

"""

    ppos = 1

    for p, s in fraggers:

        medal = (

            "🥇"
            if ppos == 1
            else
            "🥈"
            if ppos == 2
            else
            "🥉"
            if ppos == 3
            else
            ""

        )

        html += f"""

    <div class="fragger-row">

        <div class="fragger-pos">

            {medal} {ppos}

        </div>

        <div class="fragger-player">

            {p}

        </div>

        <div class="fragger-team">

            {s["team"]}

        </div>

        <div class="fragger-kills">

            {s["kills"]}

        </div>

    </div>

"""

        ppos += 1

    html += """

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
