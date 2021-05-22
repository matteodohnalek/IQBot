# LIBARIES
import discord
from discord.ext import commands
from credentials import *
import re
import json
import random
import mysql
import mysql.connector as mysql

botdb = mysql.connect(
    host="192.168.55.10",
    user="iqbot",
    password=database_password,
    database="iqbot"
)

if botdb:
    print("DB Working")
    botdbc = botdb.cursor(dictionary=True)

    # Discord Client Init
    client = discord.Client()

    # FUNKTIONEN
    def mention(author_id):
        return "<@" + str(author_id) + ">"
    
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

    @client.event
    async def on_message(message):

        # NICHT DIR SELBST ANTWORTEN
        if message.author == client.user:
            return
            
        # Wenn Nachricht länger als Datenbank Limit ist, wird sie ignoriert!
        if len(message.content) > 254:
            return

        # TICTACTOE Init
        if message.content.startswith("!tictactoe"):

            # Der Command "tictactoe" wird von der Nachricht entfernt, damit am Ende nur die Parameter übrig bleiben
            arg1 = (message.content).replace("!tictactoe ","")
            
            # Variablen festlegen
            error_msg = False

            # Schauen ob ein Nutzer markiert wurde (@) und ob "accept" geschickt wurde
            if "accept" in arg1 and not "@" in arg1:

                # Schaue in der Datenbank nach, ob eine Anfrage an den Nutzer geschickt wurde
                botdbc.execute("SELECT challanger_id FROM battlerequests WHERE guild_id = " + str(message.guild.id) + " AND opponent_id = " + str(message.author.id))
                battlerequest = botdbc.fetchone()

                if battlerequest is None:

                    # Keine Anfrage wurde gefunden, also error!
                    error_msg = "You dont have a open battle request! Challange somebody with: !tictactoe @USERNAME"

                else:
                    # Eine Anfrage wurde gefunden, jetzt wird ein Spiel initiiert!
                    # Schauen ob Nutzer auch teil des Servers ist (für Multiple Server funktionalität)
                    if await message.guild.fetch_member(battlerequest["challanger_id"]) is not None:

                        # Nutzer werden festgelegt (Diesen Prozess reduzieren)
                        challanger = await client.fetch_user(battlerequest["challanger_id"])
                        opponent = message.author

                        # Fügt hinzu, wer Challanger (c) und wer Oponent (o)
                        starterlist = ["o", "c"]
                        starter = random.choice(starterlist)

                        # Festlegen wer wer ist u. in Datenbank schreiben (Prozess reduzieren)
                        if starter == "o":
                            turn_id = opponent.id
                        elif starter == "c":
                            turn_id = challanger.id

                        # Anfrage des Battles wird aus der Datenbank gelöscht
                        sql_deleterequest = "DELETE FROM battlerequests WHERE guild_id = " + str(message.guild.id) + " AND challanger_id = " + str(challanger.id) + " AND opponent_id = " + str(opponent.id)
                        botdbc.execute(sql_deleterequest)
                        botdb.commit()

                        # leeres Feld wird als json festgelegt
                        empty_json_field = '{"A": {"1": "0", "2": "0", "3": "0"}, "B": {"1": "0", "2": "0", "3": "0"}, "C": {"1": "0", "2": "0", "3": "0"}}'
                        empty_field = field(json.loads(empty_json_field))

                        # Alle Informationen werden in as Aktive Battle Datenbank geschrieben
                        sql_battle = "INSERT INTO activebattle (guild_id, opponent_id, challanger_id, json_field, turn_id) VALUES (%s, %s, %s, %s, %s)"
                        val_battle = (message.guild.id, challanger.id, opponent.id, empty_json_field, turn_id)
                        botdbc.execute(sql_battle, val_battle)
                        botdb.commit()

                        # Die Antwort auf die Nachricht mit dem aktiven Spielfeld als Inhalt wird als Embed hier vorbereitet und geschickt
                        response=discord.Embed(title="Active Battle", color=0xb00000)
                        response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                        response.add_field(name="🔴" + challanger.name + " vs 🔵" + opponent.name, value=empty_field, inline=True)
                        response.add_field(name="Usage:", value="| A1 | A2 | A3 |\n| B1 | B2 | B3 |\n| C1 | C2 | C3 |\nTo place your block on a field, write the field number", inline=False)
                        response.add_field(name="Whose turn is it:", value=(await client.fetch_user(turn_id)).name, inline=False)
                        response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                        await message.channel.send(embed = response)
                        response = ""
                    
                    # Schlägt an wenn der Nutzer auf dem falschen Server eine Anfrage annehmen will
                    else:
                        return

            # Eine Anfrage wird geschickt
            else:

                # Das angegebene Argument (arg1) bei Commandausführung löscht alles bis auf Zahlen (/D) aus dem String,
                # um so nur die NutzerID des markierten zu bekommen
                arg1 = re.sub("\D", "", arg1)
                
                # Checkt ob eine Nutzer ID vorhanden ist (falls nicht wird ein error zurück gegeben)
                if arg1 == "":
                    error_msg = "User not found"
                    return
                
                else:
                    # Hier wird geprüft ob der Nutzer tatsälich auf dem DiscordServer ist u. existiert.
                    print(arg1)
                    try:
                        if await message.guild.fetch_member(arg1) is not None:

                            # Hier wird festgelegt welcher Nuitzer welcher ist (SINN????)
                            opponent = await client.fetch_user(arg1)
                            challanger = message.author

                            if opponent.id == challanger.id:
                                error_msg = "Cant send yourself a battle request!"
                                return
                            # Hier wird in der Datenbank nachgeschaut, ob der Nutzer schon eine aktive Anfrage hat
                            botdbc.execute("SELECT challanger_id FROM battlerequests WHERE guild_id = " + str(message.guild.id) + " AND opponent_id = " + str(message.author.id))
                            check_battle = botdbc.fetchone()

                            # Wenn der Nutzer keine Anfrage hat, dann
                            if check_battle is None:

                            # Check ob Nutzer versucht sich selbst eine Anfrage zu schauen

                                # Die Anfrage wird in die Datenbank aufgenommen
                                error = False
                                sql_battlerequest = "INSERT INTO battlerequests (guild_id, opponent_id, challanger_id) VALUES (%s, %s, %s)"
                                val_battlerequest = (message.guild.id, opponent.id, challanger.id)
                                botdbc.execute(sql_battlerequest, val_battlerequest)
                                botdb.commit()

                                # Nachricht wird als Embed erstellt und geschickt
                                response=discord.Embed(title="Challange", color=0x00ff00)
                                response.add_field(name= challanger.name + " vs " + opponent.name, value="Their battle will be legendary!", inline=False)
                                response.add_field(name="To accept this battle:", value="!tictactoe accept", inline=False)
                                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                                await message.channel.send(embed = response)
                                response = ""

                            # Falls der Nutzer bereits eine Anfrage hat        
                            else:
                                error_msg = "This user is currently in a battle!"
                        
                    # Falls der Nutzer nicht gefunden wurde
                    except:
                        error_msg = "Error"
            
            # Hier werden Nachrichten verschickt die mit der Variable "error vorher festgelegt wurden"

            # Checkt das Variable "error" nicht "false" ist
            if error_msg:

                # Schickt error Nachricht als Embed
                response=discord.Embed(title="❌ " + error_msg, color=0xff0000)
                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                await message.channel.send(embed = response)
                response = ""
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
                    print("An error occured while trying to update the field!")
                    return
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
                    turn_id = str(challanger.id)
                elif activebattle["turn_id"] == str(challanger.id):
                    turn_id = str(opponent.id)

            
                # Aktualisiertes Feld wird in die Datenbank geschrieben
                sql_update_active_battle = "UPDATE activebattle SET json_field = %s, turn_id = %s WHERE challanger_id = %s AND guild_id = %s AND opponent_id = %s"
                val_update_active_battle = (json.dumps(data), str(turn_id), str(activebattle["challanger_id"]), str(message.guild.id), str(activebattle["opponent_id"]))
                botdbc.execute(sql_update_active_battle, val_update_active_battle)
                botdb.commit()

                # Aktualisiertes Feld wird ausgegeben
                response=discord.Embed(title="Active Battle", color=0xb00000)
                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                response.add_field(name="🔴" + challanger.name + " vs 🔵" + opponent.name, value=field_send, inline=True)
                response.add_field(name="Usage:", value="| A1 | A2 | A3 |\n| B1 | B2 | B3 |\n| C1 | C2 | C3 |\nTo place your block on a field, write the field number", inline=False)
                response.add_field(name="Whose turn is it:", value=(await client.fetch_user(activebattle["opponent_id"])).name, inline=False)
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

                # Winner Nachricht wird als Embed erstellt und gesendet
                response=discord.Embed(title=winner.name + " has won!", color=0xb00000)
                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                response.add_field(name="🔴" + challanger.name + " vs 🔵" + opponent.name, value=field_send, inline=True)
                response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                await message.channel.send(embed = response)
                response = ""

            # Falls Unentschieden    
            elif tie:
                # Tausche Rollen je nach dem wer dran ist
                field_send = field(data)

                # Lösche Aktives Battle aus der Datenbank
                sql_delete_battle = "DELETE FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND challanger_id = " + str(activebattle["challanger_id"]) + " AND opponent_id = " + str(activebattle["opponent_id"])
                botdbc.execute(sql_delete_battle)
                botdb.commit()

                # Erstelle Untenschieden Nachricht und schicke sie ab
                response=discord.Embed(title="Tie!", color=0xb00000)
                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                response.add_field(name="🔴" + challanger.name + " vs 🔵" + opponent.name, value=field_send, inline=True)
                response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                await message.channel.send(embed = response)
                response = ""

            # Erstelle und sende Error Nachricht, falls einer aufgetreten sein sollte    
            elif error_msg:
                response=discord.Embed(title="❌ " + error_msg, color=0xff0000)
                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                await message.channel.send(embed = response)
                response = ""
            return

        # Andere Antworten auf Nachrichten
        
        # LISTROLES COMMAND (aktuell nicht funktional)
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

            return

    ## DEFINETLY NOT FINISHED -> If you react to the configured message with ANY emoji, the bot reacts with a check_mark
    # @client.event
    # async def on_raw_reaction_add(payload):
    #    if payload.message_id != react_to_get_role_msg:
    #        return
    #    else:
    #        message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    #        user = await client.get_user(payload.user_id)
    #        await message.add_reaction("✅")
    #        return

    client.run(token)
else:
    print("DB Not Working")
