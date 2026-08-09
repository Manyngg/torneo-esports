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

    padding: 12px;

    background: #eee9df;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    color: #111;

}


/* =========================================================
   TITLE
   ========================================================= */

.main-title {

    text-align: center;

    font-size: 24px;

    font-weight: 900;

    letter-spacing: 1px;

    margin-bottom: 12px;

}


/* =========================================================
   RANKING GRID
   TOP 1-9 LEFT
   TOP 10+ RIGHT
   ========================================================= */

.ranking-grid {

    width: 100%;

    max-width: 1400px;

    margin: 0 auto;

    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        minmax(0, 1fr);

    gap: 8px;

    align-items: start;

}


/* =========================================================
   COLUMN
   ========================================================= */

.ranking-column {

    display: flex;

    flex-direction: column;

    gap: 8px;

}


/* =========================================================
   CARD
   ========================================================= */

.team-card {

    width: 100%;

    background: #dcdcdc;

    border-radius: 9px;

    overflow: hidden;

    border: 2px solid #c8c8c8;

    box-shadow:
        0 2px 5px rgba(0,0,0,0.20);

}


/* =========================================================
   TOP BAR
   ========================================================= */

.rank-box {

    min-height: 48px;

    display: grid;

    grid-template-columns:
        72px
        1fr
        75px
        65px;

    align-items: center;

    gap: 4px;

    padding: 5px 7px;

    background: #d5d5d5;

}


/* TOP 1 */

.top1 .rank-box {

    background: #d9ff38;

    border-bottom: 2px solid #b8d900;

}


/* TOP 2 */

.top2 .rank-box {

    background: #e4e4e4;

    border-bottom: 2px solid #bdbdbd;

}


/* TOP 3 */

.top3 .rank-box {

    background: #f0dfaa;

    border-bottom: 2px solid #c9b77b;

}


/* OTHER */

.other .rank-box {

    background: #dcdcdc;

}


/* =========================================================
   POSITION
   ========================================================= */

.rank-number {

    font-size: 20px;

    font-weight: 900;

    white-space: nowrap;

}


.rank-label {

    display: none;

}


/* =========================================================
   SCORE
   ========================================================= */

.rank-points {

    text-align: center;

    font-size: 19px;

    font-weight: 900;

    line-height: 1;

}


.rank-points-label {

    text-align: center;

    font-size: 9px;

    font-weight: 800;

    text-transform: uppercase;

}


/* =========================================================
   TOTAL KILLS
   ========================================================= */

.rank-kills {

    text-align: center;

    font-size: 18px;

    font-weight: 900;

    line-height: 1;

}


.rank-kills-label {

    text-align: center;

    font-size: 9px;

    font-weight: 800;

    text-transform: uppercase;

}


/* =========================================================
   TEAM
   ========================================================= */

.team-area {

    background: #eeeeee;

    padding: 6px 7px 7px 7px;

}


.rank-team {

    text-align: center;

    font-size: 16px;

    font-weight: 900;

    text-transform: uppercase;

    letter-spacing: .3px;

    padding: 4px 3px 6px 3px;

    color: #111;

}


/* =========================================================
   PLAYER HEADER
   ========================================================= */

.player-header {

    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        45px
        55px;

    align-items: center;

    background: #c9c9c9;

    border-radius: 5px;

    padding: 4px 6px;

    font-size: 8px;

    font-weight: 900;

    text-transform: uppercase;

}


/* =========================================================
   PLAYER ROW
   ========================================================= */

.player-row {

    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        45px
        55px;

    align-items: center;

    min-height: 27px;

    padding: 3px 6px;

    margin-top: 2px;

    background: #f7f7f7;

    border-radius: 4px;

    font-size: 11px;

    font-weight: 700;

}


.player-name {

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

}


.player-avg,
.player-kills {

    text-align: center;

    font-weight: 900;

}


/* =========================================================
   GAMES
   ========================================================= */

.games-area {

    padding: 6px 7px 7px 7px;

    background: #dedede;

}


/* =========================================================
   GAME HEADER
   ========================================================= */

.game-header {

    display: grid;

    grid-template-columns:
        repeat(var(--games-count), minmax(55px, 1fr));

    gap: 4px;

    margin-bottom: 4px;

}


.game-header span {

    text-align: center;

    background: #d9ff38;

    border-radius: 4px;

    padding: 4px 2px;

    font-size: 10px;

    font-weight: 900;

}


/* =========================================================
   GAME VALUES
   ========================================================= */

.game-values {

    display: grid;

    grid-template-columns:
        repeat(var(--games-count), minmax(55px, 1fr));

    gap: 4px;

}


/* =========================================================
   GAME COLUMN
   ========================================================= */

