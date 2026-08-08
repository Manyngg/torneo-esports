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

    try:

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

html {
    width: 100%;
    min-width: 100%;
}

body {

    margin: 0;

    padding: 25px;

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
   MAIN CONTAINER
   ========================================================= */

.main-container {

    width: 100%;

    max-width: 1500px;

    min-width: 1100px;

    margin: 0 auto;

}


/* =========================================================
   TITLE
   ========================================================= */

.main-title {

    text-align: center;

    font-size: 36px;

    font-weight: 1000;

    letter-spacing: 4px;

    margin-bottom: 30px;

    color: #ffffff;

}


/* =========================================================
   RANK BOX
   ========================================================= */

.rank-box {

    position: relative;

    width: 100%;

    height: 145px;

    margin-top: 25px;

    padding: 20px;

    border-radius: 18px;

    background:
        linear-gradient(
            145deg,
            #252b2e,
            #121517
        );

    border: 1px solid #353d40;

    box-shadow:
        0 12px 25px rgba(0,0,0,.45),
        inset 0 1px 0 rgba(255,255,255,.04);

}


/* =========================================================
   RANK LABEL
   ========================================================= */

.rank-label {

    position: absolute;

    top: 13px;

    left: 22px;

    font-size: 12px;

    font-weight: 900;

    letter-spacing: 2px;

    color: #b8c0c3;

}


/* =========================================================
   RANK NUMBER
   ========================================================= */

.rank-number {

    position: absolute;

    left: 22px;

    bottom: 23px;

    font-size: 32px;

    font-weight: 1000;

    white-space: nowrap;

}


/* =========================================================
   POINTS
   ========================================================= */

.rank-points {

    position: absolute;

    right: 150px;

    top: 40px;

    font-size: 34px;

    font-weight: 1000;

    color: #dfff00;

    text-align: center;

    width: 100px;

}


.rank-points-label {

    position: absolute;

    right: 150px;

    top: 82px;

    width: 100px;

    text-align: center;

    font-size: 10px;

    font-weight: 800;

    color: #8d979b;

}


/* =========================================================
   KILLS
   ========================================================= */

.rank-kills {

    position: absolute;

    right: 35px;

    top: 40px;

    font-size: 34px;

    font-weight: 1000;

    color: #39ff14;

    text-align: center;

    width: 80px;

}


.rank-kills-label {

    position: absolute;

    right: 35px;

    top: 82px;

    width: 80px;

    text-align: center;

    font-size: 10px;

    font-weight: 800;

    color: #8d979b;

}


/* =========================================================
   PLAYERS
   ========================================================= */

.players-area {

    margin-top: 10px;

    border-radius: 12px;

    overflow: hidden;

    border: 1px solid #30383b;

    background: #171b1d;

}


.player-header,
.player-row {

    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        130px
        100px;

    width: 100%;

}


.player-header {

    height: 34px;

    align-items: center;

    background: #22282b;

    color: #9ba4a8;

    font-size: 10px;

    font-weight: 900;

    letter-spacing: 1px;

}


.player-header > div {

    padding: 0 15px;

}


.player-header > div:nth-child(2),
.player-header > div:nth-child(3) {

    text-align: right;

}


.player-row {

    min-height: 39px;

    align-items: center;

    border-top: 1px solid #282e31;

}


.player-name {

    padding-left: 15px;

    font-weight: 900;

    font-size: 13px;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;

}


.player-avg,
.player-kills {

    text-align: right;

    padding-right: 15px;

    font-size: 13px;

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

    margin-top: 10px;

    width: 100%;

    overflow: hidden;

    border-radius: 12px;

    border: 1px solid #30383b;

    background: #15191b;

}


.game-header,
.game-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            1fr
        );

    width: 100%;

}


.game-header {

    min-height: 42px;

    background: #22282b;

    border-bottom: 1px solid #343c3f;

}


.game-header span {

    display: flex;

    align-items: center;

    justify-content: center;

    min-width: 0;

    font-size: 13px;

    font-weight: 1000;

    color: #ffffff;

    letter-spacing: 1px;

    border-right: 1px solid #343c3f;

}


.game-header span:last-child {

    border-right: none;

}


.game-values {

    min-height: 72px;

}


