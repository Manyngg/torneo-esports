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

/* ============================================================
   RESET
   ============================================================ */

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

    background: #f2eee6;

    color: #ffffff;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    overflow-x: hidden;

}


/* ============================================================
   CONTENEDOR
   ============================================================ */

.container {

    width: 100%;

    max-width: 1200px;

    margin: 0 auto;

    padding: 10px;

}


/* ============================================================
   TITULO
   ============================================================ */

.title {

    text-align: center;

    font-size: 25px;

    font-weight: 1000;

    letter-spacing: 1px;

    color: #111111;

    margin-bottom: 10px;

}


/* ============================================================
   TARJETA DE EQUIPO
   ============================================================ */

.rank-card {

    width: 100%;

    margin-bottom: 9px;

    padding: 7px;

    background: #e6e6e6;

    border-radius: 16px;

    box-shadow:
        0 10px 0 #bdbdbd,
        0 18px 35px rgba(0,0,0,0.25);

    color: #111111;

    overflow: hidden;

}


/* ============================================================
   TOP 1
   ============================================================ */

.rank-card.top1 {

    border: 3px solid #d8ff00;

    background:
        linear-gradient(
            135deg,
            #f1f1f1,
            #d9ff00
        );

}


/* ============================================================
   TOP 2
   ============================================================ */

.rank-card.top2 {

    border: 3px solid #bfc4c7;

    background:
        linear-gradient(
            135deg,
            #f4f4f4,
            #d7dadd
        );

}


/* ============================================================
   TOP 3
   ============================================================ */

.rank-card.top3 {

    border: 3px solid #ffb300;

    background:
        linear-gradient(
            135deg,
            #f5f5f5,
            #ffd37a
        );

}


/* ============================================================
   OTHER
   ============================================================ */

.rank-card.other {

    border: 2px solid #d0d0d0;

}


/* ============================================================
   LABEL
   ============================================================ */

.rank-label {

    text-align: center;

    font-size: 8px;

    font-weight: 900;

    line-height: 9px;

    color: #202020;

    margin: 0;

}


/* ============================================================
   POSICION
   ============================================================ */

.rank-number {

    text-align: center;

    font-size: 20px;

    font-weight: 1000;

    line-height: 21px;

    color: #111111;

    margin: 0;

}


/* ============================================================
   TEAM NAME
   ============================================================ */

.rank-team {

    text-align: center;

    font-size: 15px;

    font-weight: 1000;

    line-height: 17px;

    color: #111111;

    margin: 1px 0 3px 0;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;

}


/* ============================================================
   POINTS
   ============================================================ */

.rank-points {

    text-align: center;

    font-size: 17px;

    font-weight: 1000;

    line-height: 18px;

    color: #111111;

    margin: 0;

}

.rank-points-label {

    text-align: center;

    font-size: 7px;

    font-weight: 900;

    line-height: 8px;

    color: #555555;

}


/* ============================================================
   KILLS
   ============================================================ */

.rank-kills {

    text-align: center;

    font-size: 13px;

    font-weight: 1000;

    line-height: 14px;

    color: #111111;

    margin-top: 1px;

}

.rank-kills-label {

    text-align: center;

    font-size: 7px;

    font-weight: 900;

    line-height: 8px;

    color: #555555;

}


/* ============================================================
   PLAYER HEADER
   ============================================================ */

.player-header {

    display: grid;

    grid-template-columns:
        1fr
        70px
        50px;

    align-items: center;

    height: 19px;

    min-height: 19px;

    margin-top: 3px;

    padding: 2px 5px;

    background: #202326;

    color: #d8ff00;

    border-radius: 5px 5px 0 0;

    font-size: 6px;

    font-weight: 1000;

    line-height: 7px;

}


/* ============================================================
   PLAYER ROW
   ============================================================ */

.player-row {

    display: grid;

    grid-template-columns:
        1fr
        70px
        50px;

    align-items: center;

    min-height: 20px;

    height: 20px;

    padding: 2px 5px;

    background: #eeeeee;

    border-bottom: 1px solid #d0d0d0;

    color: #151515;

    font-size: 8px;

    line-height: 9px;

}


/* ============================================================
   PLAYER NAME
   ============================================================ */

.player-name {

    font-size: 8px;

    font-weight: 900;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

}

.player-avg {

    text-align: center;

    font-size: 7px;

    font-weight: 900;

}

.player-kills {

    text-align: right;

    font-size: 8px;

    font-weight: 1000;

    color: #101010;

}


/* ============================================================
   GAME HEADER
   ============================================================ */

.game-header {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    gap: 2px;

    margin-top: 3px;

    height: 18px;

}


.game-header span {

    display: flex;

    align-items: center;

    justify-content: center;

    background: #202326;

    color: #d8ff00;

    border-radius: 4px 4px 0 0;

    font-size: 6px;

    font-weight: 1000;

    line-height: 7px;

}