.game-column {

    min-width: 0;

    background: #f2f2f2;

    border-radius: 5px;

    padding: 4px;

    text-align: center;

}


/* =========================================================
   POSITION
   ========================================================= */

.game-position-title {

    font-size: 7px;

    font-weight: 900;

    color: #555;

}


.game-position {

    font-size: 15px;

    font-weight: 900;

    line-height: 1.1;

    margin: 2px 0 4px 0;

}


.game-score-title {

    font-size: 6px;

    line-height: 1.05;

    font-weight: 800;

    color: #555;

}


.game-score {

    font-size: 13px;

    font-weight: 900;

    margin-top: 2px;

}


/* =========================================================
   DUPLICATE POSITION
   ========================================================= */

.duplicate-pos {

    background: #ff4d4d !important;

    color: white !important;

    border-radius: 4px;

    padding: 2px 4px;

}


/* =========================================================
   SUMMARY
   ========================================================= */

.summary-team {

    display: flex;

    align-items: center;

    gap: 7px;

    padding: 6px 8px;

    background: #cfcfcf;

}


.team-mark {

    width: 28px;

    height: 28px;

    display: flex;

    justify-content: center;

    align-items: center;

    border-radius: 6px;

    background: #d9ff38;

    font-weight: 900;

    font-size: 13px;

}


.summary-title {

    font-size: 10px;

    font-weight: 900;

}


.summary-subtitle {

    font-size: 7px;

    font-weight: 700;

    color: #555;

}


/* =========================================================
   SUMMARY VALUES
   ========================================================= */

.summary-values {

    display: grid;

    grid-template-columns:
        repeat(var(--games-count), minmax(55px, 1fr));

    gap: 4px;

    padding: 6px;

    background: #dedede;

}


.summary-item {

    text-align: center;

    background: #f2f2f2;

    border-radius: 5px;

    padding: 4px;

    font-size: 8px;

    font-weight: 800;

}


.summary-label {

    font-size: 15px;

    font-weight: 900;

    line-height: 1.1;

}


/* =========================================================
   FRAGGER
   ========================================================= */

.fragger-section {

    max-width: 1400px;

    margin: 14px auto 0 auto;

    background: #dcdcdc;

    border-radius: 9px;

    overflow: hidden;

}


.fragger-title {

    background: #d9ff38;

    padding: 8px;

    font-size: 15px;

    font-weight: 900;

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

    gap: 4px;

    padding: 5px 8px;

}


.fragger-header {

    background: #c8c8c8;

    font-size: 8px;

    font-weight: 900;

}


.fragger-row {

    background: #eeeeee;

    border-top: 1px solid #d0d0d0;

    font-size: 10px;

    font-weight: 700;

}


.fragger-pos {

    font-weight: 900;

}


.fragger-player {

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

}


.fragger-team {

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

}


.fragger-kills {

    text-align: right;

    font-weight: 900;

}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 700px) {

    body {

        padding: 5px;

    }


    .ranking-grid {

        gap: 5px;

    }


    .ranking-column {

        gap: 5px;

    }


    .team-card {

        border-radius: 6px;

        border-width: 1px;

    }


    .rank-box {

        grid-template-columns:
            42px
            1fr
            45px
            42px;

        min-height: 38px;

        padding: 3px 4px;

    }


    .rank-number {

        font-size: 15px;

    }


    .rank-points {

        font-size: 14px;

    }


    .rank-kills {

        font-size: 14px;

    }


    .rank-points-label,
    .rank-kills-label {

        font-size: 6px;

    }


    .rank-team {

        font-size: 11px;

        padding: 3px;

    }


    .player-header {

        grid-template-columns:
            minmax(0, 1fr)
            34px
            40px;

        font-size: 6px;

        padding: 3px 4px;

    }


    .player-row {

        grid-template-columns:
            minmax(0, 1fr)
            34px
            40px;

        min-height: 21px;

        padding: 2px 4px;

        font-size: 8px;

    }


    .game-header {

        grid-template-columns:
            repeat(var(--games-count), minmax(35px, 1fr));

        gap: 2px;

    }


    .game-header span {

        padding: 3px 1px;

        font-size: 7px;

    }


    .game-values {

        grid-template-columns:
            repeat(var(--games-count), minmax(35px, 1fr));

        gap: 2px;

    }


    .game-column {

        padding: 3px 2px;

    }


    .game-position-title {

        font-size: 5px;

    }


    .game-position {

        font-size: 11px;

    }


    .game-score-title {

        font-size: 4.5px;

    }


    .game-score {

        font-size: 9px;

    }


    .summary-values {

        grid-template-columns:
            repeat(var(--games-count), minmax(35px, 1fr));

        gap: 2px;

    }


    .summary-item {

        font-size: 6px;

        padding: 3px 2px;

    }


    .summary-label {

        font-size: 11px;

    }


    .fragger-header,
    .fragger-row {

        grid-template-columns:
            35px
            minmax(0, 1fr)
            minmax(0, 1fr)
            40px;

        padding: 4px 5px;

        font-size: 8px;

    }


    .fragger-title {

        font-size: 12px;

        padding: 6px;

    }

}


