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

    background:
        linear-gradient(
            135deg,
            #e8e4d9 0%,
            #f3f0e7 50%,
            #ddd9ce 100%
        );

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    color: #111;

    padding: 8px;

    overflow-x: hidden;
}


/* ==========================================================
   MAIN CONTAINER
   ========================================================== */

.main-container {

    width: 100%;

    max-width: 1250px;

    margin: 0 auto;
}


/* ==========================================================
   TITLE
   ========================================================== */

.page-title {

    text-align: center;

    font-size: clamp(
        22px,
        5vw,
        40px
    );

    font-weight: 1000;

    letter-spacing: 1px;

    margin: 4px 0 10px;

    color: #111;

    text-transform: uppercase;
}


/* ==========================================================
   RANK BOX
   ========================================================== */

.rank-box {

    width: 100%;

    display: grid;

    grid-template-columns:
        0.9fr
        1.1fr
        1fr
        1fr;

    align-items: center;

    gap: 5px;

    padding: 7px 9px;

    margin-top: 10px;

    border-radius: 12px;

    border: 2px solid #151515;

    box-shadow:
        0 4px 0 #111,
        0 5px 10px rgba(0,0,0,.20);

    background: #eeeeea;

    position: relative;

    min-height: 58px;
}


/* ==========================================================
   TOP 1
   ========================================================== */

.rank-box.top1 {

    background:
        linear-gradient(
            135deg,
            #dfff00,
            #bfff00
        );

    border-color: #101010;
}


/* ==========================================================
   TOP 2
   ========================================================== */

.rank-box.top2 {

    background:
        linear-gradient(
            135deg,
            #e9e9e9,
            #c8c8c8
        );

    border-color: #161616;
}


/* ==========================================================
   TOP 3
   ========================================================== */

.rank-box.top3 {

    background:
        linear-gradient(
            135deg,
            #ffc56a,
            #e99635
        );

    border-color: #161616;
}


/* ==========================================================
   OTHER
   ========================================================== */

.rank-box.other {

    background: #ededed;
}


/* ==========================================================
   RANK LABEL
   ========================================================== */

.rank-label {

    position: absolute;

    top: 3px;

    left: 8px;

    font-size: 8px;

    font-weight: 900;

    letter-spacing: .6px;
}


/* ==========================================================
   RANK NUMBER
   ========================================================== */

.rank-number {

    font-size: clamp(
        20px,
        5vw,
        32px
    );

    font-weight: 1000;

    text-align: center;

    line-height: 1;
}


/* ==========================================================
   RANK POINTS
   ========================================================== */

.rank-points {

    font-size: clamp(
        18px,
        4vw,
        28px
    );

    font-weight: 1000;

    text-align: center;
}


.rank-points-label {

    font-size: 8px;

    font-weight: 900;

    text-align: center;

    margin-top: -3px;
}


.rank-kills {

    font-size: clamp(
        18px,
        4vw,
        28px
    );

    font-weight: 1000;

    text-align: center;
}


.rank-kills-label {

    font-size: 8px;

    font-weight: 900;

    text-align: center;

    margin-top: -3px;
}


/* ==========================================================
   TEAM AREA
   ========================================================== */

.team-area {

    width: 100%;

    margin-top: 4px;

    background: #f4f4f1;

    border: 2px solid #171717;

    border-radius: 10px;

    overflow: hidden;
}


/* ==========================================================
   TEAM NAME
   ========================================================== */

.rank-team {

    width: 100%;

    text-align: center;

    font-size: clamp(
        17px,
        4vw,
        27px
    );

    font-weight: 1000;

    text-transform: uppercase;

    padding: 7px 5px 5px;

    letter-spacing: .5px;

    background:
        linear-gradient(
            90deg,
            #dfff00,
            #f5ff87,
            #dfff00
        );

    border-bottom: 2px solid #151515;

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
        .7fr
        .7fr;

    gap: 3px;

    padding: 4px 6px;

    font-size: 8px;

    font-weight: 1000;

    text-align: center;

    background: #deded9;
}


/* ==========================================================
   PLAYER ROW
   ========================================================== */

.player-row {

    display: grid;

    grid-template-columns:
        minmax(0, 2fr)
        .7fr
        .7fr;

    gap: 3px;

    align-items: center;

    padding: 5px 6px;

    border-top: 1px solid #aaa;

    min-height: 29px;
}


.player-name {

    font-size: 11px;

    font-weight: 900;

    text-align: left;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;
}


.player-avg,
.player-kills {

    text-align: center;

    font-size: 12px;

    font-weight: 1000;
}


/* ==========================================================
   GAMES
   ========================================================== */

.games-area {

    width: 100%;

    margin-top: 5px;

    background: #eeeeea;

    border: 2px solid #171717;

    border-radius: 10px;

    overflow: hidden;
}


/* ==========================================================
   GAME HEADER
   ========================================================== */

.game-header {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    width: 100%;

    background: #171717;

    color: #ffffff;

    min-width: 0;
}


.game-header span {

    text-align: center;

    padding: 5px 2px;

    font-size: clamp(
        10px,
        2.5vw,
        14px
    );

    font-weight: 1000;

    border-right: 1px solid #555;
}


/* ==========================================================
   GAME VALUES
   ========================================================== */

.game-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    width: 100%;

    min-width: 0;
}


/* ==========================================================
   GAME COLUMN
   ========================================================== */

.game-column {

    min-width: 0;

    text-align: center;

    padding: 5px 2px;

    border-right: 1px solid #999;

    background: #f0f0ed;
}