/* ============================================================
   GAME VALUES
   ============================================================ */

.game-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    gap: 2px;

}


/* ============================================================
   GAME COLUMN
   ============================================================ */

.game-column {

    min-width: 0;

    min-height: 66px;

    padding: 3px 2px;

    background: #eeeeee;

    border: 1px solid #d0d0d0;

    border-radius: 0 0 5px 5px;

    text-align: center;

}


/* ============================================================
   POSITION TITLE
   ============================================================ */

.game-position-title {

    font-size: 5px;

    font-weight: 1000;

    line-height: 6px;

    color: #666666;

    white-space: nowrap;

}


/* ============================================================
   POSITION
   ============================================================ */

.game-position {

    font-size: 14px;

    font-weight: 1000;

    line-height: 16px;

    color: #111111;

}


/* ============================================================
   DUPLICATE POSITION
   ============================================================ */

.game-position.duplicate-pos {

    color: #ff1f1f;

    background: #ffd6d6;

    border-radius: 3px;

}


/* ============================================================
   SCORE TITLE
   ============================================================ */

.game-score-title {

    margin-top: 2px;

    font-size: 4.5px;

    font-weight: 1000;

    line-height: 5px;

    color: #777777;

}


/* ============================================================
   SCORE
   ============================================================ */

.game-score {

    font-size: 10px;

    font-weight: 1000;

    line-height: 12px;

    color: #151515;

}


/* ============================================================
   SUMMARY TEAM
   ============================================================ */

.summary-team {

    display: flex;

    align-items: center;

    gap: 5px;

    height: 25px;

    min-height: 25px;

    margin-top: 2px;

    padding: 2px 5px;

    background: #202326;

    border-radius: 5px 5px 0 0;

}


/* ============================================================
   TEAM MARK
   ============================================================ */

.team-mark {

    display: flex;

    align-items: center;

    justify-content: center;

    width: 20px;

    height: 20px;

    border-radius: 4px;

    background: #d8ff00;

    color: #111111;

    font-size: 9px;

    font-weight: 1000;

}


/* ============================================================
   SUMMARY VALUES
   ============================================================ */

.summary-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            minmax(0, 1fr)
        );

    gap: 2px;

}


/* ============================================================
   SUMMARY ITEM
   ============================================================ */

.summary-item {

    min-height: 22px;

    padding: 2px;

    text-align: center;

    background: #eeeeee;

    color: #333333;

    border-radius: 0 0 4px 4px;

    font-size: 5px;

    line-height: 6px;

}


/* ============================================================
   SUMMARY NUMBER
   ============================================================ */

.summary-label {

    font-size: 9px;

    font-weight: 1000;

    line-height: 10px;

    color: #111111;

}


/* ============================================================
   FRAGGER TITLE
   ============================================================ */

.fragger-title {

    margin-top: 10px;

    margin-bottom: 3px;

    padding: 5px 7px;

    background: #202326;

    border-left: 5px solid #d8ff00;

    border-radius: 6px;

    color: #d8ff00;

    font-size: 12px;

    font-weight: 1000;

    line-height: 13px;

}


/* ============================================================
   FRAGGER TABLE
   ============================================================ */

.fragger-row {

    display: grid;

    grid-template-columns:
        42px
        minmax(0, 1.4fr)
        minmax(0, 1fr)
        45px;

    align-items: center;

    min-height: 20px;

    height: 20px;

    padding: 2px 5px;

    background: #eeeeee;

    border-bottom: 1px solid #d0d0d0;

    color: #151515;

    font-size: 7px;

    line-height: 8px;

}


.fragger-row.header {

    height: 18px;

    min-height: 18px;

    background: #202326;

    color: #d8ff00;

    font-size: 6px;

    font-weight: 1000;

}


/* ============================================================
   FRAGGER POSITION
   ============================================================ */

.fragger-pos {

    font-size: 8px;

    font-weight: 1000;

}


/* ============================================================
   FRAGGER PLAYER
   ============================================================ */

.fragger-player {

    font-size: 7px;

    font-weight: 900;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

}


/* ============================================================
   FRAGGER TEAM
   ============================================================ */

.fragger-team {

    font-size: 6px;

    font-weight: 700;

    color: #555555;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

}


/* ============================================================
   FRAGGER KILLS
   ============================================================ */

.fragger-kills {

    text-align: right;

    font-size: 9px;

    font-weight: 1000;

}


/* ============================================================
   MOBILE
   ============================================================ */

