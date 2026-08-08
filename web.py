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


/* =========================================================
   GLOBAL
   ========================================================= */

* {

    box-sizing: border-box;

}


html,
body {

    width: 100%;

    min-width: 0;

    margin: 0;

    padding: 0;

}


body {

    background:
        radial-gradient(
            circle at top,
            #252a2d 0%,
            #111416 45%,
            #090a0b 100%
        );

    color: #ffffff;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    overflow-x: hidden;

    -webkit-text-size-adjust: 100%;

    text-size-adjust: 100%;

}


/* =========================================================
   MAIN
   ========================================================= */

.main-container {

    width: 100%;

    min-width: 0;

    max-width: 1500px;

    margin: 0 auto;

    padding: 10px;

}


/* =========================================================
   TITLE
   ========================================================= */

.main-title {

    text-align: center;

    font-size: 30px;

    font-weight: 1000;

    letter-spacing: 3px;

    margin-bottom: 15px;

    color: #ffffff;

}


/* =========================================================
   RANK CARD
   ========================================================= */

.rank-box {

    position: relative;

    width: 100%;

    height: 120px;

    margin-top: 12px;

    border-radius: 14px;

    background:
        linear-gradient(
            145deg,
            #252b2e,
            #121517
        );

    border: 1px solid #353d40;

    box-shadow:
        0 8px 18px rgba(0,0,0,.40),
        inset 0 1px 0 rgba(255,255,255,.04);

}


.rank-label {

    position: absolute;

    top: 10px;

    left: 16px;

    font-size: 10px;

    font-weight: 900;

    letter-spacing: 1.5px;

    color: #b8c0c3;

}


.rank-number {

    position: absolute;

    left: 16px;

    bottom: 18px;

    font-size: 27px;

    font-weight: 1000;

    white-space: nowrap;

}


.rank-points {

    position: absolute;

    right: 125px;

    top: 31px;

    width: 85px;

    text-align: center;

    font-size: 29px;

    font-weight: 1000;

    color: #dfff00;

}


.rank-points-label {

    position: absolute;

    right: 125px;

    top: 66px;

    width: 85px;

    text-align: center;

    font-size: 8px;

    font-weight: 800;

    color: #8d979b;

}


.rank-kills {

    position: absolute;

    right: 22px;

    top: 31px;

    width: 65px;

    text-align: center;

    font-size: 29px;

    font-weight: 1000;

    color: #39ff14;

}


.rank-kills-label {

    position: absolute;

    right: 22px;

    top: 66px;

    width: 65px;

    text-align: center;

    font-size: 8px;

    font-weight: 800;

    color: #8d979b;

}


/* =========================================================
   TOP 1
   ========================================================= */

.top1 {

    border-color: #dfff00;

    box-shadow:
        0 0 15px rgba(223,255,0,.10),
        0 8px 18px rgba(0,0,0,.40);

}


.top1 .rank-label {

    color: #dfff00;

}


/* =========================================================
   TOP 2
   ========================================================= */

.top2 {

    border-color: #c8c8c8;

}


/* =========================================================
   TOP 3
   ========================================================= */

.top3 {

    border-color: #cd7f32;

}


.top3 .rank-label {

    color: #cd7f32;

}


/* =========================================================
   PLAYERS
   ========================================================= */

.players-area {

    margin-top: 5px;

    width: 100%;

    border-radius: 8px;

    overflow: hidden;

    border: 1px solid #30383b;

    background: #171b1d;

}


.player-header,
.player-row {

    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        100px
        75px;

    width: 100%;

}


.player-header {

    min-height: 29px;

    align-items: center;

    background: #22282b;

    color: #9ba4a8;

    font-size: 8px;

    font-weight: 900;

    letter-spacing: .7px;

}


.player-header > div {

    padding: 0 10px;

}


.player-header > div:nth-child(2),
.player-header > div:nth-child(3) {

    text-align: right;

}


.player-row {

    min-height: 34px;

    align-items: center;

    border-top: 1px solid #282e31;

}


.player-name {

    min-width: 0;

    padding-left: 10px;

    font-weight: 900;

    font-size: 11px;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;

}


.player-avg,
.player-kills {

    text-align: right;

    padding-right: 10px;

    font-size: 11px;

    font-weight: 900;

}


.player-avg {

    color: #aab2b5;

}