.game-column:last-child {

    border-right: none;
}


.game-position-title,
.game-score-title {

    font-size: 7px;

    line-height: 1.05;

    font-weight: 900;

    color: #444;
}


.game-position {

    font-size: clamp(
        17px,
        4vw,
        24px
    );

    font-weight: 1000;

    margin: 1px 0 4px;
}


.game-score {

    font-size: clamp(
        14px,
        3.5vw,
        20px
    );

    font-weight: 1000;

    margin-top: 2px;
}


/* ==========================================================
   DUPLICATE POSITION
   ========================================================== */

.duplicate-pos {

    color: #d00000;

    background: #ffd6d6;

    border-radius: 5px;
}


/* ==========================================================
   SUMMARY
   ========================================================== */

.summary-team {

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 7px;

    margin-top: 5px;

    padding: 6px;

    border: 2px solid #171717;

    border-radius: 10px 10px 0 0;

    background: #dfff00;
}


.team-mark {

    width: 28px;

    height: 28px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 50%;

    background: #171717;

    color: #dfff00;

    font-weight: 1000;

    font-size: 14px;
}


.summary-title {

    font-size: 11px;

    font-weight: 1000;

    line-height: 1;
}


.summary-subtitle {

    font-size: 7px;

    font-weight: 900;

    margin-top: 2px;
}


/* ==========================================================
   SUMMARY VALUES
   ========================================================== */

.summary-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    border: 2px solid #171717;

    border-top: none;

    border-radius: 0 0 10px 10px;

    overflow: hidden;

    background: #eeeeea;
}


.summary-item {

    text-align: center;

    padding: 5px 2px;

    border-right: 1px solid #999;

    font-size: 8px;

    font-weight: 900;
}


.summary-item:last-child {

    border-right: none;
}


.summary-label {

    font-size: 17px;

    font-weight: 1000;

    line-height: 1;
}


/* ==========================================================
   FRAGGER
   ========================================================== */

.fragger-title {

    margin-top: 10px;

    background: #171717;

    color: #dfff00;

    border-radius: 10px 10px 0 0;

    padding: 7px;

    text-align: center;

    font-size: 14px;

    font-weight: 1000;

    letter-spacing: .5px;
}


.fragger-header {

    display: grid;

    grid-template-columns:
        .55fr
        1.7fr
        1.4fr
        .7fr;

    gap: 3px;

    background: #dfff00;

    border: 2px solid #171717;

    border-top: none;

    padding: 5px;

    font-size: 8px;

    font-weight: 1000;

    text-align: center;
}


.fragger-row {

    display: grid;

    grid-template-columns:
        .55fr
        1.7fr
        1.4fr
        .7fr;

    gap: 3px;

    align-items: center;

    padding: 5px;

    background: #eeeeea;

    border-left: 2px solid #171717;

    border-right: 2px solid #171717;

    border-bottom: 1px solid #999;

    font-size: 10px;

    font-weight: 900;
}


.fragger-row:last-child {

    border-bottom: 2px solid #171717;

    border-radius: 0 0 10px 10px;
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

    font-size: 12px;

    font-weight: 1000;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 600px) {

    body {
        padding: 4px;
    }

    .rank-box {
        min-height: 54px;
        padding: 6px 5px;
        gap: 2px;
        margin-top: 7px;
    }

    .rank-label {
        font-size: 7px;
        top: 2px;
        left: 5px;
    }

    .rank-number {
        font-size: 20px;
    }

    .rank-points {
        font-size: 18px;
    }

    .rank-kills {
        font-size: 18px;
    }

    .rank-points-label,
    .rank-kills-label {
        font-size: 7px;
    }

    .rank-team {
        font-size: 16px;
        padding: 6px 4px 4px;
    }

    .player-header {
        font-size: 7px;
        padding: 3px 4px;
    }

    .player-row {
        padding: 4px;
        min-height: 26px;
    }

    .player-name {
        font-size: 10px;
    }

    .player-avg,
    .player-kills {
        font-size: 11px;
    }

    .game-header span {
        font-size: 9px;
        padding: 4px 1px;
    }

    .game-column {
        padding: 4px 1px;
    }

    .game-position-title,
    .game-score-title {
        font-size: 6px;
    }

    .game-position {
        font-size: 16px;
        margin-bottom: 3px;
    }

    .game-score {
        font-size: 13px;
    }

    .summary-item {
        font-size: 7px;
        padding: 4px 1px;
    }

    .summary-label {
        font-size: 15px;
    }

    .fragger-header,
    .fragger-row {
        padding: 4px 3px;
        font-size: 9px;
    }

    .fragger-kills {
        font-size: 11px;
    }
}


/* ==========================================================
   VERY SMALL PHONES
   ========================================================== */

@media (max-width: 380px) {

    .rank-box {
        grid-template-columns:
            .8fr
            1fr
            .9fr
            .9fr;
    }

    .rank-number {
        font-size: 18px;
    }

    .rank-points,
    .rank-kills {
        font-size: 16px;
    }

    .rank-team {
        font-size: 14px;
    }

    .player-name {
        font-size: 9px;
    }

    .game-position {
        font-size: 14px;
    }

    .game-score {
        font-size: 11px;
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
        # MEDALS
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
        # CARD
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


<div class="team-area">


    <!-- TEAM ABOVE AVG / KILLS -->

    <div class="rank-team">
        {r["team"]}
    </div>


    <!-- PLAYER HEADER -->

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
            {info.get("kills", 0)}
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
