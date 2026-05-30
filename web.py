fragger = {}

for team,data in equipos.items():

    for player,stats in data["players"].items():

        if player not in fragger:

            fragger[player] = {

                "team":team,

                "kills":0

            }

        fragger[player]["kills"] += stats["kills"]


fraggers = sorted(

    fragger.items(),

    key=lambda x:x[1]["kills"],

    reverse=True

)