.game-column {

    min-width: 0;

    display: flex;

    flex-direction: column;

    align-items: center;

    justify-content: center;

    border-right: 1px solid #2c3336;

}


.game-column:last-child {

    border-right: none;

}


.game-position {

    font-size: 20px;

    font-weight: 1000;

    line-height: 1;

    color: #ffffff;

}


.game-score {

    margin-top: 8px;

    font-size: 13px;

    font-weight: 900;

    color: #dfff00;

}


.duplicate-pos {

    color: #ff3131 !important;

}


/* =========================================================
   SUMMARY
   ========================================================= */

.summary-area {

    margin-top: 10px;

    display: grid;

    grid-template-columns:
        230px
        minmax(0, 1fr);

    width: 100%;

    min-height: 72px;

    border-radius: 12px;

    overflow: hidden;

    border: 1px solid #30383b;

    background: #15191b;

}


.summary-team {

    display: flex;

    align-items: center;

    gap: 12px;

    padding: 12px;

    background: #202629;

}


.team-mark {

    width: 40px;

    height: 40px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 10px;

    background: #2c3336;

    color: #dfff00;

    font-size: 20px;

    font-weight: 1000;

}


.summary-values {

    display: grid;

    grid-template-columns:
        repeat(
            var(--games-count),
            1fr
        );

    width: 100%;

}


.summary-item {

    display: flex;

    flex-direction: column;

    align-items: center;

    justify-content: center;

    border-right: 1px solid #2c3336;

    font-size: 9px;

    color: #7f898d;

}


.summary-item:last-child {

    border-right: none;

}


.summary-label {

    color: #ffffff;

    font-size: 17px;

    font-weight: 1000;

    margin-bottom: 3px;

}


/* =========================================================
   FRAGGER
   ========================================================= */

.fragger-container {

    width: 100%;

    margin-top: 35px;

    border-radius: 15px;

    overflow: hidden;

    border: 1px solid #30383b;

    background: #15191b;

}


.fragger-title {

    padding: 16px 20px;

    font-size: 18px;

    font-weight: 1000;

    letter-spacing: 1px;

    background: #202629;

    color: #dfff00;

}


.fragger-row {

    display: grid;

    grid-template-columns:
        80px
        minmax(0, 1fr)
        minmax(0, 1fr)
        110px;

    width: 100%;

    min-height: 45px;

    align-items: center;

    border-top: 1px solid #292f32;

}


.fragger-row.header {

    min-height: 38px;

    background: #22282b;

    border-top: none;

    color: #8f989c;

    font-size: 10px;

    font-weight: 1000;

    letter-spacing: 1px;

}


.fragger-row > div {

    min-width: 0;

    padding: 0 15px;

}


.fragger-pos {

    font-size: 15px;

    font-weight: 1000;

}


.fragger-player {

    font-size: 13px;

    font-weight: 900;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;

}


.fragger-team {

    font-size: 12px;

    font-weight: 800;

    color: #9ca5a8;

    white-space: nowrap;

    overflow: hidden;

    text-overflow: ellipsis;

}


.fragger-kills {

    text-align: right;

    font-size: 16px;

    font-weight: 1000;

    color: #39ff14;

}


/* =========================================================
   TOP 1
   ========================================================= */

.top1 {

    border-color: #dfff00;

    box-shadow:
        0 0 18px rgba(223,255,0,.12),
        0 12px 25px rgba(0,0,0,.45);

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


.top2 .rank-label {

    display: none;

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
   OTHER
   ========================================================= */

.other {

    border-color: #343b3e;

}


/* =========================================================
   NO ZOOM / FIXED STRUCTURE
   ========================================================= */

@media (max-width: 900px) {

    body {

        padding: 10px;

    }

    .main-container {

        min-width: 1100px;

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


# ============================================================
# RANK CARDS
# ============================================================

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

        <div>PLAYER</div>

        <div>AVG KILLS</div>

        <div>KILLS</div>

    </div>

"""


    # ========================================================
    # PLAYERS
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


    # ========================================================
    # GAMES
    # ========================================================

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


    html += f"""

    </div>

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


    # ========================================================
    # SUMMARY
    # ========================================================

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


# ============================================================
# FRAGGER TABLE
# ============================================================

html += """

<div class="fragger-container">

    <div class="fragger-title">

        🔥 FRAGGER TABLE

    </div>

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
