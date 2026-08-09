from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

DB = "data.json"


# ============================================================
# DATABASE
# ============================================================

def load():

    if not os.path.exists(DB):

        print("data.json no existe. Creando base nueva.")

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

    print("Base de datos guardada correctamente.")


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

    try:

        body = request.json or {}

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

        if not team:

            return jsonify({
                "ok": False,
                "error": "equipo vacío"
            }), 400

        if not game:

            return jsonify({
                "ok": False,
                "error": "game vacío"
            }), 400

        db = load()

        if team not in db["equipos"]:

            db["equipos"][team] = {
                "games": {}
            }

        total_kills = sum(
            int(k)
            for k in kills
        )

        db["equipos"][team]["games"][game] = {

            "placement": placement,

            "kills": total_kills,

            "score": calcular_score(
                placement,
                total_kills
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

    except Exception as e:

        print("ERROR en /report:")
        print(e)

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# ============================================================
# MODIFY MATCH
# ============================================================

@app.route(
    "/modificar",
    methods=["POST"]
)
def modificar():

    try:

        body = request.json or {}

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
                "ok": False,
                "error": "equipo no existe"
            }), 400

        if game not in db["equipos"][team]["games"]:

            return jsonify({
                "ok": False,
                "error": "partida no existe"
            }), 400

        total_kills = sum(
            int(k)
            for k in kills
        )

        db["equipos"][team]["games"][game] = {

            "placement": placement,

            "kills": total_kills,

            "score": calcular_score(
                placement,
                total_kills
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

    except Exception as e:

        print("ERROR en /modificar:")
        print(e)

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# ============================================================
# DELETE ALL
# ============================================================

@app.route(
    "/borrar",
    methods=["POST"]
)
def borrar():

    try:

        db = load()

        db["equipos"] = {}

        save(db)

        return jsonify({
            "ok": True
        })

    except Exception as e:

        print("ERROR en /borrar:")
        print(e)

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


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


    # ========================================================
    # ALL GAMES
    # ========================================================

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
content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"
>

<title>TORNEOS MANYN</title>


<style>

/* ============================================================
   COLORES PRINCIPALES
   ============================================================ */

:root {

    --bg:
        #101516;

    --card:
        #1b2426;

    --card-dark:
        #171e20;

    --card-light:
        #202a2c;

    --border:
        #303a3c;

    --yellow:
        #ffc400;

    --yellow-dark:
        #d9a700;

    --white:
        #f4f7f8;

    --text:
        #d8e0e2;

    --muted:
        #7f8c90;

    --muted-dark:
        #596569;

    --red:
        #ff3b30;

}


/* ============================================================
   RESET
   ============================================================ */

* {

    box-sizing:
        border-box;

}


html,
body {

    margin:
        0;

    padding:
        0;

    width:
        100%;

    min-height:
        100%;

}


body {

    background:
        var(--bg);

    color:
        var(--white);

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    overflow-x:
        hidden;

}


/* ============================================================
   CONTAINER
   ============================================================ */

.container {

    width:
        100%;

    max-width:
        1550px;

    margin:
        0 auto;

    padding:
        8px;

}


/* ============================================================
   TITLE
   ============================================================ */

.title {

    text-align:
        center;

    color:
        var(--yellow);

    font-size:
        20px;

    font-weight:
        1000;

    letter-spacing:
        1px;

    margin:
        2px 0 8px 0;

}


/* ============================================================
   RANK CARD
   ============================================================ */

.rank-card {

    width:
        100%;

    margin-bottom:
        7px;

    padding:
        7px 9px 6px 9px;

    background:
        var(--card);

    border:
        1px solid var(--border);

    border-radius:
        14px;

    box-shadow:
        0 5px 15px rgba(0,0,0,0.28);

    overflow:
        hidden;

}


/* ============================================================
   TOP 1
   ============================================================ */

.rank-card.top1 {

    border-color:
        #3b4446;

}


/* ============================================================
   TOP 2
   ============================================================ */

.rank-card.top2 {

    border-color:
        #343d3f;

}


/* ============================================================
   TOP 3
   ============================================================ */

.rank-card.top3 {

    border-color:
        #343d3f;

}


/* ============================================================
   RANK MAIN
   ============================================================ */

.rank-main {

    display:
        grid;

    grid-template-columns:
        78px
        minmax(250px, 1fr)
        minmax(360px, 1.8fr);

    gap:
        8px;

    align-items:
        stretch;

}


/* ============================================================
   RANK BOX
   ============================================================ */

.rank-box {

    min-height:
        115px;

    background:
        #20282a;

    border:
        1px solid #293335;

    border-radius:
        9px;

    display:
        flex;

    flex-direction:
        column;

    align-items:
        center;

    justify-content:
        center;

    position:
        relative;

}


/* ============================================================
   LABEL
   ============================================================ */

.rank-label {

    position:
        absolute;

    top:
        0;

    left:
        0;

    padding:
        3px 10px;

    background:
        var(--yellow);

    color:
        #151515;

    font-size:
        8px;

    font-weight:
        1000;

    border-radius:
        6px 0 6px 0;

}


/* ============================================================
   POSITION
   ============================================================ */

.rank-number {

    color:
        var(--yellow);

    font-size:
        30px;

    font-weight:
        1000;

    line-height:
        30px;

    margin-top:
        4px;

}


/* ============================================================
   RANK POINTS
   ============================================================ */

.rank-points {

    color:
        var(--yellow);

    font-size:
        16px;

    font-weight:
        1000;

    line-height:
        17px;

    margin-top:
        7px;

}


.rank-points-label {

    color:
        #d4dadd;

    font-size:
        7px;

    line-height:
        8px;

}


.rank-kills {

    color:
        var(--yellow);

    font-size:
        14px;

    font-weight:
        1000;

    line-height:
        15px;

    margin-top:
        7px;

}


.rank-kills-label {

    color:
        #d4dadd;

    font-size:
        7px;

    line-height:
        8px;

}


/* ============================================================
   TEAM AREA
   ============================================================ */

.team-area {

    min-width:
        0;

    padding:
        3px 4px;

}


/* ============================================================
   TEAM NAME
   ============================================================ */

.rank-team {

    color:
        var(--white);

    font-size:
        14px;

    font-weight:
        1000;

    line-height:
        17px;

    margin:
        1px 0 4px 0;

    white-space:
        nowrap;

    overflow:
        hidden;

    text-overflow:
        ellipsis;

}


/* ============================================================
   PLAYER HEADER
   ============================================================ */

.player-header {

    display:
        grid;

    grid-template-columns:
        minmax(120px, 1fr)
        55px
        48px
        48px
        48px;

    align-items:
        center;

    height:
        18px;

    padding:
        2px 4px;

    background:
        #151c1e;

    border-bottom:
        1px solid #30383a;

    color:
        var(--muted);

    font-size:
        6px;

    font-weight:
        900;

    line-height:
        7px;

}


/* ============================================================
   PLAYER ROW
   ============================================================ */

.player-row {

    display:
        grid;

    grid-template-columns:
        minmax(120px, 1fr)
        55px
        48px
        48px
        48px;

    align-items:
        center;

    height:
        21px;

    min-height:
        21px;

    padding:
        2px 4px;

    border-bottom:
        1px solid #2b3436;

    color:
        var(--text);

    font-size:
        8px;

    line-height:
        9px;

}


/* ============================================================
   PLAYER NAME
   ============================================================ */

.player-name {

    color:
        #ffffff;

    font-size:
        9px;

    font-weight:
        900;

    white-space:
        nowrap;

    overflow:
        hidden;

    text-overflow:
        ellipsis;

}


/* ============================================================
   PLAYER STATS
   ============================================================ */

.player-avg,
.player-kills,
.player-deaths,
.player-kd {

    text-align:
        center;

    color:
        #b9c4c7;

    font-size:
        8px;

    font-weight:
        700;

}


/* ============================================================
   GAME AREA
   ============================================================ */

.games-area {

    min-width:
        0;

    overflow:
        hidden;

}


/* ============================================================
   GAME HEADER
   ============================================================ */

.game-header {

    display:
        grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(24px, 1fr)
        );

    gap:
        1px;

    height:
        18px;

    align-items:
        center;

}


.game-header span {

    text-align:
        center;

    color:
        var(--muted);

    font-size:
        6px;

    line-height:
        7px;

    white-space:
        nowrap;

}


/* ============================================================
   GAME VALUES
   ============================================================ */

.game-values {

    display:
        grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(24px, 1fr)
        );

    gap:
        1px;

}


