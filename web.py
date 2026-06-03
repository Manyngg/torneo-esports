import discord
import requests
import re

TOKEN = "TU_TOKEN"
URL = "https://torneo-esports.onrender.com"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


# =========================
# REQUEST
# =========================

def enviar(data, endpoint):

    try:
        url = URL.rstrip("/") + endpoint

        r = requests.post(
            url,
            json=data,
            timeout=10
        )

        print("WEB STATUS:", r.status_code)
        print("WEB RESPONSE:", r.text)

        return r.status_code, r.text

    except Exception as e:
        print("ERROR REQUEST:", e)
        return None, str(e)


# =========================
# BOT
# =========================

@client.event
async def on_message(message):

    if message.author.bot:
        return

    content = message.content

    print("RECIBI:", repr(content))


    # =========================
    # BORRAR TORNEO
    # =========================

    if content.lower().startswith("!borrar"):

        try:

            status, response = enviar({}, "/borrar")

            if status == 200:
                await message.channel.send(
                    "🧹 Torneo borrado correctamente\n"
                    "📦 Toda la información fue eliminada"
                )
            else:
                await message.channel.send(
                    f"❌ Error al borrar (HTTP {status})\n{response}"
                )

        except Exception as e:
            await message.channel.send(f"❌ Error borrar: {e}")

        return


    # =========================
    # REPORTE
    # =========================

    if content.startswith("!reporte"):

        try:

            lineas = content.splitlines()

            partida = int(re.sub(r"\D", "", lineas[0]))
            equipo = lineas[1].replace("Equipo:", "").strip()
            posicion = int(re.sub(r"\D", "", lineas[2]))

            jugadores = []
            kills = []

            for linea in lineas[3:]:

                match = re.search(r"(.+?)\s*(\d+)$", linea)

                if not match:
                    continue

                jugadores.append(match.group(1).strip())
                kills.append(int(match.group(2)))

            data = {
                "equipo": equipo,
                "game": partida,
                "placement": posicion,
                "jugadores": jugadores,
                "kills": kills
            }

            status, response = enviar(data, "/report")

            if status == 200:
                await message.channel.send(
                    f"✅ Reporte Guardado\n"
                    f"Equipo: {equipo}\n"
                    f"Partida: {partida}"
                )
            else:
                await message.channel.send(
                    f"❌ Error API (HTTP {status})\n{response}"
                )

        except Exception as e:
            await message.channel.send(f"❌ Error formato\n{e}")

        return


    # =========================
    # MODIFICAR
    # =========================

    if content.startswith("!modificar"):

        try:

            lineas = content.splitlines()

            partida = int(re.sub(r"\D", "", lineas[0]))
            equipo = lineas[1].replace("Equipo:", "").strip()
            posicion = int(re.sub(r"\D", "", lineas[2]))

            jugadores = []
            kills = []

            for linea in lineas[3:]:

                match = re.search(r"(.+?)\s*(\d+)$", linea)

                if not match:
                    continue

                jugadores.append(match.group(1).strip())
                kills.append(int(match.group(2)))

            data = {
                "equipo": equipo,
                "game": partida,
                "placement": posicion,
                "jugadores": jugadores,
                "kills": kills
            }

            status, response = enviar(data, "/modificar")

            if status == 200:
                await message.channel.send(
                    f"✏️ Modificado correctamente\n"
                    f"Equipo: {equipo}\n"
                    f"Partida: {partida}"
                )
            else:
                await message.channel.send(
                    f"❌ Error API (HTTP {status})\n{response}"
                )

        except Exception as e:
            await message.channel.send(f"❌ Error modificar\n{e}")

        return


client.run(TOKEN)
