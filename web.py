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
    # HTML + CSS
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


/* =========================================================
   GENERAL
   ========================================================= */

* {
    box-sizing: border-box;
}


body {

    margin: 0;

    padding: 14px;

    background: #eee9df;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    color: #111;

}


.page {

    width: 100%;

    max-width: 1500px;

    margin: auto;

}


.main-title {

    text-align: center;

    font-size: 28px;

    font-weight: 900;

    letter-spacing: 2px;

    margin-bottom: 18px;

}


/* =========================================================
   RANKING GRID
   ========================================================= */

.ranking-grid {

    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        minmax(0, 1fr);

    gap: 14px;

    align-items: start;

}


/*
   IZQUIERDA = TOP 10 EN ADELANTE
   DERECHA = TOP 1 AL TOP 9
*/

.ranking-left,
.ranking-right {

    display: flex;

    flex-direction: column;

    gap: 14px;

}


/* =========================================================
   CARD
   ========================================================= */

.team-card {

    width: 100%;

    background: #dedede;

    border-radius: 14px;

    overflow: hidden;

    box-shadow:
        0 4px 10px rgba(0,0,0,.20);

}


/* =========================================================
   TOP 1
   ========================================================= */

.team-card.top1 {

    border: 3px solid #d7ff00;

    background:
        linear-gradient(
            135deg,
            #d7ff00 0%,
            #f3ff83 42%,
            #d7ff00 100%
        );

}


/* =========================================================
   TOP 2
   ========================================================= */

.team-card.top2 {

    border: 3px solid #c9c9c9;

    background:
        linear-gradient(
            135deg,
            #bcbcbc 0%,
            #f2f2f2 45%,
            #bdbdbd 100%
        );

}


/* =========================================================
   TOP 3
   ========================================================= */

.team-card.top3 {

    border: 3px solid #ff9b19;

    background:
        linear-gradient(
            135deg,
            #ff9b19 0%,
            #ffd28a 45%,
            #ff9b19 100%
        );

}


/* =========================================================
   OTHER
   ========================================================= */

.team-card.other {

    border: 2px solid #bfbfbf;

    background: #e2e2e2;

}


/* =========================================================
   RANK HEADER
   ========================================================= */

.rank-box {

    display: grid;

    grid-template-columns:
        70px
        minmax(80px, 1fr)
        90px;

    align-items: center;

    min-height: 72px;

    padding: 8px 12px;

    gap: 8px;

}


.rank-number {

    font-size: 28px;

    font-weight: 900;

    text-align: center;

    white-space: nowrap;

}


.rank-points-box {

    text-align: center;

}


.rank-points {

    font-size: 25px;

    font-weight: 900;

    line-height: 1;

}


.rank-points-label {

    font-size: 10px;

    font-weight: 800;

    text-transform: uppercase;

}


.rank-kills-box {

    text-align: center;

}


.rank-kills {

    font-size: 25px;

    font-weight: 900;

    line-height: 1;

}


.rank-kills-label {

    font-size: 10px;

    font-weight: 800;

    text-transform: uppercase;

}


/* =========================================================
   TEAM NAME
   ========================================================= */

.team-area {

    padding: 0 10px 10px;

}


.rank-team {

    text-align: center;

    font-size: 21px;

    font-weight: 1000;

    text-transform: uppercase;

    letter-spacing: .7px;

    padding: 9px 5px 10px;

    border-top: 2px solid rgba(0,0,0,.18);

    border-bottom: 2px solid rgba(0,0,0,.18);

    margin-bottom: 7px;

    overflow-wrap: anywhere;

}


/* =========================================================
   PLAYER HEADER
   ========================================================= */

.player-header {

    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        58px
        62px;

    align-items: center;

    background: rgba(255,255,255,.45);

    border-radius: 7px;

    min-height: 31px;

    font-size: 10px;

    font-weight: 900;

    text-align: center;

}


.player-header div:first-child {

    text-align: left;

    padding-left: 8px;

}


/* =========================================================
   PLAYER ROW
   ========================================================= */

.player-row {

    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        58px
        62px;

    align-items: center;

    min-height: 32px;

    border-bottom: 1px solid rgba(0,0,0,.12);

}


.player-row:last-child {

    border-bottom: none;

}


.player-name {

    font-size: 13px;

    font-weight: 800;

    padding-left: 8px;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

}


.player-avg,
.player-kills {

    text-align: center;

    font-size: 13px;

    font-weight: 900;

}


/* =========================================================
   GAMES
   ========================================================= */

.games-area {

    margin-top: 9px;

    padding: 9px;

    background: rgba(0,0,0,.08);

    border-radius: 9px;

    overflow-x: auto;

}


.game-header {

    display: grid;

    grid-template-columns:
        repeat(var(--games-count), minmax(85px, 1fr));

    min-width: max-content;

    gap: 5px;

    margin-bottom: 5px;

}


