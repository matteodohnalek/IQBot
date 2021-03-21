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
    

    def emptyfield():
        emptyrows = '{"row1": ["0", "0", "0"], "row2": ["0", "0", "0"], "row3": ["0", "0", "0"]}'
        data  = json.loads(emptyrows)
        finished_message = ""
        count = 0
        for rows in data:
            for i in data[rows]:
                if i == "0":
                    if count == 2:
                        finished_message+="| ⚪ |\n"
                        count = 0
                    else:
                        finished_message+="| ⚪ "
                        count+=1
        return "" + finished_message
        
    def field(data, count):
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
            
        if len(message.content) > 254:
            return

        if message.content.startswith("!tictactoe"):
            arg1 = (message.content).replace("!tictactoe ","")
            skipcheckuser = False
            if "accept" in arg1 and not "@" in arg1:
                skipcheckuser = True
                botdbc.execute("SELECT challenger_id FROM battlerequests WHERE guild_id = " + str(message.guild.id) + " AND opponent_id = " + str(message.author.id))
                battlerequest = botdbc.fetchone()
                if battlerequest is None:
                    error = "You dont have a open battle request! Challange somebody with: !tictactoe @USERNAME"
                else:
                    error = False
                    if await message.guild.fetch_member(battlerequest["challenger_id"]) is not None:
                        user1 = await client.fetch_user(battlerequest["challenger_id"])
                        user2 = message.author

                        empty_field = emptyfield()

                        starterlist = ["o", "c"]
                        starter = random.choice(starterlist)

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

                        sql_deleterequest = "DELETE FROM battlerequests WHERE guild_id = " + str(message.guild.id) + " AND challenger_id = " + str(user1.id) + " AND opponent_id = " + str(user2.id)
                        botdbc.execute(sql_deleterequest)
                        botdb.commit()

                        empty_json_field = '{"row1": ["0", "0", "0"], "row2": ["0", "0", "0"], "row3": ["0", "0", "0"]}'

                        sql_battle = "INSERT INTO activebattle (guild_id, opponent_id, challenger_id, json_field, turn_id, opponent_name, challenger_name, turn_name, turn_color) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        val_battle = (message.guild.id, user2.id, user1.id, empty_json_field, turn_id, user2.name,  user1.name, turn_name, turn_color)
                        botdbc.execute(sql_battle, val_battle)
                        botdb.commit()

                        response=discord.Embed(title="Active Battle", color=0xb00000)
                        response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                        response.add_field(name="🔴" + user1.name + " vs 🔵" + user2.name, value=empty_field, inline=True)
                        response.add_field(name="Usage:", value="| A1 | A2 | A3 |\n| B1 | B2 | B3 |\n| C1 | C2 | C3 |\nTo place your block on a field, write the field number", inline=False)
                        response.add_field(name="Whose turn is it:", value=turn_name, inline=False)
                        response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                        await message.channel.send(embed = response)
                        response = ""
                    else:
                        error = "An error occured! 2"
            if not skipcheckuser:
                arg1 = re.sub("\D", "", arg1)
                if arg1 == "" and error:
                    error = "User not found"
                else:
                    if await message.guild.fetch_member(arg1) is not None:
                        user1 = await client.fetch_user(arg1)
                        user2 = message.author
                        botdbc.execute("SELECT challenger_id FROM battlerequests WHERE guild_id = " + str(message.guild.id) + " AND opponent_id = " + str(message.author.id))
                        check_battle = botdbc.fetchone()
                        if check_battle is None:
                            if user1.id == user2.id:
                                error = "You cant send yourself a battle request!"
                            else: 
                                response=discord.Embed(title="Challange", color=0x00ff00)
                                response.add_field(name= user2.name + " vs " + user1.name, value="Their battle will be legendary!", inline=False)
                                response.add_field(name="To accept this battle:", value="!tictactoe accept", inline=False)
                                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                                await message.channel.send(embed = response)
                                response = ""
                                error = False
                                sql_battlerequest = "INSERT INTO battlerequests (guild_id, opponent_id, challenger_id) VALUES (%s, %s, %s)"
                                val_battlerequest = (message.guild.id, user1.id, user2.id)
                                botdbc.execute(sql_battlerequest, val_battlerequest)
                                botdb.commit()
                        else:
                            error = "This user is currently in a battle!"
                    else:
                        error = "User not found"
            
            if error is not False:
                user2 = message.author
                response=discord.Embed(title="❌ " + error, color=0xff0000)
                response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                await message.channel.send(embed = response)
                response = ""        
            return
        elif message.content == "A1" or "A2" or "A3" or "B1" or "B2" or "B3" or "C1" or "C2" or "C3":
            botdbc.execute("SELECT * FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND turn_id = " + str(message.author.id))
            activebattle = botdbc.fetchone()
            if activebattle is None:
                return
            else:
                skip = False
                win = False
                error = False
                error_msg = ""
                data  = json.loads(activebattle["json_field"])

                if message.content.startswith("A"):
                    if message.content.endswith("1"):
                        if data["row1"][0] == "0":
                            if activebattle["turn_color"] == "blue":
                                data["row1"][0] = "2"
                            elif activebattle["turn_color"] == "red":
                                data["row1"][0] = "1"
                        else:
                            error = True
                            error_msg = "no"
                    elif message.content.endswith("2"):
                        if data["row1"][1] == "0":
                            if activebattle["turn_color"] == "blue":
                                data["row1"][1] = "2"
                            elif activebattle["turn_color"] == "red":
                                data["row1"][1] = "1"
                        else:
                            error = True
                            error_msg = "no"
                    elif message.content.endswith("3"):
                        if data["row1"][2] == "0":
                            if activebattle["turn_color"] == "blue":
                                data["row1"][2] = "2"
                            elif activebattle["turn_color"] == "red":
                                data["row1"][2] = "1"
                        else:
                            error = True
                            error_msg = "no"
                    else:
                        skip = True

                elif message.content.startswith("B"):
                    if message.content.endswith("1"):
                        if data["row2"][0] == "0":
                            if activebattle["turn_color"] == "blue":
                                data["row2"][0] = "2"
                            elif activebattle["turn_color"] == "red":
                                data["row2"][0] = "1"
                        else:
                            error = True
                            error_msg = "no"
                    elif message.content.endswith("2"):
                        if data["row2"][1] == "0":
                            if activebattle["turn_color"] == "blue":
                                data["row2"][1] = "2"
                            elif activebattle["turn_color"] == "red":
                                data["row2"][1] = "1"
                        else:
                            error = True
                            error_msg = "no"
                    elif message.content.endswith("3"):
                        if data["row2"][2] == "0":
                            if activebattle["turn_color"] == "blue":
                                data["row2"][2] = "2"
                            elif activebattle["turn_color"] == "red":
                                data["row2"][2] = "1"
                        else:
                            error = True
                            error_msg = "no"
                    else:
                        skip = True

                elif message.content.startswith("C"):
                    if message.content.endswith("1"):
                        if data["row3"][0] == "0":
                            if activebattle["turn_color"] == "blue":
                                data["row3"][0] = "2"
                            elif activebattle["turn_color"] == "red":
                                data["row3"][0] = "1"
                        else:
                            error = True
                            error_msg = "no"
                    elif message.content.endswith("2"):
                        if data["row3"][1] == "0":
                            if activebattle["turn_color"] == "blue":
                                data["row3"][1] = "2"
                            elif activebattle["turn_color"] == "red":
                                data["row3"][1] = "1"
                        else:
                            error = True
                            error_msg = "no"
                    elif message.content.endswith("3"):
                        if data["row3"][2] == "0":
                            if activebattle["turn_color"] == "blue":
                                data["row3"][2] = "2"
                            elif activebattle["turn_color"] == "red":
                                data["row3"][2] = "1"
                        else:
                            error = True
                            error_msg = "no"
                    else:
                        skip = True
                        ### Check if somebody has won!
                if data["row1"][0] == "1" and data["row1"][1] == "1" and data["row1"][2] == "1" or data["row2"][0] == "1" and data["row2"][1] == "1" and data["row2"][2] == "1" or data["row3"][0] == "1" and data["row3"][1] == "1" and data["row3"][2] == "1" or data["row1"][0] == "1" and data["row2"][1] == "1" and data["row3"][2] == "1" or data["row1"][2] == "1" and data["row2"][1] == "1" and data["row3"][0] == "1":
                    win = True
                    winner_name = activebattle["challenger_name"]
                elif data["row1"][0] == "2" and data["row1"][1] == "2" and data["row1"][2] == "2" or data["row2"][0] == "2" and data["row2"][1] == "2" and data["row2"][2] == "2" or data["row3"][0] == "2" and data["row3"][1] == "2" and data["row3"][2] == "2" or data["row1"][0] == "2" and data["row2"][1] == "2" and data["row3"][2] == "2" or data["row1"][2] == "2" and data["row2"][1] == "2" and data["row3"][0] == "2":
                    win = True
                    winner_name = activebattle["opponent_name"]
                tie = False
                tie_number = 0
                for i in data["row1"]:
                    print(i)
                    if not tie:
                        if i == "0":
                            tie_number += 1
                for ii in data["row2"]:
                    print(ii)
                    if not tie:
                        if ii == "0":
                            tie_number += 1
                for iii in data["row3"]:
                    print(iii)
                    if not tie:
                        if iii == "0":
                            tie_number += 1
                print(tie_number)
                if tie_number == 0:
                    tie = True
                else:
                    tie = False
                print(tie)

                ### END for check if somebody has won!

                if not skip and not win and not error and not tie:
                    field_send = field(data, 0)
                    if activebattle["turn_id"] == activebattle["opponent_id"]:
                        turn_name = activebattle["challenger_name"]
                        turn_id = activebattle["challenger_id"]
                    elif activebattle["turn_id"] == activebattle["challenger_id"]:
                        turn_name = activebattle["opponent_name"]
                        turn_id = activebattle["opponent_id"]
                    if activebattle["turn_color"] == "red":
                        turn_color = "blue"
                    elif activebattle["turn_color"] == "blue":
                        turn_color = "red"

                    sql_update_active_battle = "UPDATE activebattle SET json_field = %s, turn_color = %s, turn_id = %s WHERE challenger_id = %s AND guild_id = %s AND opponent_id = %s"
                    val_update_active_battle = (json.dumps(data), str(turn_color), str(turn_id), str(activebattle["challenger_id"]), str(message.guild.id), str(activebattle["opponent_id"]))
                    botdbc.execute(sql_update_active_battle, val_update_active_battle)
                    botdb.commit()

                    response=discord.Embed(title="Active Battle", color=0xb00000)
                    response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                    response.add_field(name="🔴" + activebattle["challenger_name"] + " vs 🔵" + activebattle["opponent_name"], value=field_send, inline=True)
                    response.add_field(name="Usage:", value="| A1 | A2 | A3 |\n| B1 | B2 | B3 |\n| C1 | C2 | C3 |\nTo place your block on a field, write the field number", inline=False)
                    response.add_field(name="Whose turn is it:", value=turn_name, inline=False)
                    response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                    await message.channel.send(embed = response)
                    response = ""
                elif not skip and win and not error and not tie:
                    field_send = field(data, 0)
                    if activebattle["turn_id"] == activebattle["opponent_id"]:
                        turn_name = activebattle["challenger_name"]
                    elif activebattle["turn_id"] == activebattle["challenger_id"]:
                        turn_name = activebattle["opponent_name"]

                    sql_delete_battle = "DELETE FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND challenger_id = " + str(activebattle["challenger_id"]) + " AND opponent_id = " + str(activebattle["opponent_id"])
                    botdbc.execute(sql_delete_battle)
                    botdb.commit()
                    response=discord.Embed(title=winner_name + " has won!", color=0xb00000)
                    response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                    response.add_field(name="🔴" + activebattle["challenger_name"] + " vs 🔵" + activebattle["opponent_name"], value=field_send, inline=True)
                    response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                    await message.channel.send(embed = response)
                    response = ""
                elif tie:
                    field_send = field(data, 0)
                    if activebattle["turn_id"] == activebattle["opponent_id"]:
                        turn_name = activebattle["challenger_name"]
                    elif activebattle["turn_id"] == activebattle["challenger_id"]:
                        turn_name = activebattle["opponent_name"]

                    sql_delete_battle = "DELETE FROM activebattle WHERE guild_id = " + str(message.guild.id) + " AND challenger_id = " + str(activebattle["challenger_id"]) + " AND opponent_id = " + str(activebattle["opponent_id"])
                    botdbc.execute(sql_delete_battle)
                    botdb.commit()
                    response=discord.Embed(title="Tie!", color=0xb00000)
                    response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                    response.add_field(name="🔴" + activebattle["challenger_name"] + " vs 🔵" + activebattle["opponent_name"], value=field_send, inline=True)
                    response.set_footer(text="Want your own battle? !tictactoe @USERNAME")
                    await message.channel.send(embed = response)
                    response = ""
                elif error:
                    response=discord.Embed(title="❌ " + error_msg, color=0xff0000)
                    response.set_author(name=message.author.name,icon_url=message.author.avatar_url)
                    await message.channel.send(embed = response)
                    response = ""
                else:
                    return
 
        elif message.content.startswith("!listroles"):
            await message.add_reaction("✅")
            guild = client.get_guild(message.guild.id)
            guild_roles = []
            for role in reversed(guild.roles):
                guild_roles.append(role.name + "    ID:  " + str(role.id) + "\n")
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
            print(payload)
            message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
            user = await client.get_user(payload.user_id)
            await message.add_reaction("✅")
            return

    client.run(token)
else:
    print("DB Not Working")