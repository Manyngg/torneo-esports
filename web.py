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

/* ==========================================================
   GENERAL
   ========================================================== */

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    padding: 0;
    width: 100%;
}

body {

    background: #e9e5db;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    color: #111;

    padding: 5px;

    overflow-x: hidden;
}


/* ==========================================================
   CONTAINER
   ========================================================== */

.main-container {

    width: 100%;

    max-width: 1100px;

    margin: 0 auto;
}


/* ==========================================================
   TITLE
   ========================================================== */

.page-title {

    text-align: center;

    font-size: 26px;

    font-weight: 1000;

    margin: 3px 0 7px;

    letter-spacing: 1px;
}


/* ==========================================================
   RANK BOX
   ========================================================== */

.rank-box {

    width: 100%;

    min-height: 55px;

    display: grid;

    grid-template-columns:
        1fr
        1fr
        1fr;

    align-items: center;

    gap: 3px;

    padding: 5px;

    margin-top: 7px;

    border: 2px solid #111;

    border-radius: 10px;

    background: #eeeeea;

    box-shadow:
        0 3px 0 #111;

    position: relative;
}


/* ==========================================================
   TOP 1
   ========================================================== */

.rank-box.top1 {

    background:
        linear-gradient(
            90deg,
            #d8ff00,
            #f1ff72,
            #d8ff00
        );
}


/* ==========================================================
   TOP 2
   ========================================================== */

.rank-box.top2 {

    background:
        linear-gradient(
            90deg,
            #eeeeee,
            #cfcfcf,
            #eeeeee
        );
}


/* ==========================================================
   TOP 3
   ========================================================== */

.rank-box.top3 {

    background:
        linear-gradient(
            90deg,
            #ffc36a,
            #ffe0ad,
            #ffc36a
        );
}


/* ==========================================================
   RANK LABEL
   ========================================================== */

.rank-label {

    position: absolute;

    left: 6px;

    top: 2px;

    font-size: 7px;

    font-weight: 1000;
}


/* ==========================================================
   RANK NUMBER
   ========================================================== */

.rank-number {

    text-align: center;

    font-size: 22px;

    font-weight: 1000;

    line-height: 1;
}


/* ==========================================================
   POINTS
   ========================================================== */

.rank-points {

    text-align: center;

    font-size: 21px;

    font-weight: 1000;

    line-height: 1;
}


.rank-points-label {

    text-align: center;

    font-size: 7px;

    font-weight: 1000;

    margin-top: 2px;
}


/* ==========================================================
   KILLS
   ========================================================== */

.rank-kills {

    text-align: center;

    font-size: 21px;

    font-weight: 1000;

    line-height: 1;
}


.rank-kills-label {

    text-align: center;

    font-size: 7px;

    font-weight: 1000;

    margin-top: 2px;
}


/* ==========================================================
   TEAM
   ========================================================== */

.team-area {

    width: 100%;

    margin-top: 4px;

    border: 2px solid #111;

    border-radius: 9px;

    overflow: hidden;

    background: #ededeb;
}


.rank-team {

    width: 100%;

    text-align: center;

    padding: 5px 4px;

    font-size: 18px;

    font-weight: 1000;

    text-transform: uppercase;

    background: #d8ff00;

    border-bottom: 2px solid #111;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;
}


/* ==========================================================
   PLAYER HEADER
   ========================================================== */

.player-header {

    display: grid;

    grid-template-columns:
        minmax(0, 2fr)
        0.8fr
        0.8fr;

    align-items: center;

    background: #d7d7d2;

    font-size: 8px;

    font-weight: 1000;

    text-align: center;

    padding: 4px;
}


/* ==========================================================
   PLAYER ROW
   ========================================================== */

.player-row {

    display: grid;

    grid-template-columns:
        minmax(0, 2fr)
        0.8fr
        0.8fr;

    align-items: center;

    min-height: 27px;

    padding: 3px 5px;

    border-top: 1px solid #aaa;

    background: #f1f1ee;
}


.player-name {

    text-align: left;

    font-size: 10px;

    font-weight: 900;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;
}


.player-avg,
.player-kills {

    text-align: center;

    font-size: 11px;

    font-weight: 1000;
}


/* ==========================================================
   GAMES
   ========================================================== */

.games-area {

    width: 100%;

    margin-top: 4px;

    border: 2px solid #111;

    border-radius: 9px;

    overflow: hidden;

    background: #eeeeea;
}


.game-header {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    width: 100%;

    background: #111;

    color: #fff;
}


.game-header span {

    text-align: center;

    padding: 4px 1px;

    font-size: 10px;

    font-weight: 1000;

    border-right: 1px solid #555;
}


.game-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    width: 100%;
}


.game-column {

    min-width: 0;

    text-align: center;

    padding: 4px 2px;

    border-right: 1px solid #aaa;

    background: #eeeeea;
}


.game-column:last-child {

    border-right: none;
}


.game-position-title,
.game-score-title {

    font-size: 6px;

    font-weight: 1000;

    line-height: 1.05;
}


.game-position {

    font-size: 18px;

    font-weight: 1000;

    line-height: 1;

    margin: 3px 0 4px;
}


.game-score {

    font-size: 15px;

    font-weight: 1000;

    line-height: 1;

    margin-top: 3px;
}


/* ==========================================================
   DUPLICATE POSITION
   ========================================================== */

.duplicate-pos {

    color: #d00000;

    background: #ffd2d2;

    border-radius: 4px;

    padding: 2px;
}


/* ==========================================================
   SUMMARY
   ========================================================== */

.summary-team {

    width: 100%;

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 6px;

    margin-top: 4px;

    padding: 5px;

    background: #d8ff00;

    border: 2px solid #111;

    border-radius: 8px 8px 0 0;
}


