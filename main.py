# LIBARIES
import discord
from discord.ext import commands
from credentials import *
import re
import json
import random
import mysql
import mysql.connector as mysql
import traceback
import datetime

botdb = mysql.connect(
host="192.168.55.10",
user="iqbot",
password=database_password,
database="iqbot"
)
if botdb:
    botdbc = botdb.cursor(dictionary=True,buffered=True)

    # Discord Client Init
    client = discord.Client()

    # DISCORD BOT START
    @client.event
    async def on_ready():
        print(client.user)

        # STATUS SETZEN
        game = discord.Game("mit der API")
        await client.change_presence(status=discord.Status.online, activity=game)

        # ALLE SERVER AUSGEBEN
        print('Aktuell auf ' + str(len(client.guilds)) + ' Servern')

    # FUNKTIONEN
    def mention(author_id):
        return "<@" + str(author_id) + ">"
    
    async def send_error_msg(temp_msg, message):
        response=discord.Embed(title="❌ " + temp_msg, color=0xff0000)
        response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
        await message.channel.send(embed = response)
        response = ""
        message = ""
        temp_msg = ""
        return

    ## Ein Feld das anzeigt werden kann aus dem JSON erzeugen
    def field(data):
        count = 0
        finished_message = ""
        
        for key, value in data.items():
            for key2, i in value.items():
                if i == "0":
                    if count == 2:
                        finished_message+="| ⚪ |\n"
                        count = 0
                    else:
                        finished_message+="| ⚪ "
                        count+=1
                elif i == "1":
                    if count == 2:
                        finished_message+="| 🔴 |\n"
                        count = 0
                    else:
                        finished_message+="| 🔴 "
                        count+=1
                elif i == "2":
                    if count == 2:
                        finished_message+="| 🔵 |\n"
                        count = 0
                    else:
                        finished_message+="| 🔵 "
                        count+=1
        return "" + finished_message
    
    async def new_request(temp_guild_id, temp_channel_id, temp_challanger_id, temp_opponent_id, rematch):
        # Hier wird festgelegt welcher Nuitzer welcher ist
        opponent = await client.fetch_user(temp_opponent_id)
        challanger = await client.fetch_user(temp_challanger_id)
        channel = client.get_channel(temp_channel_id)

        if opponent.id == challanger.id:
            error_msg = "Cant send yourself a battle request!"

        botdbc.execute("SELECT * FROM battlerequests WHERE guild_id = " + str(temp_guild_id) + " AND opponent_id = " + str(temp_opponent_id) + " ORDER BY date")
        battle_request = botdbc.fetchall()
        if battle_request is not None:
            for i in battle_request:
                if i["date"] < datetime.datetime.now()-datetime.timedelta(seconds=30):
                    sql_deleterequest = "DELETE FROM battlerequests WHERE id = " + str(i["id"])
                    botdbc.execute(sql_deleterequest)
                    botdb.commit()

        # Hier wird in der Datenbank nachgeschaut, ob der Nutzer schon eine aktive Anfrage hat
        botdbc.execute("SELECT challanger_id FROM battlerequests WHERE guild_id = " + str(temp_guild_id) + " AND opponent_id = " + str(opponent.id) + " OR challanger_id = " + str(challanger.id))
        check_battle = botdbc.fetchone()

        # Wenn der Nutzer keine Anfrage hat, dann
        if check_battle is None:

            if rematch:
                temp_title = "Rematch:"
            else:
                temp_title = "Challange:"

            # Nachricht wird als Embed erstellt und geschickt
            response=discord.Embed(title=temp_title, color=0x00ff00)
            response.add_field(name= challanger.name + " vs " + opponent.name, value="Their battle will be legendary!", inline=False)
            response.add_field(name="To accept this battle:", value="!tictactoe accept", inline=False)
            response.set_author(name=challanger.name,icon_url=challanger.avatar_url)
            temp_msg = await channel.send(embed = response)
            await temp_msg.add_reaction("✅")
            response = ""

            sql_battlerequest = "INSERT INTO battlerequests (guild_id, opponent_id, challanger_id, message_id) VALUES (%s, %s, %s, %s)"
            val_battlerequest = (temp_guild_id, opponent.id, challanger.id, temp_msg.id)
            botdbc.execute(sql_battlerequest, val_battlerequest)
            botdb.commit()

        # Falls der Nutzer bereits eine Anfrage hat        
        else:
            error_msg = "This user is currently in a battle!"

    async def init_game(temp_guild_id, temp_author_id, temp_channel_id):
        # Schaue in der Datenbank nach, ob eine Anfrage an den Nutzer geschickt wurde  
        guild = client.get_guild(temp_guild_id)
        channel = client.get_channel(temp_channel_id)
        botdbc.execute("SELECT challanger_id FROM battlerequests WHERE guild_id = " + str(guild.id) + " AND opponent_id = " + str(temp_author_id))
        battlerequest = botdbc.fetchone()

        if battlerequest is None:

            # Keine Anfrage wurde gefunden, also error!
            error_msg = "You dont have a open battle request! Challange somebody with: !tictactoe @USERNAME"

        else:
            # Eine Anfrage wurde gefunden, jetzt wird ein Spiel initiiert!
            # Schauen ob Nutzer auch teil des Servers ist (für Multiple Server funktionalität)
            if await guild.fetch_member(battlerequest["challanger_id"]) is not None:

                # Nutzer werden festgelegt (Diesen Prozess reduzieren)
                challanger = await client.fetch_user(battlerequest["challanger_id"])
                opponent = await client.fetch_user(temp_author_id)

                # Fügt hinzu, wer Challanger (c) und wer Oponent (o)
                starterlist = ["o", "c"]
                starter = random.choice(starterlist)

                # Festlegen wer wer ist u. in Datenbank schreiben (Prozess reduzieren)
                if starter == "o":
                    turn_id = opponent.id
                elif starter == "c":
                    turn_id = challanger.id

                # Anfrage des Battles wird aus der Datenbank gelöscht
                sql_deleterequest = "DELETE FROM battlerequests WHERE guild_id = " + str(guild.id) + " AND challanger_id = " + str(challanger.id) + " AND opponent_id = " + str(opponent.id)
                botdbc.execute(sql_deleterequest)
                botdb.commit()

                # leeres Feld wird als json festgelegt
                empty_json_field = '{"A": {"1": "0", "2": "0", "3": "0"}, "B": {"1": "0", "2": "0", "3": "0"}, "C": {"1": "0", "2": "0", "3": "0"}}'
                empty_field = field(json.loads(empty_json_field))

                # Alle Informationen werden in as Aktive Battle Datenbank geschrieben
                sql_battle = "INSERT INTO activebattle (guild_id, opponent_id, challanger_id, json_field, turn_id) VALUES (%s, %s, %s, %s, %s)"
                val_battle = (guild.id, opponent.id, challanger.id, empty_json_field, turn_id)
                botdbc.execute(sql_battle, val_battle)
                botdb.commit()

                # Die Antwort auf die Nachricht mit dem aktiven Spielfeld als Inhalt wird als Embed hier vorbereitet und geschickt
                response=discord.Embed(title="Active Battle", color=0xb00000)
                response.set_author(name=opponent.name,icon_url=opponent.avatar_url)
                response.add_field(name="🔴" + challanger.name + " vs 🔵" + opponent.name, value=empty_field, inline=True)
                response.add_field(name="Usage:", value="| A1 | A2 | A3 |\n| B1 | B2 | B3 |\n| C1 | C2 | C3 |\nTo place your block on a field, write the field number", inline=False)
                response.add_field(name="Whose turn is it:", value=(await client.fetch_user(turn_id)).name, inline=False)
                response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                await channel.send(embed = response)
                response = ""

    @client.event
    async def on_message(message):

        # NICHT DIR SELBST ANTWORTEN
        if message.author == client.user:
            return
            
        if message.author.bot:
            return
        
        # Wenn Nachricht länger als Datenbank Limit ist, wird sie ignoriert!
        if len(message.content) > 254:
            return

        # TICTACTOE Init

        # LISTROLES COMMAND (zählt alle Rollen auf einem Server auf)
        if message.content == "!listroles":
            # Füge Haken zu nachricht des sender (als bestätigung)
            await message.add_reaction("✅")

            # Hole alle Rollen auf diesem Server ein
            guild = client.get_guild(message.guild.id)
            guild_roles = []

            # Gebe die Rollen umgekehrt aus (umgekehrt weil sie sonst nicht in der Richtung wo es in der Teilnehmerleiste ist ausgegeben werden)
            for role in reversed(guild.roles):
                # Rollen werden einzeln zu der variable hinzugefügt
                guild_roles.append(role.name + "\n")

            # Die Antwort wird als Embed mit allen Rollen erstellt und geschickt
            response = discord.Embed(
                title = "List of all roles:",
                description = ''.join(guild_roles),
                colour = discord.Colour.blue()
            )
            await message.channel.send("Here is a list of all roles on this server",embed = response)
            response = ""

        elif message.content == "!test":
            response=discord.Embed(title="{null}", color=0xb00000)
            response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
            response.add_field(name="🔴" + "{null}" + " vs 🔵" + "{null}", value="{null}", inline=True)
            response.add_field(name="Usage:", value="This\nis\na\ntestcommand\nlol", inline=False)
            response.add_field(name="Whose turn is it:", value="{null}", inline=False)
            response.set_footer(text="[loooooooooooooooooool]")
            await message.channel.send(":dancedancedance: ",embed = response)
            response = ""

        elif message.content.startswith("!tictactoe"):

            # Der Command "tictactoe" wird von der Nachricht entfernt, damit am Ende nur die Parameter übrig bleiben
            arg1 = (message.content).replace("!tictactoe ","")
            
            # Variablen festlegen
            error_msg = False

            # Schauen ob ein Nutzer markiert wurde (@) und ob "accept" geschickt wurde
            if "accept" in arg1 and not "@" in arg1:
                await init_game(message.guild.id, message.author.id, message.channel.id)

            # Battle verlassen
            elif arg1 == "leave":
                botdbc.execute("SELECT * FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND opponent_id = " + str(message.author.id) + " OR challanger_id = " + str(message.author.id))
                activebattle = botdbc.fetchone()

                if activebattle is not None:
                    # Falls kein Aktives Battle vorhanden ist wird die Nachricht einfach ignoriert
                    error_msg = False
                    opponent = await client.fetch_user(activebattle["opponent_id"])
                    challanger = await client.fetch_user(activebattle["challanger_id"])

                    sql_delete_battle = "DELETE FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND challanger_id = " + str(activebattle["challanger_id"]) + " AND opponent_id = " + str(activebattle["opponent_id"])
                    botdbc.execute(sql_delete_battle)
                    botdb.commit()
                    await send_error_msg("You left the battle", message)
                else:
                    await send_error_msg("You cant leave any battle", message)

            # Eine Anfrage wird geschickt
            else:

                # Das angegebene Argument (arg1) bei Commandausführung löscht alles bis auf Zahlen (/D) aus dem String,
                # um so nur die NutzerID des markierten zu bekommen
                arg1 = re.sub("\D", "", arg1)
                
                # Checkt ob eine Nutzer ID vorhanden ist (falls nicht wird ein error zurück gegeben)
                if arg1 == "":
                    error_msg = "User not found"
                
                else:
                    # Hier wird geprüft ob der Nutzer tatsälich auf dem DiscordServer ist u. existiert.
                    try:
                        if await message.guild.fetch_member(arg1) is not None:
                            await new_request(message.guild.id, message.channel.id, message.author.id, arg1, False)
                        
                    # Falls der Nutzer nicht gefunden wurde
                    except:
                        traceback.print_exc()
                        error_msg = "Exception Error!"
            
            # Hier werden Nachrichten verschickt die mit der Variable "error vorher festgelegt wurden"

            # Checkt das Variable "error" nicht "false" ist
            if error_msg:

                # Schickt error Nachricht als Embed
                await send_error_msg(error_msg, message)
            return
        
        # Spielsteuerung
        uppermsg = (message.content).upper()
        if uppermsg == "A1" or "A2" or "A3" or "B1" or "B2" or "B3" or "C1" or "C2" or "C3":
            # In der Datenbank wird geschaut ob der NachrichtenAutor auch ein aktives Battle auf der Guild hat
            botdbc.execute("SELECT * FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND turn_id = " + str(message.author.id))
            activebattle = botdbc.fetchone()

            if activebattle is not None:
                # Falls kein Aktives Battle vorhanden ist wird die Nachricht einfach ignoriert
                error_msg = False
                opponent = await client.fetch_user(activebattle["opponent_id"])
                challanger = await client.fetch_user(activebattle["challanger_id"])
                data = json.loads(activebattle["json_field"])
            else:
                return

            if data[uppermsg[0]][uppermsg[1]] == "0":
                if activebattle["turn_id"] == str(opponent.id):
                    data[uppermsg[0]][uppermsg[1]] = "2"
                elif activebattle["turn_id"] == str(challanger.id):
                    data[uppermsg[0]][uppermsg[1]] = "1"
            else:
                error_msg = "Nein"
                    
            ### Check ob jemand gewonnen hat (evtl schöner??)
            winner = False
            for i in "ABC":
                if data[i]["1"] == data[i]["2"] == data[i]["3"] != "0":
                    if data[i]["1"] and data[i]["2"] and data[i]["3"] == "1":
                        winner = challanger

                    elif data[i]["1"] and data[i]["2"] and data[i]["3"] == "2":
                        winner = opponent

            for ii in "123":
                if data["A"][ii] == data["B"][ii] == data["C"][ii] != "0":
                    if data["A"][ii] and data["B"][ii] and data["C"][ii] == "1":
                        winner = challanger
                    elif data["A"][ii] and data["B"][ii] and data["C"][ii] == "2":
                        winner = opponent

            if data["A"]["1"] == data["B"]["2"] == data["C"]["3"] != "0" or data["A"]["3"] == data["B"]["2"] == data["C"]["1"] != "0":
                if data["B"]["2"] == "1":
                    winner = challanger
                elif data["B"]["2"] == "2":
                    winner = opponent

            tie = False
            if not winner:
                tie_number = 0
                counter = int()
                for key, value in data.items():
                    for key2, i in value.items():
                        if i == "0":
                            tie = False
                            break
                        elif i == "1" or "2":
                            counter+=1
                if counter == 9:
                    tie = True

            ### ENDE check ob jemand gewonnen hat

            if not winner and not error_msg and not tie:
                # Tauschen der Rollen jenachdem wer dran ist (pls change)
                field_send = field(data)
                
                if activebattle["turn_id"] == str(opponent.id):
                    turn_id = challanger.id
                elif activebattle["turn_id"] == str(challanger.id):
                    turn_id = opponent.id
            
                # Aktualisiertes Feld wird in die Datenbank geschrieben
                sql_update_active_battle = "UPDATE activebattle SET json_field = %s, turn_id = %s WHERE challanger_id = %s AND guild_id = %s AND opponent_id = %s"
                val_update_active_battle = (json.dumps(data), turn_id, activebattle["challanger_id"], message.guild.id, activebattle["opponent_id"])
                botdbc.execute(sql_update_active_battle, val_update_active_battle)
                botdb.commit()

                # Aktualisiertes Feld wird ausgegeben
                response=discord.Embed(title="Active Battle", color=0xb00000)
                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                response.add_field(name="🔴" + challanger.name + " vs 🔵" + opponent.name, value=field_send, inline=True)
                response.add_field(name="Usage:", value="| A1 | A2 | A3 |\n| B1 | B2 | B3 |\n| C1 | C2 | C3 |\nTo place your block on a field, write the field number", inline=False)
                response.add_field(name="Whose turn is it:", value=(await client.fetch_user(turn_id)).name, inline=False)
                response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                await message.channel.send(embed = response)
                response = ""

            
            # Battle Win
            elif winner and not error_msg and not tie:

                # Tausche Rollen, je nach dem Wer gerade dran ist
                field_send = field(data)

                # Lösche Aktives Battle aus der Datenbank
                sql_delete_battle = "DELETE FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND challanger_id = " + str(challanger.id) + " AND opponent_id = " + str(opponent.id)
                botdbc.execute(sql_delete_battle)
                botdb.commit()

                sql_game_log = "INSERT INTO game_log (guild_id, challanger_id, opponent_id, winner_id, message_id) VALUES (%s, %s, %s, %s, %s)"
                sql_game_log_values = (message.guild.id, challanger.id, opponent.id, winner.id, message.id)
                botdbc.execute(sql_game_log, sql_game_log_values)
                botdb.commit()

                # Winner Nachricht wird als Embed erstellt und gesendet
                response=discord.Embed(title=winner.name + " has won!", color=0xb00000)
                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                response.add_field(name="🔴" + challanger.name + " vs 🔵" + opponent.name, value=field_send, inline=True)
                response.set_footer(text="Press 🔄 for a rematch (available for 10 seconds)")
                temp_msg = await message.channel.send(embed = response)
                await temp_msg.add_reaction("🔄")
                response = ""

            # Falls Unentschieden    
            elif tie:
                # Tausche Rollen je nach dem wer dran ist
                field_send = field(data)

                # Lösche Aktives Battle aus der Datenbank
                sql_delete_battle = "DELETE FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND challanger_id = " + str(activebattle["challanger_id"]) + " AND opponent_id = " + str(activebattle["opponent_id"])
                botdbc.execute(sql_delete_battle)
                botdb.commit()

                sql_game_log = "INSERT INTO game_log (guild_id, challanger_id, opponent_id, winner_id, message_id) VALUES (%s, %s, %s, %s, %s)"
                sql_game_log_values = (message.guild.id, challanger.id, opponent.id, winner.id, message.id)
                botdbc.execute(sql_game_log, sql_game_log_values)
                botdb.commit()

                # Erstelle Untenschieden Nachricht und schicke sie ab
                response=discord.Embed(title="Tie!", color=0xb00000)
                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                response.add_field(name="🔴" + challanger.name + " vs 🔵" + opponent.name, value=field_send, inline=True)
                response.set_footer(text="Press 🔄 for a rematch (available for 10 seconds)")
                temp_msg = await message.channel.send(embed = response)
                await temp_msg.add_reaction("🔄")
                response = ""

            # Erstelle und sende Error Nachricht, falls einer aufgetreten sein sollte    
            elif error_msg:
                await send_error_msg(error_msg, message)
            return

    @client.event
    async def on_raw_reaction_add(payload):
        if payload.member.bot:
            return
        else:
            if payload.emoji.name == "🔄":
                botdbc.execute("SELECT * FROM game_log WHERE guild_id = " + str(payload.guild_id) + " AND message_id = " + str(payload.message_id) + " OR challanger_id = " + str(payload.member.id) + " OR opponent_id = " + str(payload.member.id) + " ORDER BY date")
                game_log = botdbc.fetchone()

                if game_log is None:
                    return
                elif game_log["date"] < datetime.datetime.now()-datetime.timedelta(seconds=10):
                    return
                else:
                    await new_request(game_log["guild_id"], payload.channel_id, game_log["challanger_id"], game_log["opponent_id"], True)
            elif payload.emoji.name == "✅":
                botdbc.execute("SELECT * FROM battlerequests WHERE guild_id = " + str(payload.guild_id) + " AND message_id = " + str(payload.message_id) + " AND opponent_id = " + str(payload.member.id) + " ORDER BY date")
                battle_request = botdbc.fetchone()

                if battle_request is None:
                    return
                elif battle_request["date"] < datetime.datetime.now()-datetime.timedelta(seconds=30):

                    sql_deleterequest = "DELETE FROM battlerequests WHERE guild_id = " + str(payload.guild.id) + " AND challanger_id = " + str(battle_request["challanger_id"]) + " AND opponent_id = " + str(payload.member.id)
                    botdbc.execute(sql_deleterequest)
                    botdb.commit()

                    response=discord.Embed(title="❌ You dont have an open request!", color=0xff0000)
                    response.set_author(name=payload.member.name,icon_url=payload.member.avatar_url)
                    response.set_footer(text="Request expire after 30 seconds!")
                    await payload.channel.send(embed = response)
                    return
                else:
                    await init_game(payload.guild_id, payload.member.id, payload.channel_id)



    client.run(token)
else:
    exit()