.game-header span {

    text-align: center;

    font-size: 12px;

    font-weight: 1000;

    padding: 5px;

    border-radius: 5px;

    background: #c8ff00;

}


/* =========================================================
   GAME VALUES
   ========================================================= */

.game-values {

    display: grid;

    grid-template-columns:
        repeat(var(--games-count), minmax(85px, 1fr));

    min-width: max-content;

    gap: 5px;

}


/* Cada M1 M2 M3 permanece en su propia columna */

.game-column {

    min-width: 85px;

    background: #f1f1f1;

    border-radius: 7px;

    overflow: hidden;

    text-align: center;

    border: 1px solid #c8c8c8;

}


.game-position-title,
.game-score-title {

    font-size: 8px;

    font-weight: 900;

    padding: 4px 2px;

    background: #d9d9d9;

}


.game-position {

    font-size: 20px;

    font-weight: 1000;

    padding: 5px;

}


.game-score {

    font-size: 15px;

    font-weight: 1000;

    padding: 6px;

    background: #e8ff65;

}


.duplicate-pos {

    background: #ff3b30 !important;

    color: white;

}


/* =========================================================
   SUMMARY
   ========================================================= */

.summary-team {

    display: flex;

    align-items: center;

    gap: 8px;

    margin-top: 8px;

    padding: 7px;

    border-radius: 8px;

    background: #d4d4d4;

}


.team-mark {

    width: 31px;

    height: 31px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 50%;

    background: #c8ff00;

    font-weight: 1000;

}


.summary-title {

    font-size: 12px;

    font-weight: 1000;

}


.summary-subtitle {

    font-size: 8px;

    font-weight: 700;

}


.summary-values {

    display: grid;

    grid-template-columns:
        repeat(var(--games-count), minmax(85px, 1fr));

    min-width: max-content;

    gap: 5px;

    margin-top: 5px;

}


.summary-item {

    text-align: center;

    background: #e2e2e2;

    border-radius: 6px;

    padding: 5px;

    font-size: 9px;

    font-weight: 800;

}


.summary-label {

    font-size: 18px;

    font-weight: 1000;

}


/* =========================================================
   FRAGGER
   ========================================================= */

.fragger-section {

    margin-top: 25px;

    background: #dedede;

    border-radius: 12px;

    padding: 12px;

    box-shadow:
        0 4px 10px rgba(0,0,0,.18);

}


.fragger-title {

    text-align: center;

    font-size: 21px;

    font-weight: 1000;

    margin-bottom: 10px;

}


.fragger-header,
.fragger-row {

    display: grid;

    grid-template-columns:
        55px
        minmax(0, 1fr)
        minmax(0, 1fr)
        65px;

    align-items: center;

    gap: 5px;

}


.fragger-header {

    background: #c8ff00;

    border-radius: 6px;

    padding: 7px;

    font-size: 10px;

    font-weight: 1000;

}


.fragger-row {

    padding: 7px;

    border-bottom: 1px solid rgba(0,0,0,.12);

}


.fragger-pos,
.fragger-player,
.fragger-team,
.fragger-kills {

    font-weight: 800;

    font-size: 12px;

}


.fragger-kills {

    text-align: right;

    font-size: 15px;

    font-weight: 1000;

}


/* =========================================================
   DESKTOP
   ========================================================= */

@media (min-width: 1000px) {

    .ranking-grid {

        gap: 18px;

    }

    .team-card {

        min-width: 0;

    }

}


/* =========================================================
   TABLET
   ========================================================= */

@media (max-width: 800px) {

    body {

        padding: 8px;

    }

    .ranking-grid {

        gap: 8px;

    }

    .team-card {

        border-radius: 10px;

    }

    .rank-box {

        grid-template-columns:
            48px
            minmax(50px, 1fr)
            60px;

        min-height: 60px;

        padding: 5px;

    }

    .rank-number {

        font-size: 20px;

    }

    .rank-points {

        font-size: 19px;

    }

    .rank-kills {

        font-size: 19px;

    }

    .rank-team {

        font-size: 16px;

    }

}


/* =========================================================
   CELULAR
   ========================================================= */