/* ============================================================
   GAME COLUMN
   ============================================================ */

.game-column {

    min-width:
        0;

    min-height:
        62px;

    padding:
        4px 2px;

    background:
        #1a2224;

    border:
        1px solid #293234;

    border-radius:
        4px;

    text-align:
        center;

}


/* ============================================================
   POSITION TITLE
   ============================================================ */

.game-position-title {

    color:
        var(--muted);

    font-size:
        5px;

    font-weight:
        900;

    line-height:
        6px;

    white-space:
        nowrap;

}


/* ============================================================
   POSITION
   ============================================================ */

.game-position {

    color:
        #ffffff;

    font-size:
        14px;

    font-weight:
        1000;

    line-height:
        16px;

    margin-top:
        2px;

}


/* ============================================================
   DUPLICATE
   ============================================================ */

.game-position.duplicate-pos {

    color:
        var(--red);

    background:
        rgba(255,59,48,0.13);

    border-radius:
        3px;

}


/* ============================================================
   SCORE TITLE
   ============================================================ */

.game-score-title {

    color:
        var(--muted);

    font-size:
        4px;

    font-weight:
        900;

    line-height:
        5px;

    margin-top:
        5px;

}


/* ============================================================
   SCORE
   ============================================================ */

.game-score {

    color:
        var(--yellow);

    font-size:
        9px;

    font-weight:
        1000;

    line-height:
        10px;

    margin-top:
        1px;

}