@media (max-width: 600px) {


    .container {

        padding: 5px;

    }


    .title {

        font-size: 20px;

        margin-bottom: 5px;

    }


    .rank-card {

        margin-bottom: 6px;

        padding: 5px;

        border-radius: 11px;

        box-shadow:
            0 6px 0 #bdbdbd,
            0 10px 20px rgba(0,0,0,0.20);

    }


    .rank-label {

        font-size: 6px;

        line-height: 7px;

    }


    .rank-number {

        font-size: 16px;

        line-height: 17px;

    }


    .rank-team {

        font-size: 12px;

        line-height: 14px;

        margin: 0 0 2px 0;

    }


    .rank-points {

        font-size: 13px;

        line-height: 14px;

    }


    .rank-points-label {

        font-size: 5px;

        line-height: 6px;

    }


    .rank-kills {

        font-size: 10px;

        line-height: 11px;

    }


    .rank-kills-label {

        font-size: 5px;

        line-height: 6px;

    }


    /* PLAYER */

    .player-header {

        grid-template-columns:
            1fr
            52px
            38px;

        height: 16px;

        min-height: 16px;

        padding: 1px 4px;

        margin-top: 2px;

        font-size: 5px;

        line-height: 6px;

    }


    .player-row {

        grid-template-columns:
            1fr
            52px
            38px;

        height: 17px;

        min-height: 17px;

        padding: 1px 4px;

    }


    .player-name {

        font-size: 7px;

        line-height: 8px;

    }


    .player-avg {

        font-size: 6px;

        line-height: 7px;

    }


    .player-kills {

        font-size: 7px;

        line-height: 8px;

    }


    /* GAMES */

    .game-header {

        height: 15px;

        gap: 1px;

        margin-top: 2px;

    }


    .game-header span {

        font-size: 5px;

        line-height: 6px;

        border-radius: 3px 3px 0 0;

    }


    .game-values {

        gap: 1px;

    }


    .game-column {

        min-height: 55px;

        padding: 2px 1px;

        border-radius: 0 0 3px 3px;

    }


    .game-position-title {

        font-size: 4px;

        line-height: 5px;

    }


    .game-position {

        font-size: 12px;

        line-height: 13px;

    }


    .game-score-title {

        margin-top: 1px;

        font-size: 3.8px;

        line-height: 4px;

    }


    .game-score {

        font-size: 9px;

        line-height: 10px;

    }


    /* SUMMARY */

    .summary-team {

        height: 21px;

        min-height: 21px;

        margin-top: 1px;

        padding: 1px 4px;

        gap: 3px;

    }


    .team-mark {

        width: 17px;

        height: 17px;

        font-size: 7px;

    }


    .summary-values {

        gap: 1px;

    }


    .summary-item {

        min-height: 18px;

        padding: 1px;

        font-size: 4px;

        line-height: 5px;

    }


    .summary-label {

        font-size: 8px;

        line-height: 8px;

    }


    /* FRAGGER */

    .fragger-title {

        margin-top: 6px;

        margin-bottom: 2px;

        padding: 3px 5px;

        border-left-width: 3px;

        border-radius: 4px;

        font-size: 9px;

        line-height: 10px;

    }


    .fragger-row {

        grid-template-columns:
            32px
            minmax(0, 1.4fr)
            minmax(0, 1fr)
            35px;

        height: 17px;

        min-height: 17px;

        padding: 1px 4px;

        font-size: 6px;

    }


    .fragger-row.header {

        height: 15px;

        min-height: 15px;

        font-size: 5px;

    }


    .fragger-pos {

        font-size: 7px;

    }


    .fragger-player {

        font-size: 6px;

    }


    .fragger-team {

        font-size: 5px;

    }


    .fragger-kills {

        font-size: 8px;

    }

}


/* ============================================================
   CELULARES PEQUEÑOS
   ============================================================ */

@media (max-width: 380px) {


    .container {

        padding: 3px;

    }


    .rank-card {

        padding: 4px;

        margin-bottom: 5px;

    }


    .game-column {

        min-height: 50px;

        padding: 1px;

    }


    .game-position {

        font-size: 11px;

        line-height: 12px;

    }


    .game-score-title {

        font-size: 3.5px;

        line-height: 4px;

    }


    .game-score {

        font-size: 8px;

        line-height: 9px;

    }


    .fragger-row {

        grid-template-columns:
            28px
            minmax(0, 1.4fr)
            minmax(0, 1fr)
            30px;

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

<div class="rank-card {rank_class}">


    <div class="rank-label">

        {label}

    </div>


    <div class="rank-number">

        {medal} {pos}

    </div>


    <div class="rank-team">

        {r["team"]}

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


"""


        # ====================================================
        # PLAYER HEADER
        # ====================================================

        html += """

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


<div class="summary-team">


    <div class="team-mark">

        M

    </div>


    <div>

        <div
            style="
            color:#ffffff;
            font-weight:900;
            font-size:9px;
            line-height:9px;
            "
        >

            TOTAL

        </div>


        <div
            style="
            color:#8f989c;
            font-size:6px;
            line-height:7px;
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