/* =========================================================
   VERY SMALL PHONES
   ========================================================= */

@media (max-width: 430px) {

    .ranking-grid {

        gap: 3px;

    }


    .ranking-column {

        gap: 3px;

    }


    .rank-box {

        grid-template-columns:
            36px
            1fr
            40px
            38px;

    }


    .rank-number {

        font-size: 13px;

    }


    .rank-points {

        font-size: 12px;

    }


    .rank-kills {

        font-size: 12px;

    }


    .rank-team {

        font-size: 9px;

    }


    .player-header {

        grid-template-columns:
            minmax(0, 1fr)
            30px
            34px;

    }


    .player-row {

        grid-template-columns:
            minmax(0, 1fr)
            30px
            34px;

        font-size: 7px;

    }

}


</style>

</head>


<body>


<div class="main-title">

    TORNEOS MANYN

</div>


<div class="ranking-grid">

"""


    # ========================================================
    # SPLIT RANKING
    #
    # LEFT  = TOP 1 - 9
    # RIGHT = TOP 10+
    # ========================================================

    left_ranking = ranking[:9]

    right_ranking = ranking[9:]


    html += """

    <div class="ranking-column">

"""


    # ========================================================
    # LEFT COLUMN
    # TOP 1 TO TOP 9
    # ========================================================

    for pos, r in enumerate(
        left_ranking,
        start=1
    ):

        html += generar_card(
            pos,
            r,
            allgames,
            posiciones_por_game
        )


    html += """

    </div>


    <div class="ranking-column">

"""


    # ========================================================
    # RIGHT COLUMN
    # TOP 10 ONWARD
    # ========================================================

    for index, r in enumerate(
        right_ranking,
        start=10
    ):

        html += generar_card(
            index,
            r,
            allgames,
            posiciones_por_game
        )


    html += """

    </div>

</div>


<!-- ========================================================
     FRAGGER
     ======================================================== -->

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


    # ========================================================
    # FRAGGER ROWS
    # ========================================================

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
# CARD GENERATOR
# ============================================================

def generar_card(
    pos,
    r,
    allgames,
    posiciones_por_game
):


    # ========================================================
    # RANK STYLE
    # ========================================================

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


    # ========================================================
    # PLAYER STATS
    # ========================================================

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


    # ========================================================
    # GAME COUNT
    # ========================================================

    games_count = max(
        len(allgames),
        1
    )


    # ========================================================
    # CARD START
    # ========================================================

    html = f"""

<div class="team-card {rank_class}">


    <!-- ================================================
         RANK
         ================================================ -->

    <div class="rank-box">


        <div class="rank-number">

            {medal} {pos}

        </div>


        <div></div>


        <div>

            <div class="rank-points">

                {r["score"]}

            </div>

            <div class="rank-points-label">

                Puntos

            </div>

        </div>


        <div>

            <div class="rank-kills">

                {r["kills"]}

            </div>

            <div class="rank-kills-label">

                Kills

            </div>

        </div>


    </div>


    <!-- ================================================
         TEAM + PLAYERS
         ================================================ -->

    <div class="team-area">


        <div class="rank-team">

            {r["team"]}

        </div>


        <div class="player-header">

            <div>
                PLAYER
            </div>

            <div style="text-align:center;">
                AVG
            </div>

            <div style="text-align:center;">
                KILLS
            </div>

        </div>

"""


    # ========================================================
    # TOP 3 PLAYERS
    # ========================================================

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


        </div>

"""


    html += """

    </div>


    <!-- ================================================
         GAMES
         ================================================ -->

    <div class="games-area">


        <div
            class="game-header"
            style="--games-count:""" + str(games_count) + """;"
        >
"""


    # ========================================================
    # M1 M2 M3...
    # ========================================================

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
            style="--games-count:""" + str(games_count) + """;"
        >

"""


    # ========================================================
    # GAME CELLS
    # ========================================================

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

                    RESULTADO<br>
                    MULTIPLICADO

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

                    RESULTADO<br>
                    MULTIPLICADO

                </div>


                <div class="game-score">

                    -

                </div>


            </div>

"""


    html += """

        </div>

    </div>


    <!-- ================================================
         TOTAL
         ================================================ -->

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
        style="--games-count:""" + str(games_count) + """;"
    >

"""


    # ========================================================
    # SUMMARY VALUES
    # ========================================================

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