/* ============================================================
   SUMMARY
   ============================================================ */

.summary {

    display:
        grid;

    grid-template-columns:
        150px
        minmax(0, 1fr);

    gap:
        4px;

    margin-top:
        4px;

}


/* ============================================================
   SUMMARY TEAM
   ============================================================ */

.summary-team {

    display:
        flex;

    align-items:
        center;

    gap:
        7px;

    height:
        29px;

    padding:
        3px 6px;

    background:
        #151c1e;

    border:
        1px solid #293234;

    border-radius:
        5px;

}


/* ============================================================
   TEAM MARK
   ============================================================ */

.team-mark {

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    width:
        21px;

    height:
        21px;

    border-radius:
        4px;

    background:
        var(--yellow);

    color:
        #171717;

    font-size:
        8px;

    font-weight:
        1000;

}


/* ============================================================
   SUMMARY TEXT
   ============================================================ */

.summary-title {

    color:
        #ffffff;

    font-size:
        8px;

    font-weight:
        900;

    line-height:
        9px;

}


.summary-subtitle {

    color:
        var(--muted);

    font-size:
        5px;

    line-height:
        6px;

}


/* ============================================================
   SUMMARY VALUES
   ============================================================ */

.summary-values {

    display:
        grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(24px, 1fr)
        );

    gap:
        1px;

}


/* ============================================================
   SUMMARY ITEM
   ============================================================ */