.player-kills {

    color: #39ff14;

}


/* =========================================================
   GAMES
   ========================================================= */

.games-area {

    margin-top: 5px;

    width: 100%;

    overflow: hidden;

    border-radius: 8px;

    border: 1px solid #30383b;

    background: #15191b;

}


.game-header,
.game-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    width: 100%;

}


.game-header {

    min-height: 30px;

    background: #22282b;

    border-bottom: 1px solid #343c3f;

}


.game-header span {

    min-width: 0;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 11px;

    font-weight: 1000;

    color: #ffffff;

    letter-spacing: .5px;

    border-right: 1px solid #343c3f;

}


.game-header span:last-child {

    border-right: none;

}


.game-values {

    min-height: 92px;

}


.game-column {

    min-width: 0;

    display: flex;

    flex-direction: column;

    align-items: center;

    justify-content: center;

    border-right: 1px solid #2c3336;

    padding: 4px 2px;

}


.game-column:last-child {

    border-right: none;

}


.game-position-title {

    font-size: 7px;

    line-height: 1;

    font-weight: 900;

    color: #8f989c;

    text-align: center;

    white-space: nowrap;

}


.game-position {

    margin-top: 4px;

    font-size: 20px;

    font-weight: 1000;

    line-height: 1;

    color: #ffffff;

}


.game-score-title {

    margin-top: 8px;

    font-size: 6px;

    line-height: 1;

    font-weight: 900;

    color: #8f989c;

    text-align: center;

    white-space: normal;

}


.game-score {

    margin-top: 4px;

    font-size: 13px;

    font-weight: 1000;

    color: #dfff00;

}


.duplicate-pos {

    color: #ff3131 !important;

    text-shadow:
        0 0 7px rgba(255,49,49,.45);

}


/* =========================================================
   SUMMARY
   ========================================================= */

.summary-area {

    margin-top: 5px;

    display: grid;

    grid-template-columns:
        180px
        minmax(0, 1fr);

    width: 100%;

    min-height: 62px;

    border-radius: 8px;

    overflow: hidden;

    border: 1px solid #30383b;

    background: #15191b;

}


.summary-team {

    display: flex;

    align-items: center;

    gap: 8px;

    padding: 8px;

    background: #202629;

}


.team-mark {

    width: 34px;

    height: 34px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 8px;

    background: #2c3336;

    color: #dfff00;

    font-size: 17px;

    font-weight: 1000;

}


.summary-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    width: 100%;

}


.summary-item {

    min-width: 0;

    display: flex;

    flex-direction: column;

    align-items: center;

    justify-content: center;

    border-right: 1px solid #2c3336;

    font-size: 7px;

    color: #7f898d;

}


.summary-item:last-child {

    border-right: none;

}


.summary-label {

    color: #ffffff;

    font-size: 14px;

    font-weight: 1000;

    margin-bottom: 2px;

}


/* =========================================================
   FRAGGER
   ========================================================= */

.fragger-container {

    width: 100%;

    margin-top: 18px;

    border-radius: 10px;

    overflow: hidden;

    border: 1px solid #30383b;

    background: #15191b;

}


.fragger-title {

    padding: 11px 13px;

    font-size: 14px;

    font-weight: 1000;

    letter-spacing: 1px;

    background: #202629;

    color: #dfff00;

}


.fragger-row {

    display: grid;

    grid-template-columns:
        60px
        minmax(0, 1fr)
        minmax(0, 1fr)
        80px;

    width: 100%;

    min-height: 38px;

    align-items: center;

    border-top: 1px solid #292f32;

}


.fragger-row.header {

    min-height: 31px;

    background: #22282b;

    border-top: none;

    color: #8f989c;

    font-size: 8px;

    font-weight: 1000;

    letter-spacing: .7px;

}


.fragger-row > div {

    min-width: 0;

    padding: 0 10px;

}


.fragger-pos {

    font-size: 12px;

    font-weight: 1000;

}


.fragger-player {

    font-size: 11px;

    font-weight: 900;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;

}


.fragger-team {

    font-size: 10px;

    font-weight: 800;

    color: #9ca5a8;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;

}


