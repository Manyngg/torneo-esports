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
   BASE
   ========================================================= */

* {
    box-sizing: border-box;
}

html {
    -webkit-text-size-adjust: 100%;
    text-size-adjust: 100%;
}

body {

    margin: 0;

    padding: 12px;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        radial-gradient(
            circle at top,
            #252a2d 0%,
            #111416 45%,
            #090a0b 100%
        );

    color: #ffffff;

    min-width: 0;
}


/* =========================================================
   MAIN
   ========================================================= */

.main-container {

    width: 100%;

    max-width: 1500px;

    margin: auto;
}


/* =========================================================
   TITLE
   ========================================================= */

.page-title {

    text-align: center;

    font-size: 28px;

    font-weight: 900;

    letter-spacing: 2px;

    margin-bottom: 18px;

    color: #dfff00;

    text-shadow:
        0 0 8px rgba(223,255,0,.35);
}


/* =========================================================
   RANK CARD
   ========================================================= */

.rank-box {

    display: grid;

    grid-template-columns:
        1fr
        1fr
        1fr
        1fr;

    align-items: center;

    min-height: 72px;

    border-radius: 12px 12px 0 0;

    border: 1px solid #353d40;

    background: #15191b;

    overflow: hidden;
}


/* =========================================================
   TOP COLORS
   ========================================================= */

.top1 {

    background:
        linear-gradient(
            135deg,
            #dfff00,
            #9fc900
        );

    color: #080a08;

    border-color: #dfff00;

    box-shadow:
        0 0 18px rgba(223,255,0,.20);
}


.top2 {

    background:
        linear-gradient(
            135deg,
            #eeeeee,
            #bcbcbc
        );

    color: #111111;

    border-color: #c8c8c8;
}


.top3 {

    background:
        linear-gradient(
            135deg,
            #cd7f32,
            #9f5d20
        );

    color: #ffffff;

    border-color: #cd7f32;
}


.other {

    background: #252b2e;

    color: #ffffff;
}


/* =========================================================
   RANK CONTENT
   ========================================================= */

.rank-label {

    display: none;
}


.rank-number {

    font-size: 24px;

    font-weight: 900;

    text-align: center;

    padding: 8px;
}


.rank-points {

    font-size: 25px;

    font-weight: 900;

    text-align: center;
}


.rank-points-label {

    font-size: 11px;

    font-weight: 800;

    text-align: center;

    text-transform: uppercase;
}


.rank-kills {

    font-size: 25px;

    font-weight: 900;

    text-align: center;
}


.rank-kills-label {

    font-size: 11px;

    font-weight: 800;

    text-align: center;

    text-transform: uppercase;
}


/* =========================================================
   TEAM AREA
   ========================================================= */

.team-area {

    background: #121517;

    border-left: 1px solid #353d40;

    border-right: 1px solid #353d40;

    border-bottom: 1px solid #30383b;

    overflow: hidden;
}


/* =========================================================
   TEAM NAME
   ========================================================= */

.rank-team {

    width: 100%;

    text-align: center;

    padding: 11px 8px 8px;

    font-size: 20px;

    font-weight: 900;

    letter-spacing: .8px;

    color: #dfff00;

    text-transform: uppercase;

    background: #15191b;

    border-bottom: 1px solid #353d40;

    text-shadow:
        0 0 8px rgba(223,255,0,.20);
}


/* =========================================================
   PLAYER HEADER
   ONLY PLAYER / AVG / KILLS
   ========================================================= */

.player-header {

    display: grid;

    grid-template-columns:
        2fr
        1fr
        1fr;

    align-items: center;

    background: #22282b;

    border-bottom: 1px solid #353d40;

    min-height: 34px;
}


.player-header > div {

    font-size: 10px;

    font-weight: 900;

    color: #9ba4a8;

    text-align: center;

    padding: 7px 4px;

    letter-spacing: .5px;
}


/* =========================================================
   PLAYER ROW
   ========================================================= */

.player-row {

    display: grid;

    grid-template-columns:
        2fr
        1fr
        1fr;

    min-height: 34px;

    align-items: center;

    border-bottom: 1px solid #30383b;

    background: #15191b;
}