@media (max-width: 560px) {

    body {

        padding: 5px;

    }

    .ranking-grid {

        grid-template-columns:
            minmax(0, 1fr)
            minmax(0, 1fr);

        gap: 5px;

    }

    .ranking-left,
    .ranking-right {

        gap: 5px;

    }

    .rank-box {

        grid-template-columns:
            40px
            minmax(40px, 1fr)
            48px;

        min-height: 52px;

        gap: 2px;

    }

    .rank-number {

        font-size: 16px;

    }

    .rank-points {

        font-size: 16px;

    }

    .rank-kills {

        font-size: 16px;

    }

    .rank-points-label,
    .rank-kills-label {

        font-size: 7px;

    }

    .rank-team {

        font-size: 12px;

        padding: 6px 2px;

    }

    .player-header {

        grid-template-columns:
            minmax(0, 1fr)
            39px
            42px;

        font-size: 7px;

    }

    .player-row {

        grid-template-columns:
            minmax(0, 1fr)
            39px
            42px;

        min-height: 27px;

    }

    .player-name {

        font-size: 9px;

    }

    .player-avg,
    .player-kills {

        font-size: 9px;

    }

    .games-area {

        padding: 4px;

    }

    .game-header,
    .game-values,
    .summary-values {

        gap: 3px;

    }

    .game-header span {

        font-size: 9px;

        padding: 4px;

    }

    .game-column {

        min-width: 62px;

    }

    .game-position-title,
    .game-score-title {

        font-size: 6px;

    }

    .game-position {

        font-size: 15px;

    }

    .game-score {

        font-size: 11px;

    }

}


/* =========================================================
   MEDALS
   ========================================================= */

.top1 .rank-number {

    text-shadow:
        0 1px 0 white;

}


.top2 .rank-number {

    text-shadow:
        0 1px 0 white;

}


.top3 .rank-number {

    text-shadow:
        0 1px 0 white;

}


</style>

</head>


<body>


<div class="page">


<div class="main-title">

TORNEOS MANYN

</div>


<div class="ranking-grid">

"""


    # ========================================================
    # DIVISION DE EQUIPOS
    #
    # DERECHA  = TOP 1 - TOP 9
    # IZQUIERDA = TOP 10 EN ADELANTE
    # ========================================================

    ranking_right = ranking[:9]

    ranking_left = ranking[9:]


    # ========================================================
    # FUNCIÓN PARA CREAR TARJETA
    # ========================================================

    def crear_tarjeta(r, pos):

        if pos == 1:

            rank_class = "top1"

        elif pos == 2:

            rank_class = "top2"

        elif pos == 3:

            rank_class = "top3"

        else:

            rank_class = "other"


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

        card = f"""

<div class="team-card {rank_class}">


    <div class="rank-box">


        <div class="rank-number">

            {medal} {pos}

        </div>


        <div class="rank-points-box">

            <div class="rank-points">

                {r["score"]}

            </div>

            <div class="rank-points-label">

                PUNTOS

            </div>

        </div>


        <div class="rank-kills-box">

            <div class="rank-kills">

                {r["kills"]}

            </div>

            <div class="rank-kills-label">

                KILLS

            </div>

        </div>


    </div>


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


            card += f"""

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


        card += """

    </div>


    <!-- ==================================================
         GAMES
         ================================================== -->

    <div class="games-area">

"""


        games_count = max(
            len(allgames),
            1
        )


        # ====================================================
        # GAME HEADER
        # ====================================================

        card += f"""

        <div
            class="game-header"
            style="--games-count:{games_count};"
        >

"""


        for g in allgames:

            card += f"""

            <span>

                M{g}

            </span>

"""


        card += """

        </div>


"""


        # ====================================================
        # GAME VALUES
        # ====================================================

        card += f"""

        <div
            class="game-values"
            style="--games-count:{games_count};"
        >

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


                card += f"""

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

                card += """

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


        card += """

        </div>

    </div>


"""


        # ====================================================
        # SUMMARY
        # ====================================================

        card += f"""

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


        for g in allgames:

            info = r["games"].get(
                g
            )


            if info:

                kills_game = info.get(
                    "kills",
                    0
                )


                card += f"""

        <div class="summary-item">


            <div class="summary-label">

                {kills_game}

            </div>


            <div>

                Kills

            </div>


        </div>

"""


            else:

                card += """

        <div class="summary-item">


            <div class="summary-label">

                -

            </div>


            <div>

                Kills

            </div>


        </div>

"""


        card += """

    </div>


</div>

"""


        return card


    # ========================================================
    # COLUMNA IZQUIERDA
    # TOP 10 EN ADELANTE
    # ========================================================

    html += """

<div class="ranking-left">

"""


    for index, r in enumerate(
        ranking_left,
        start=10
    ):

        html += crear_tarjeta(
            r,
            index
        )


    html += """

</div>


"""


    # ========================================================
    # COLUMNA DERECHA
    # TOP 1 AL TOP 9
    # ========================================================

    html += """

<div class="ranking-right">

"""


    for index, r in enumerate(
        ranking_right,
        start=1
    ):

        html += crear_tarjeta(
            r,
            index
        )


    html += """

</div>


</div>


"""


    # ========================================================
    # FRAGGER
    # ========================================================

    html += """

<div class="fragger-section">


    <div class="fragger-title">

        🔥 FRAGGER TABLE

    </div>


    <div class="fragger-header">

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