.summary-item {

    min-height:
        29px;

    padding:
        3px 2px;

    background:
        #1a2224;

    border:
        1px solid #293234;

    border-radius:
        4px;

    text-align:
        center;

    color:
        var(--muted);

    font-size:
        5px;

    line-height:
        6px;

}


.summary-label {

    color:
        #dfe6e8;

    font-size:
        9px;

    font-weight:
        1000;

    line-height:
        10px;

}


/* ============================================================
   FRAGGER TITLE
   ============================================================ */

.fragger-title {

    margin:
        10px 0 4px 0;

    padding:
        6px 8px;

    background:
        #1b2426;

    border:
        1px solid #303a3c;

    border-left:
        4px solid var(--yellow);

    border-radius:
        6px;

    color:
        var(--yellow);

    font-size:
        11px;

    font-weight:
        1000;

}


/* ============================================================
   FRAGGER TABLE
   ============================================================ */

.fragger-row {

    display:
        grid;

    grid-template-columns:
        45px
        minmax(0, 1.5fr)
        minmax(0, 1fr)
        55px;

    align-items:
        center;

    height:
        22px;

    min-height:
        22px;

    padding:
        2px 6px;

    background:
        #1b2426;

    border-bottom:
        1px solid #2d3638;

    color:
        var(--text);

    font-size:
        8px;

}


.fragger-row.header {

    height:
        19px;

    min-height:
        19px;

    background:
        #151c1e;

    color:
        var(--muted);

    font-size:
        6px;

    font-weight:
        900;

}


/* ============================================================
   FRAGGER POS
   ============================================================ */

.fragger-pos {

    color:
        var(--yellow);

    font-size:
        9px;

    font-weight:
        1000;

}


/* ============================================================
   FRAGGER PLAYER
   ============================================================ */

.fragger-player {

    color:
        #ffffff;

    font-size:
        8px;

    font-weight:
        900;

    white-space:
        nowrap;

    overflow:
        hidden;

    text-overflow:
        ellipsis;

}


/* ============================================================
   FRAGGER TEAM
   ============================================================ */

.fragger-team {

    color:
        #8d9a9e;

    font-size:
        7px;

    white-space:
        nowrap;

    overflow:
        hidden;

    text-overflow:
        ellipsis;

}


/* ============================================================
   FRAGGER KILLS
   ============================================================ */

.fragger-kills {

    text-align:
        right;

    color:
        var(--yellow);

    font-size:
        9px;

    font-weight:
        1000;

}


/* ============================================================
   TABLET
   ============================================================ */

@media (max-width: 900px) {

    .rank-main {

        grid-template-columns:
            65px
            minmax(190px, 1fr)
            minmax(280px, 1.5fr);

    }

    .rank-box {

        min-height:
            105px;

    }

    .rank-number {

        font-size:
            25px;

    }

}


/* ============================================================
   MOBILE
   ============================================================ */