.team-mark {

    width: 25px;

    height: 25px;

    display: flex;

    justify-content: center;

    align-items: center;

    background: #111;

    color: #d8ff00;

    border-radius: 50%;

    font-weight: 1000;
}


.summary-title {

    font-size: 10px;

    font-weight: 1000;
}


.summary-subtitle {

    font-size: 6px;

    font-weight: 900;
}


.summary-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    width: 100%;

    border: 2px solid #111;

    border-top: none;

    border-radius: 0 0 8px 8px;

    overflow: hidden;
}


.summary-item {

    text-align: center;

    padding: 4px;

    border-right: 1px solid #aaa;

    background: #eeeeea;

    font-size: 7px;

    font-weight: 1000;
}


.summary-item:last-child {

    border-right: none;
}


.summary-label {

    font-size: 16px;

    font-weight: 1000;

    line-height: 1;
}


/* ==========================================================
   FRAGGER
   ========================================================== */

.fragger-title {

    margin-top: 8px;

    padding: 6px;

    text-align: center;

    background: #111;

    color: #d8ff00;

    border: 2px solid #111;

    border-radius: 8px 8px 0 0;

    font-size: 13px;

    font-weight: 1000;
}


.fragger-header {

    display: grid;

    grid-template-columns:
        .55fr
        1.6fr
        1.3fr
        .7fr;

    align-items: center;

    padding: 4px;

    background: #d8ff00;

    border-left: 2px solid #111;

    border-right: 2px solid #111;

    font-size: 7px;

    font-weight: 1000;

    text-align: center;
}


.fragger-row {

    display: grid;

    grid-template-columns:
        .55fr
        1.6fr
        1.3fr
        .7fr;

    align-items: center;

    padding: 4px;

    background: #eeeeea;

    border-left: 2px solid #111;

    border-right: 2px solid #111;

    border-top: 1px solid #aaa;

    font-size: 9px;

    font-weight: 900;
}


.fragger-row:last-child {

    border-bottom: 2px solid #111;

    border-radius: 0 0 8px 8px;
}


.fragger-pos,
.fragger-player,
.fragger-team,
.fragger-kills {

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;
}


.fragger-pos {

    text-align: center;
}


.fragger-player {

    text-align: left;
}


.fragger-team {

    text-align: center;
}


.fragger-kills {

    text-align: center;

    font-size: 11px;

    font-weight: 1000;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 600px) {

    body {
        padding: 3px;
    }

    .page-title {
        font-size: 21px;
        margin: 2px 0 5px;
    }

    .rank-box {
        min-height: 48px;
        margin-top: 5px;
        padding: 4px;
    }

    .rank-number {
        font-size: 18px;
    }

    .rank-points {
        font-size: 17px;
    }

    .rank-kills {
        font-size: 17px;
    }

    .rank-points-label,
    .rank-kills-label {
        font-size: 6px;
    }

    .rank-team {
        font-size: 15px;
        padding: 4px;
    }

    .player-header {
        font-size: 6px;
        padding: 3px;
    }

    .player-row {
        min-height: 24px;
        padding: 2px 4px;
    }

    .player-name {
        font-size: 9px;
    }

    .player-avg,
    .player-kills {
        font-size: 10px;
    }

    .game-header span {
        font-size: 8px;
        padding: 3px 1px;
    }

    .game-column {
        padding: 3px 1px;
    }

    .game-position-title,
    .game-score-title {
        font-size: 5px;
    }

    .game-position {
        font-size: 15px;
        margin: 2px 0 3px;
    }

    .game-score {
        font-size: 12px;
        margin-top: 2px;
    }

    .summary-item {
        padding: 3px 1px;
        font-size: 6px;
    }

    .summary-label {
        font-size: 14px;
    }

    .fragger-header,
    .fragger-row {
        padding: 3px;
    }

    .fragger-header {
        font-size: 6px;
    }

    .fragger-row {
        font-size: 8px;
    }

    .fragger-kills {
        font-size: 10px;
    }
}


/* ==========================================================
   VERY SMALL PHONES
   ========================================================== */

@media (max-width: 380px) {

    .rank-number {
        font-size: 16px;
    }

    .rank-points,
    .rank-kills {
        font-size: 15px;
    }

    .rank-team {
        font-size: 13px;
    }

    .player-name {
        font-size: 8px;
    }

    .game-position {
        font-size: 13px;
    }

    .game-score {
        font-size: 10px;
    }
}

</style>

</head>


<body>

<div class="main-container">

<div class="page-title">
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

            label = ""

        elif pos == 2:

            rank_class = "top2"

            label = ""

        elif pos == 3:

            rank_class = "top3"

            label = "TOP 3"

        else:

            rank_class = "other"

            label = "RANKING"


        # ====================================================
        # MEDAL
        # ====================================================

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
        # RANK
        # ====================================================

        html += f"""

<div class="rank-box {rank_class}">


    <div class="rank-label">

        {label}

    </div>


    <div class="rank-number">

        {medal} {pos}

    </div>


    <div>

        <div class="rank-points">

            {r["score"]}

        </div>


        <div class="rank-points-label">

            PUNTOS

        </div>

    </div>


    <div>

        <div class="rank-kills">

            {r["kills"]}

        </div>


        <div class="rank-kills-label">

            KILLS

        </div>

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


    </div>

"""


        html += """

</div>


<!-- ======================================================
     GAMES
     ====================================================== -->

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


<!-- ======================================================
     SUMMARY
     ====================================================== -->

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

            KILLS

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

            KILLS

        </div>


    </div>

"""


        html += """

</div>

"""


    # ========================================================
    # FRAGGER
    # ========================================================

    html += """

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


    <div>

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
