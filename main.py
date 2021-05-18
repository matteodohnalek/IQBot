# LIBARIES
import discord
from discord.ext import commands
from credentials import *
import re
import json
import random

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

        for rows in data:
        
            for i in data[rows]:

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
            skipcheckuser = False
            error = False

            # Schauen ob ein Nutzer markiert wurde (@) und ob "accept" geschickt wurde
            if "accept" in arg1 and not "@" in arg1:
                
                # Checkt nicht ob der Nutzer existiert
                skipcheckuser = True

                # Schaue in der Datenbank nach, ob eine Anfrage an den Nutzer geschickt wurde
                botdbc.execute("SELECT challenger_id FROM battlerequests WHERE guild_id = " + str(message.guild.id) + " AND opponent_id = " + str(message.author.id))
                battlerequest = botdbc.fetchone()

                if battlerequest is None:

                    # Keine Anfrage wurde gefunden, also error!
                    error = "You dont have a open battle request! Challange somebody with: !tictactoe @USERNAME"

                else:
                    # Eine Anfrage wurde gefunden, jetzt wird ein Spiel initiiert!

                    error = False

                    # Schauen ob Nutzer auch teil des Servers ist (für Multiple Server funktionalität)
                    if await message.guild.fetch_member(battlerequest["challenger_id"]) is not None:

                        # Nutzer werden festgelegt (Diesen Prozess reduzieren)
                        user1 = await client.fetch_user(battlerequest["challenger_id"])
                        user2 = message.author

                        # Fügt hinzu, wer Challanger (c) und wer Oponent (o)
                        starterlist = ["o", "c"]
                        starter = random.choice(starterlist)

                        # Festlegen wer wer ist u. in Datenbank schreiben (Prozess reduzieren)
                        if starter == "o":
                            turn_id = user2.id
                            turn_name = user2.name
                            not_turn_name = user1.name
                            turn_color = "blue"
                        elif starter == "c":
                            turn_id = user1.id
                            turn_name = user1.name
                            not_turn_name = user2.name
                            turn_color = "red"

                        # Anfrage des Battles wird aus der Datenbank gelöscht
                        sql_deleterequest = "DELETE FROM battlerequests WHERE guild_id = " + str(message.guild.id) + " AND challenger_id = " + str(user1.id) + " AND opponent_id = " + str(user2.id)
                        botdbc.execute(sql_deleterequest)
                        botdb.commit()

                        # leeres Feld wird als json festgelegt
                        empty_json_field = '{"A": {"1": "0", "2": "0", "3": "0"}, "B": {"1": "0", "2": "0", "3": "0"}, "C": {"1": "0", "2": "0", "3": "0"}}'
                        empty_field = field(json.loads(empty_json_field))

                        # Alle Informationen werden in as Aktive Battle Datenbank geschrieben
                        sql_battle = "INSERT INTO activebattle (guild_id, opponent_id, challenger_id, json_field, turn_id, opponent_name, challenger_name, turn_name, turn_color) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        val_battle = (message.guild.id, user2.id, user1.id, empty_json_field, turn_id, user2.name,  user1.name, turn_name, turn_color)
                        botdbc.execute(sql_battle, val_battle)
                        botdb.commit()

                        # Die Antwort auf die Nachricht mit dem aktiven Spielfeld als Inhalt wird als Embed hier vorbereitet und geschickt
                        response=discord.Embed(title="Active Battle", color=0xb00000)
                        response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                        response.add_field(name="🔴" + user1.name + " vs 🔵" + user2.name, value=empty_field, inline=True)
                        response.add_field(name="Usage:", value="| A1 | A2 | A3 |\n| B1 | B2 | B3 |\n| C1 | C2 | C3 |\nTo place your block on a field, write the field number", inline=False)
                        response.add_field(name="Whose turn is it:", value=turn_name, inline=False)
                        response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                        await message.channel.send(embed = response)
                        response = ""
                    
                    # Schlägt an wenn der Nutzer auf dem falschen Server eine Anfrage annehmen will
                    else:
                        return

            # Eine Anfrage wird geschickt
            if not skipcheckuser:

                # Das angegebene Argument (arg1) bei Commandausführung löscht alles bis auf Zahlen (/D) aus dem String,
                # um so nur die NutzerID des markierten zu bekommen
                arg1 = re.sub("\D", "", arg1)
                
                # Checkt ob eine Nutzer ID vorhanden ist (falls nicht wird ein error zurück gegeben)
                if arg1 == "" and error:
                    error = "User not found"
                
                else:
                    # Hier wird geprüft ob der Nutzer tatsälich auf dem DiscordServer ist u. existiert.
                    try:
                        if await message.guild.fetch_member(arg1) is not None:

                            # Hier wird festgelegt welcher Nuitzer welcher ist (SINN????)
                            user1 = await client.fetch_user(arg1)
                            user2 = message.author

                            # Hier wird in der Datenbank nachgeschaut, ob der Nutzer schon eine aktive Anfrage hat
                            botdbc.execute("SELECT challenger_id FROM battlerequests WHERE guild_id = " + str(message.guild.id) + " AND opponent_id = " + str(message.author.id))
                            check_battle = botdbc.fetchone()

                            # Wenn der Nutzer keine Anfrage hat, dann
                            if check_battle is None:

                                # Check ob Nutzer versucht sich selbst eine Anfrage zu schauen
                                if user1.id == user2.id:
                                    error = "You cant send yourself a battle request!"

                                # Der Nutzer ist ok und darf ein Battle erstellen!
                                else: 

                                    # Nachricht wird als Embed erstellt und geschickt
                                    response=discord.Embed(title="Challange", color=0x00ff00)
                                    response.add_field(name= user2.name + " vs " + user1.name, value="Their battle will be legendary!", inline=False)
                                    response.add_field(name="To accept this battle:", value="!tictactoe accept", inline=False)
                                    response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                                    await message.channel.send(embed = response)
                                    response = ""

                                    # Die Anfrage wird in die Datenbank aufgenommen
                                    error = False
                                    sql_battlerequest = "INSERT INTO battlerequests (guild_id, opponent_id, challenger_id) VALUES (%s, %s, %s)"
                                    val_battlerequest = (message.guild.id, user1.id, user2.id)
                                    botdbc.execute(sql_battlerequest, val_battlerequest)
                                    botdb.commit()

                            # Falls der Nutzer bereits eine Anfrage hat        
                            else:
                                error = "This user is currently in a battle!"
                        
                        # Falls der Nutzer nicht gefunden wurde
                    except:
                        error = "Not a User!"
            
            # Hier werden Nachrichten verschickt die mit der Variable "error vorher festgelegt wurden"

            # Checkt das Variable "error" nicht "false" ist
            if error is not False:

                # Schickt error Nachricht als Embed
                response=discord.Embed(title="❌ " + error, color=0xff0000)
                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                await message.channel.send(embed = response)
                response = ""
            return
        
        # Spielsteuerung
        uppermsg = message.content
        if uppermsg == "A1" or "A2" or "A3" or "B1" or "B2" or "B3" or "C1" or "C2" or "C3":
            
            # In der Datenbank wird geschaut ob der NachrichtenAutor auch ein aktives Battle auf der Guild hat
            botdbc.execute("SELECT * FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND turn_id = " + str(message.author.id))
            activebattle = botdbc.fetchone()

            if activebattle is None:
                # Falls kein Aktives Battle vorhanden ist wird die Nachricht einfach ignoriert
                return

            else:
                
                # Variablen werden festgelegt (SINN????)
                skip = False
                win = False
                error = False
                error_msg = ""
                data  = json.loads(activebattle["json_field"])

                # Spiel wird ausgewertet :/ BITTE VERKÜRZEN

            if len(message.content) != 2:
                error_msg = "Nachricht zu lang"
                error = True
            else:
                if data[uppermsg[0]][uppermsg[1]] == "0":
                    if activebattle["turn_color"] == "blue":
                        data[uppermsg[0]][uppermsg[1]] = "2"
                    else:
                        data[uppermsg[0]][uppermsg[1]] = "1"
                else:
                    error_msg = "Nein"
                    error = True
                        
                        ### Check ob jemand gewonnen hat (evtl schöner??)
                if data["A"]["1"] == "1" and data["A"]["2"] == "1" and data["B"]["3"] == "1" or data["B"]["1"] == "1" and data["B"]["2"] == "1" and data["B"]["3"] == "1" or data["C"]["1"] == "1" and data["C"]["2"] == "1" and data["C"]["3"] == "1" or data["A"]["1"] == "1" and data["B"]["2"] == "1" and data["C"]["3"] == "1" or data["A"]["3"] == "1" and data["B"]["2"] == "1" and data["C"]["1"] == "1":
                    win = True
                    winner_name = activebattle["challenger_name"]

                elif data["A"]["1"] == "2" and data["A"]["2"] == "2" and data["A"]["3"] == "2" or data["B"]["1"] == "2" and data["B"]["2"] == "2" and data["B"]["3"] == "2" or data["C"]["1"] == "2" and data["C"]["2"] == "2" and data["C"]["2"] == "3" or data["A"]["1"] == "2" and data["B"]["2"] == "2" and data["C"]["3"] == "2" or data["A"]["3"] == "2" and data["B"]["2"] == "2" and data["A"]["1"] == "2":
                    win = True
                    winner_name = activebattle["opponent_name"]
                
                tie = False
                tie_number = 0
                for i in data["A"]:
                    
                    if not tie:

                        if i == "0":
                            tie_number += 1

                for ii in data["B"]:

                    if not tie:

                        if ii == "0":
                            tie_number += 1

                for iii in data["C"]:
                    
                    if not tie:

                        if iii == "0":
                            tie_number += 1

                if tie_number == 0:
                    tie = True

                else:
                    tie = False
                tie = False ### TIE TIE TIE TIE

                ### ENDE check ob jemand gewonnen hat

                if not skip and not win and not error and not tie:
                    # Tauschen der Rollen jenachdem wer dran ist (pls change)
                    field_send = field(data)

                    if activebattle["turn_id"] == activebattle["opponent_id"]:
                        turn_name = activebattle["challenger_name"]
                        turn_id = activebattle["challenger_id"]

                    elif activebattle["turn_id"] == activebattle["challenger_id"]:
                        turn_name = activebattle["opponent_name"]
                        turn_id = activebattle["opponent_id"]

                    # Setzt welche Farbe aktuell dran ist
                    if activebattle["turn_color"] == "red":
                        turn_color = "blue"

                    elif activebattle["turn_color"] == "blue":
                        turn_color = "red"

                
                    # Aktualisiertes Feld wird in die Datenbank geschrieben
                    sql_update_active_battle = "UPDATE activebattle SET json_field = %s, turn_color = %s, turn_id = %s WHERE challenger_id = %s AND guild_id = %s AND opponent_id = %s"
                    val_update_active_battle = (json.dumps(data), str(turn_color), str(turn_id), str(activebattle["challenger_id"]), str(message.guild.id), str(activebattle["opponent_id"]))
                    botdbc.execute(sql_update_active_battle, val_update_active_battle)
                    botdb.commit()

                    # Aktualisiertes Feld wird ausgegeben
                    response=discord.Embed(title="Active Battle", color=0xb00000)
                    response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                    response.add_field(name="🔴" + activebattle["challenger_name"] + " vs 🔵" + activebattle["opponent_name"], value=field_send, inline=True)
                    response.add_field(name="Usage:", value="| A1 | A2 | A3 |\n| B1 | B2 | B3 |\n| C1 | C2 | C3 |\nTo place your block on a field, write the field number", inline=False)
                    response.add_field(name="Whose turn is it:", value=turn_name, inline=False)
                    response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                    await message.channel.send(embed = response)
                    response = ""

                
                # Battle Win
                elif not skip and win and not error and not tie:

                    # Tausche Rollen, je nach dem Wer gerade dran ist
                    field_send = field(data)
                    if activebattle["turn_id"] == activebattle["opponent_id"]:
                        turn_name = activebattle["challenger_name"]
                    elif activebattle["turn_id"] == activebattle["challenger_id"]:
                        turn_name = activebattle["opponent_name"]

                    # Lösche Aktives Battle aus der Datenbank
                    sql_delete_battle = "DELETE FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND challenger_id = " + str(activebattle["challenger_id"]) + " AND opponent_id = " + str(activebattle["opponent_id"])
                    botdbc.execute(sql_delete_battle)
                    botdb.commit()

                    # Winner Nachricht wird als Embed erstellt und gesendet
                    response=discord.Embed(title=winner_name + " has won!", color=0xb00000)
                    response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                    response.add_field(name="🔴" + activebattle["challenger_name"] + " vs 🔵" + activebattle["opponent_name"], value=field_send, inline=True)
                    response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                    await message.channel.send(embed = response)
                    response = ""

                # Falls Unentschieden    
                elif tie:
                    # Tausche Rollen je nach dem wer dran ist
                    field_send = field(data)
                    if activebattle["turn_id"] == activebattle["opponent_id"]:
                        turn_name = activebattle["challenger_name"]
                    elif activebattle["turn_id"] == activebattle["challenger_id"]:
                        turn_name = activebattle["opponent_name"]

                    # Lösche Aktives Battle aus der Datenbank
                    sql_delete_battle = "DELETE FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND challenger_id = " + str(activebattle["challenger_id"]) + " AND opponent_id = " + str(activebattle["opponent_id"])
                    botdbc.execute(sql_delete_battle)
                    botdb.commit()

                    # Erstelle Untenschieden Nachricht und schicke sie ab
                    response=discord.Embed(title="Tie!", color=0xb00000)
                    response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                    response.add_field(name="🔴" + activebattle["challenger_name"] + " vs 🔵" + activebattle["opponent_name"], value=field_send, inline=True)
                    response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                    await message.channel.send(embed = response)
                    response = ""

                # Erstelle und sende Error Nachricht, falls einer aufgetreten sein sollte    
                elif error:
                    response=discord.Embed(title="❌ " + error_msg, color=0xff0000)
                    response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                    await message.channel.send(embed = response)
                    response = ""
                return

        # Andere Antworten auf Nachrichten
        
        # LISTROLES COMMAND (aktuell nicht funktional)
        elif message.content == "!listroles":
            # Füge Haken zu nachricht des sender (als bestätigung)
            await message.add_reaction("✅")

            # Hole alle Rollen auf diesem Server ein
            guild = client.get_guild(message.guild.id)
            guild_roles = []

            # Gebe die Rollen umgekehrt aus (umgekehrt weil sie sonst nicht in der Richtung wo es in der Teilnehmerleiste ist ausgegeben werden)
            for role in reversed(guild.roles):
                # Rollen werden einzeln zu der variable hinzugefügt
                guild_roles.append(role.name + "    ID:  " + str(role.id) + "\n")

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
    @client.event
    async def on_raw_reaction_add(payload):
        if payload.message_id != react_to_get_role_msg:
            return
        else:
            message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
            user = await client.get_user(payload.user_id)
            await message.add_reaction("✅")
            return

    client.run(token)
else:
    print("DB Not Working")