@media (max-width: 650px) {

    .container {

        padding:
            4px;

    }


    .title {

        font-size:
            16px;

        margin:
            1px 0 5px 0;

    }


    .rank-card {

        padding:
            4px;

        margin-bottom:
            5px;

        border-radius:
            9px;

    }


    .rank-main {

        display:
            grid;

        grid-template-columns:
            54px
            minmax(145px, 1fr)
            minmax(160px, 1.2fr);

        gap:
            3px;

    }


    .rank-box {

        min-height:
            91px;

        border-radius:
            6px;

    }


    .rank-label {

        padding:
            2px 5px;

        font-size:
            5px;

    }


    .rank-number {

        font-size:
            21px;

        line-height:
            22px;

    }


    .rank-points {

        font-size:
            12px;

        line-height:
            13px;

        margin-top:
            5px;

    }


    .rank-points-label {

        font-size:
            5px;

        line-height:
            6px;

    }


    .rank-kills {

        font-size:
            10px;

        line-height:
            11px;

        margin-top:
            4px;

    }


    .rank-kills-label {

        font-size:
            5px;

        line-height:
            6px;

    }


    .rank-team {

        font-size:
            10px;

        line-height:
            12px;

        margin:
            0 0 2px 0;

    }


    .player-header {

        grid-template-columns:
            minmax(70px, 1fr)
            36px
            32px
            32px
            32px;

        height:
            14px;

        padding:
            1px 2px;

        font-size:
            4px;

    }


    .player-row {

        grid-template-columns:
            minmax(70px, 1fr)
            36px
            32px
            32px
            32px;

        height:
            17px;

        min-height:
            17px;

        padding:
            1px 2px;

    }


    .player-name {

        font-size:
            6px;

    }


    .player-avg,
    .player-kills,
    .player-deaths,
    .player-kd {

        font-size:
            5.5px;

    }


    .game-header {

        height:
            14px;

    }


    .game-header span {

        font-size:
            4px;

    }


    .game-values {

        gap:
            1px;

    }


    .game-column {

        min-height:
            49px;

        padding:
            2px 1px;

    }


    .game-position-title {

        font-size:
            3.5px;

        line-height:
            4px;

    }


    .game-position {

        font-size:
            10px;

        line-height:
            11px;

    }


    .game-score-title {

        font-size:
            3px;

        line-height:
            3.5px;

        margin-top:
            3px;

    }


    .game-score {

        font-size:
            7px;

        line-height:
            8px;

    }


    .summary {

        grid-template-columns:
            105px
            minmax(0, 1fr);

        gap:
            2px;

        margin-top:
            2px;

    }


    .summary-team {

        height:
            22px;

        padding:
            2px 3px;

        gap:
            3px;

    }


    .team-mark {

        width:
            16px;

        height:
            16px;

        font-size:
            6px;

    }


    .summary-title {

        font-size:
            6px;

        line-height:
            7px;

    }


    .summary-subtitle {

        font-size:
            4px;

        line-height:
            4px;

    }


    .summary-item {

        min-height:
            22px;

        padding:
            2px 1px;

        font-size:
            4px;

    }


    .summary-label {

        font-size:
            7px;

        line-height:
            8px;

    }


    .fragger-title {

        margin:
            6px 0 2px 0;

        padding:
            4px 5px;

        font-size:
            9px;

        border-left-width:
            3px;

    }


    .fragger-row {

        grid-template-columns:
            30px
            minmax(0, 1.5fr)
            minmax(0, 1fr)
            35px;

        height:
            18px;

        min-height:
            18px;

        padding:
            1px 3px;

        font-size:
            6px;

    }


    .fragger-row.header {

        height:
            15px;

        min-height:
            15px;

        font-size:
            5px;

    }


    .fragger-pos {

        font-size:
            7px;

    }


    .fragger-player {

        font-size:
            6px;

    }


    .fragger-team {

        font-size:
            5px;

    }


    .fragger-kills {

        font-size:
            7px;

    }

}


/* ============================================================
   CELULARES MUY PEQUEÑOS
   ============================================================ */

@media (max-width: 430px) {

    .rank-main {

        grid-template-columns:
            48px
            minmax(125px, 1fr)
            minmax(140px, 1.15fr);

    }


    .rank-box {

        min-height:
            83px;

    }


    .rank-number {

        font-size:
            19px;

    }


    .rank-points {

        font-size:
            10px;

    }


    .rank-kills {

        font-size:
            9px;

    }


    .player-header {

        grid-template-columns:
            minmax(60px, 1fr)
            31px
            27px
            27px
            27px;

    }


    .player-row {

        grid-template-columns:
            minmax(60px, 1fr)
            31px
            27px
            27px
            27px;

    }


    .player-name {

        font-size:
            5.5px;

    }


    .player-avg,
    .player-kills,
    .player-deaths,
    .player-kd {

        font-size:
            5px;

    }


    .game-column {

        min-height:
            45px;

    }


    .game-position {

        font-size:
            9px;

    }


    .game-score {

        font-size:
            6.5px;

    }


    .summary {

        grid-template-columns:
            90px
            minmax(0, 1fr);

    }

}