.player-row:last-child {

    border-bottom: none;
}


.player-name {

    font-size: 13px;

    font-weight: 800;

    color: #ffffff;

    padding: 6px 8px;

    text-align: left;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;
}


.player-avg,
.player-kills {

    font-size: 13px;

    font-weight: 900;

    text-align: center;

    padding: 6px 4px;

    color: #ffffff;
}


.player-kills {

    color: #39ff14;
}


/* =========================================================
   GAMES AREA
   M1 / M2 / M3 HORIZONTAL
   ========================================================= */

.games-area {

    background: #202629;

    border-left: 1px solid #353d40;

    border-right: 1px solid #353d40;

    border-bottom: 1px solid #353d40;

    overflow-x: auto;

    overflow-y: hidden;
}


/* =========================================================
   GAME HEADER
   ========================================================= */

.game-header {

    display: grid;

    grid-template-columns:
        repeat(var(--games-count), 1fr);

    width: 100%;

    min-width: 300px;

    background: #22282b;

    border-bottom: 1px solid #353d40;
}


.game-header span {

    text-align: center;

    padding: 8px 4px;

    font-size: 13px;

    font-weight: 900;

    color: #dfff00;

    border-right: 1px solid #353d40;
}


.game-header span:last-child {

    border-right: none;
}


/* =========================================================
   GAME VALUES
   ========================================================= */

.game-values {

    display: grid;

    grid-template-columns:
        repeat(var(--games-count), 1fr);

    width: 100%;

    min-width: 300px;

    align-items: stretch;
}


/* =========================================================
   GAME COLUMN
   ========================================================= */

.game-column {

    min-width: 0;

    text-align: center;

    background: #15191b;

    border-right: 1px solid #30383b;

    padding-bottom: 7px;
}


.game-column:last-child {

    border-right: none;
}


.game-position-title,
.game-score-title {

    font-size: 8px;

    font-weight: 900;

    color: #8f989c;

    padding: 6px 2px 2px;

    line-height: 1.1;
}


.game-position {

    font-size: 20px;

    font-weight: 900;

    color: #ffffff;

    padding: 2px 2px 6px;
}


.game-score-title {

    padding-top: 3px;
}


.game-score {

    font-size: 16px;

    font-weight: 900;

    color: #39ff14;

    padding: 2px;
}


/* =========================================================
   DUPLICATE POSITION
   ========================================================= */

.duplicate-pos {

    color: #ff3030 !important;

    text-shadow:
        0 0 7px rgba(255,48,48,.5);
}


/* =========================================================
   SUMMARY
   ONE SINGLE KILLS TOTAL
   ========================================================= */

.summary-team {

    display: flex;

    align-items: center;

    gap: 10px;

    background: #202629;

    border-left: 1px solid #353d40;

    border-right: 1px solid #353d40;

    padding: 8px 10px;
}


.team-mark {

    width: 34px;

    height: 34px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 8px;

    background: #dfff00;

    color: #090a0b;

    font-weight: 900;
}


.summary-title {

    font-size: 12px;

    font-weight: 900;

    color: #ffffff;
}


.summary-subtitle {

    font-size: 8px;

    color: #8f989c;

    font-weight: 700;
}


/* =========================================================
   SINGLE TOTAL KILLS
   ========================================================= */

.summary-values {

    display: flex;

    justify-content: flex-end;

    background: #15191b;

    border: 1px solid #353d40;

    border-top: none;

    padding: 7px 10px;
}


.summary-item {

    min-width: 80px;

    text-align: center;

    padding: 4px 10px;

    border-left: 1px solid #353d40;

}


.summary-label {

    font-size: 18px;

    font-weight: 900;

    color: #39ff14;
}


.summary-item > div:last-child {

    font-size: 8px;

    font-weight: 900;

    color: #8f989c;

    text-transform: uppercase;
}


/* =========================================================
   FRAGGER
   ========================================================= */

