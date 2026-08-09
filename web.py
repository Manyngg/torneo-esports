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
   BASE
   ============================================================ */

* {
    box-sizing: border-box;
}

html,
body {

    margin: 0;
    padding: 0;

    width: 100%;

    overflow-x: hidden;

}

body {

    font-family: Arial, Helvetica, sans-serif;

}


/* ============================================================
   RANK LABEL
   ============================================================ */

.rank-label {

    font-size: 8px !important;

    line-height: 9px !important;

    margin: 2px 0 !important;

}


/* ============================================================
   RANK NUMBER
   ============================================================ */

.rank-number {

    font-size: 20px !important;

    line-height: 22px !important;

    margin: 1px 0 !important;

}


/* ============================================================
   POINTS
   ============================================================ */

.rank-points {

    font-size: 17px !important;

    line-height: 18px !important;

    margin: 1px 0 !important;

}

.rank-points-label {

    font-size: 7px !important;

    line-height: 8px !important;

    margin: 0 !important;

}


/* ============================================================
   KILLS
   ============================================================ */

.rank-kills {

    font-size: 13px !important;

    line-height: 14px !important;

    margin: 1px 0 !important;

}

.rank-kills-label {

    font-size: 7px !important;

    line-height: 8px !important;

    margin: 0 !important;

}


/* ============================================================
   PLAYER HEADER
   ============================================================ */

.player-header {

    min-height: 20px !important;

    height: 20px !important;

    padding: 2px 5px !important;

    font-size: 7px !important;

    line-height: 8px !important;

    margin: 2px 0 0 0 !important;

}


/* ============================================================
   PLAYER ROW
   ============================================================ */

.player-row {

    min-height: 21px !important;

    height: 21px !important;

    padding: 2px 5px !important;

    margin: 0 !important;

    font-size: 9px !important;

    line-height: 10px !important;

}

.player-name {

    font-size: 9px !important;

    line-height: 10px !important;

}

.player-avg {

    font-size: 8px !important;

    line-height: 9px !important;

}

.player-kills {

    font-size: 9px !important;

    line-height: 10px !important;

}


/* ============================================================
   GAME HEADER
   ============================================================ */

.game-header {

    min-height: 20px !important;

    height: 20px !important;

    margin: 2px 0 0 0 !important;

    gap: 1px !important;

    font-size: 7px !important;

    line-height: 8px !important;

}

.game-header span {

    padding: 2px 1px !important;

    font-size: 7px !important;

    line-height: 8px !important;

    min-width: 0 !important;

}


/* ============================================================
   GAME VALUES
   ============================================================ */

.game-values {

    gap: 1px !important;

    margin: 0 !important;

    padding: 0 !important;

}


/* ============================================================
   GAME COLUMN
   ============================================================ */

.game-column {

    min-width: 0 !important;

    padding: 3px 2px !important;

    margin: 0 !important;

    border-radius: 4px !important;

    min-height: 72px !important;

}


/* ============================================================
   POSITION TITLE
   ============================================================ */

.game-position-title {

    font-size: 6px !important;

    line-height: 7px !important;

    white-space: nowrap;

    margin: 0 0 1px 0 !important;

    padding: 0 !important;

}


/* ============================================================
   POSITION
   ============================================================ */

.game-position {

    font-size: 15px !important;

    line-height: 17px !important;

    margin: 0 !important;

    padding: 0 !important;

    min-height: 17px !important;

}


/* ============================================================
   MULTIPLIER TITLE
   ============================================================ */

.game-score-title {

    font-size: 5.5px !important;

    line-height: 6px !important;

    margin: 3px 0 1px 0 !important;

    padding: 0 !important;

}


/* ============================================================
   SCORE
   ============================================================ */

.game-score {

    font-size: 12px !important;

    line-height: 14px !important;

    margin: 0 !important;

    padding: 0 !important;

}


/* ============================================================
   SUMMARY TEAM
   ============================================================ */

.summary-team {

    min-height: 27px !important;

    height: 27px !important;

    padding: 3px 5px !important;

    margin: 2px 0 0 0 !important;

}

.team-mark {

    font-size: 10px !important;

}

.summary-team div {

    line-height: 9px !important;

}


/* ============================================================
   SUMMARY VALUES
   ============================================================ */

.summary-values {

    gap: 1px !important;

    margin: 0 !important;

    padding: 0 !important;

}