</style>

</head>


<body>


<div class="container">

<div class="title">

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

            label = "GANADORES"


        elif pos == 2:

            rank_class = "top2"

            label = ""


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


        # ====================================================
        # PLAYER STATS
        # ====================================================

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


        # ====================================================
        # CARD
        # ====================================================

        html += f"""

<div class="rank-card {rank_class}">


<div class="rank-main">


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

            Puntos

        </div>


        <div class="rank-kills">

            {r["kills"]}

        </div>


        <div class="rank-kills-label">

            Kills

        </div>


    </div>


    <!-- TEAM / PLAYERS -->

    <div class="team-area">


        <div class="rank-team">

            {r["team"]}

        </div>


        <div class="player-header">


            <div>

                PLAYER

            </div>


            <div>

                AVG

            </div>


            <div>

                KILLS

            </div>


            <div>

                DEATHS

            </div>


            <div>

                K/D

            </div>


        </div>

"""


        # ====================================================
        # TOP 3 PLAYERS
        # ====================================================

        for p, stats in sorted_players[:3]:


            avg = (

                stats["kills"]
                /
                stats["games"]

                if stats["games"]

                else
                0

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


            <div class="player-deaths">

                -

            </div>


            <div class="player-kd">

                -

            </div>


        </div>

"""


        html += """

    </div>


    <!-- GAMES -->

    <div class="games-area">


"""


        # ====================================================
        # GAME HEADER
        # ====================================================

        games_count = max(
            len(allgames),
            1
        )


        html += f"""

        <div
            class="game-header"
            style="--games-count:{games_count};"
        >

"""


        for g in allgames:

            html += f"""

            <span>

                M{g}

            </span>

"""


        html += """

        </div>


        <div
            class="game-values"
            style="--games-count:{games_count};"
        >

"""


        # ====================================================
        # GAME CELLS
        # ====================================================

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
                    .get(
                        g,
                        {}
                    )
                    .get(
                        placement,
                        0
                    ) > 1

                ):

                    duplicate = "duplicate-pos"


                html += f"""

            <div class="game-column">


                <div class="game-position-title">

                    POSICIÓN

                </div>


                <div class="game-position {duplicate}">

                    {placement}

                </div>


                <div class="game-score-title">

                    RESULTADO CON<br>
                    MULTIPLICADOR

                </div>


                <div class="game-score">

                    {score}

                </div>


            </div>

"""


            else:


                html += """

            <div class="game-column">


                <div class="game-position-title">

                    POSICIÓN

                </div>


                <div class="game-position">

                    -

                </div>


                <div class="game-score-title">

                    RESULTADO CON<br>
                    MULTIPLICADOR

                </div>


                <div class="game-score">

                    -

                </div>


            </div>

"""


        html += """

        </div>

    </div>

</div>


<!-- ========================================================
     SUMMARY
     ======================================================== -->

<div class="summary">


    <div class="summary-team">


        <div class="team-mark">

            M

        </div>


        <div>

            <div class="summary-title">

                TOTAL

            </div>


            <div class="summary-subtitle">

                RESULTADO GENERAL

            </div>

        </div>


    </div>


    <div
        class="summary-values"
        style="--games-count:{games_count};"
    >

"""


        # ====================================================
        # SUMMARY VALUES
        # ====================================================

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


            <div class="summary-label">

                -

            </div>


            <div>

                Kills

            </div>


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

<div class="fragger-title">

    🔥 FRAGGER TABLE

</div>


<div class="fragger-row header">


    <div>

        POS

    </div>


    <div>

        PLAYER

    </div>


    <div>

        TEAM

    </div>


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


    # ========================================================
    # RETURN
    # ========================================================

    return html


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