.fragger-kills {

    text-align: right;

    font-size: 13px;

    font-weight: 1000;

    color: #39ff14;

}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 600px) {


    .main-container {

        min-width: 0;

        width: 100%;

        padding: 4px;

    }


    .main-title {

        font-size: 20px;

        letter-spacing: 2px;

        margin-bottom: 6px;

    }


    .rank-box {

        height: 92px;

        margin-top: 6px;

        border-radius: 8px;

    }


    .rank-label {

        top: 7px;

        left: 10px;

        font-size: 7px;

    }


    .rank-number {

        left: 10px;

        bottom: 12px;

        font-size: 21px;

    }


    .rank-points {

        right: 65px;

        top: 25px;

        width: 55px;

        font-size: 21px;

    }


    .rank-points-label {

        right: 65px;

        top: 51px;

        width: 55px;

        font-size: 6px;

    }


    .rank-kills {

        right: 8px;

        top: 25px;

        width: 45px;

        font-size: 21px;

    }


    .rank-kills-label {

        right: 8px;

        top: 51px;

        width: 45px;

        font-size: 6px;

    }


    .players-area {

        margin-top: 3px;

        border-radius: 6px;

    }


    .player-header,
    .player-row {

        grid-template-columns:
            minmax(0, 1fr)
            58px
            50px;

    }


    .player-header {

        min-height: 23px;

        font-size: 6px;

    }


    .player-header > div {

        padding: 0 5px;

    }


    .player-row {

        min-height: 27px;

    }


    .player-name {

        padding-left: 6px;

        font-size: 9px;

    }


    .player-avg,
    .player-kills {

        padding-right: 6px;

        font-size: 9px;

    }


    .games-area {

        margin-top: 3px;

        border-radius: 6px;

    }


    .game-header {

        min-height: 23px;

    }


    .game-header span {

        font-size: 8px;

    }


    .game-values {

        min-height: 76px;

    }


    .game-column {

        padding: 3px 1px;

    }


    .game-position-title {

        font-size: 5px;

    }


    .game-position {

        font-size: 16px;

        margin-top: 3px;

    }


    .game-score-title {

        margin-top: 6px;

        font-size: 5px;

        max-width: 70px;

        line-height: 1.1;

    }


    .game-score {

        margin-top: 2px;

        font-size: 11px;

    }


    .summary-area {

        margin-top: 3px;

        grid-template-columns:
            95px
            minmax(0, 1fr);

        min-height: 50px;

        border-radius: 6px;

    }


    .summary-team {

        padding: 5px;

        gap: 4px;

    }


    .team-mark {

        width: 26px;

        height: 26px;

        font-size: 13px;

        border-radius: 5px;

    }


    .summary-item {

        font-size: 5px;

    }


    .summary-label {

        font-size: 11px;

        margin-bottom: 1px;

    }


    .fragger-container {

        margin-top: 8px;

        border-radius: 7px;

    }


    .fragger-title {

        padding: 8px 9px;

        font-size: 11px;

    }


    .fragger-row {

        grid-template-columns:
            38px
            minmax(0, 1fr)
            minmax(0, 1fr)
            50px;

        min-height: 29px;

    }


    .fragger-row > div {

        padding: 0 5px;

    }


    .fragger-row.header {

        min-height: 24px;

        font-size: 6px;

    }


    .fragger-pos {

        font-size: 9px;

    }


    .fragger-player {

        font-size: 8px;

    }


    .fragger-team {

        font-size: 7px;

    }


    .fragger-kills {

        font-size: 10px;

    }

}

</style>

</head>


<body>


<div class="main-container">


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


        html += f"""

<div class="rank-box {rank_class}">


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


<div class="players-area">


    <div class="player-header">

        <div>

            PLAYER

        </div>


        <div>

            AVG KILLS

        </div>


        <div>

            KILLS

        </div>

    </div>

"""


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


        # ====================================================
        # GAMES
        # ====================================================

        games_count = max(
            len(allgames),
            1
        )


        html += f"""

</div>


<div class="games-area">


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


"""


        html += f"""

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


        # ====================================================
        # SUMMARY
        # ====================================================

        html += f"""

    </div>

</div>


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
                font-size:10px;
                "
            >

                TOTAL

            </div>


            <div
                style="
                color:#8f989c;
                font-size:7px;
                "
            >

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


    # ========================================================
    # FRAGGER
    # ========================================================

    html += """

<div class="fragger-container">


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