.summary-item {

    min-height: 25px !important;

    padding: 2px !important;

    font-size: 6px !important;

    line-height: 7px !important;

}

.summary-label {

    font-size: 10px !important;

    line-height: 11px !important;

}


/* ============================================================
   FRAGGER TITLE
   ============================================================ */

.fragger-title {

    font-size: 12px !important;

    line-height: 14px !important;

    margin: 6px 0 2px 0 !important;

    padding: 3px 5px !important;

}


/* ============================================================
   FRAGGER ROW
   ============================================================ */

.fragger-row {

    min-height: 22px !important;

    height: 22px !important;

    padding: 2px 5px !important;

    margin: 0 !important;

    font-size: 8px !important;

    line-height: 9px !important;

}

.fragger-row.header {

    min-height: 19px !important;

    height: 19px !important;

    font-size: 7px !important;

    line-height: 8px !important;

}


/* ============================================================
   FRAGGER CELLS
   ============================================================ */

.fragger-pos {

    font-size: 9px !important;

    line-height: 10px !important;

}

.fragger-player {

    font-size: 8px !important;

    line-height: 9px !important;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

}

.fragger-team {

    font-size: 7px !important;

    line-height: 8px !important;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

}

.fragger-kills {

    font-size: 10px !important;

    line-height: 11px !important;

}


/* ============================================================
   MOBILE
   ============================================================ */

@media (max-width: 600px) {


    body {

        font-size: 9px;

    }


    .rank-label {

        font-size: 7px !important;

    }


    .rank-number {

        font-size: 17px !important;

        line-height: 18px !important;

    }


    .rank-points {

        font-size: 14px !important;

        line-height: 15px !important;

    }


    .rank-kills {

        font-size: 11px !important;

        line-height: 12px !important;

    }


    /* PLAYERS */

    .player-header {

        height: 18px !important;

        min-height: 18px !important;

        font-size: 6px !important;

    }


    .player-row {

        height: 19px !important;

        min-height: 19px !important;

        font-size: 8px !important;

    }


    .player-name {

        font-size: 8px !important;

    }


    .player-avg,
    .player-kills {

        font-size: 7px !important;

    }


    /* GAMES */

    .game-header {

        height: 17px !important;

        min-height: 17px !important;

    }


    .game-header span {

        font-size: 6px !important;

        line-height: 7px !important;

    }


    .game-column {

        min-height: 63px !important;

        padding: 2px 1px !important;

        border-radius: 3px !important;

    }


    .game-position-title {

        font-size: 5px !important;

        line-height: 6px !important;

    }


    .game-position {

        font-size: 13px !important;

        line-height: 14px !important;

    }


    .game-score-title {

        font-size: 4.5px !important;

        line-height: 5px !important;

        margin-top: 2px !important;

    }


    .game-score {

        font-size: 10px !important;

        line-height: 11px !important;

    }


    /* SUMMARY */

    .summary-team {

        height: 23px !important;

        min-height: 23px !important;

        padding: 2px 4px !important;

    }


    .summary-item {

        min-height: 21px !important;

        font-size: 5px !important;

    }


    .summary-label {

        font-size: 9px !important;

        line-height: 9px !important;

    }


    /* FRAGGER */

    .fragger-title {

        font-size: 10px !important;

        line-height: 11px !important;

        padding: 2px 4px !important;

        margin-top: 4px !important;

    }


    .fragger-row {

        height: 19px !important;

        min-height: 19px !important;

        font-size: 7px !important;

    }


    .fragger-row.header {

        height: 17px !important;

        min-height: 17px !important;

        font-size: 6px !important;

    }


    .fragger-pos {

        font-size: 8px !important;

    }


    .fragger-player {

        font-size: 7px !important;

    }


    .fragger-team {

        font-size: 6px !important;

    }


    .fragger-kills {

        font-size: 9px !important;

    }

}


/* ============================================================
   VERY SMALL PHONES
   ============================================================ */

@media (max-width: 380px) {


    .game-column {

        padding: 2px 0 !important;

        min-height: 58px !important;

    }


    .game-position {

        font-size: 12px !important;

    }


    .game-score {

        font-size: 9px !important;

    }


    .game-position-title {

        font-size: 4.5px !important;

    }


    .game-score-title {

        font-size: 4px !important;

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