.fragger-title {

    margin-top: 18px;

    margin-bottom: 8px;

    padding: 10px;

    border-radius: 10px 10px 0 0;

    background: #dfff00;

    color: #090a0b;

    font-size: 16px;

    font-weight: 900;

    text-align: center;

    letter-spacing: 1px;
}


.fragger-header {

    display: grid;

    grid-template-columns:
        .7fr
        2fr
        2fr
        1fr;

    background: #22282b;

    border: 1px solid #353d40;
}


.fragger-header > div {

    padding: 8px 5px;

    font-size: 10px;

    font-weight: 900;

    color: #9ba4a8;

    border-right: 1px solid #353d40;

    text-align: center;
}


.fragger-row {

    display: grid;

    grid-template-columns:
        .7fr
        2fr
        2fr
        1fr;

    background: #15191b;

    border-left: 1px solid #353d40;

    border-right: 1px solid #353d40;

    border-bottom: 1px solid #30383b;

    align-items: center;
}


.fragger-pos,
.fragger-player,
.fragger-team,
.fragger-kills {

    padding: 8px 5px;

    font-size: 12px;

    font-weight: 800;

    text-align: center;

    border-right: 1px solid #30383b;
}


.fragger-player {

    text-align: left;

    color: #ffffff;
}


.fragger-team {

    color: #9ba4a8;
}


.fragger-kills {

    color: #39ff14;

    border-right: none;
}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 700px) {

    body {

        padding: 5px;
    }


    .page-title {

        font-size: 20px;

        margin-bottom: 8px;
    }


    .rank-box {

        min-height: 55px;

        border-radius: 8px 8px 0 0;
    }


    .rank-number {

        font-size: 18px;

        padding: 5px;
    }


    .rank-points {

        font-size: 19px;
    }


    .rank-kills {

        font-size: 19px;
    }


    .rank-points-label,
    .rank-kills-label {

        font-size: 8px;
    }


    .rank-team {

        font-size: 15px;

        padding: 8px 5px 6px;
    }


    .player-header > div {

        font-size: 8px;

        padding: 5px 2px;
    }


    .player-row {

        min-height: 29px;
    }


    .player-name,
    .player-avg,
    .player-kills {

        font-size: 11px;

        padding: 5px 3px;
    }


    .game-header span {

        font-size: 10px;

        padding: 6px 2px;
    }


    .game-position-title,
    .game-score-title {

        font-size: 6px;

        padding-left: 1px;

        padding-right: 1px;
    }


    .game-position {

        font-size: 16px;

        padding-bottom: 4px;
    }


    .game-score {

        font-size: 13px;
    }


    .summary-team {

        padding: 6px;
    }


    .team-mark {

        width: 28px;

        height: 28px;
    }


    .summary-title {

        font-size: 10px;
    }


    .summary-subtitle {

        font-size: 7px;
    }


    .summary-values {

        padding: 5px;
    }


    .summary-item {

        min-width: 65px;

        padding: 3px 6px;
    }


    .summary-label {

        font-size: 15px;
    }


    .fragger-title {

        font-size: 13px;

        padding: 8px;

        margin-top: 10px;
    }


    .fragger-header > div,
    .fragger-pos,
    .fragger-player,
    .fragger-team,
    .fragger-kills {

        font-size: 9px;

        padding: 6px 3px;
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

        elif pos == 2:

            rank_class = "top2"

        elif pos == 3:

            rank_class = "top3"

        else:

            rank_class = "other"


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
        # CARD
        # ====================================================

        html += f"""

<div class="rank-box {rank_class}">


    <div class="rank-number">

        {medal} {pos}

    </div>


    <div class="rank-points">

        {r["score"]}

        <div class="rank-points-label">

            PUNTOS

        </div>

    </div>


    <div class="rank-kills">

        {r["kills"]}

        <div class="rank-kills-label">

            KILLS

        </div>

    </div>


    <div></div>


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


<!-- TOTAL -->

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


<div class="summary-values">


    <div class="summary-item">


        <div class="summary-label">

            """

        html += str(
            r["kills"]
        )

        html += """

        </div>


        <div>

            KILLS

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


    return html


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
