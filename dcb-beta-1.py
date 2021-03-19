# LIBARIES
import discord
from discord.ext import commands
import random
import string
import mysql.connector as mysql
import time
from pprint import pprint
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# MYSQL INIT
botdb = mysql.connect(
    host="127.0.0.1",
    user="discordbot",
    password="",
    database="discordbot"
)
if botdb:
    print("DB Working")
else:
    print("DB Not Working")
botdbc = botdb.cursor(dictionary=True)


# FUNKTIONEN
def mention(author_id):
    return "<@" + str(author_id) + ">"


# DISCORD BOT START
class MyClient(discord.Client):
    async def on_ready(self):
        print(self.user)

        # STATUS SETZEN
        game = discord.Game("mit der API")
        await client.change_presence(status=discord.Status.online, activity=game)

        # ALLE SERVER AUSGEBEN
        print('Aktuell auf ' + str(len(client.guilds)) + ' Servern')
        for guild in client.guilds:
            print(guild.name)

    async def on_message(self, message: discord.Message) -> None:

        # NICHT DIR SELBST ANTWORTEN
        if message.author == self.user:
            return
        
        if len(message.content) > 254:
            return

        print(message)
        
        # SIMPLE RESPONSE AUSLESEN
        botdbc.execute("SELECT * FROM response_simple WHERE guild_id = " + str(message.guild.id))
        responses_simple = botdbc.fetchall()
        for x in responses_simple:
            if message.content == x["recive"] and str(message.guild.id) == x["guild_id"]:
                response = x["responde"]
                if "$mention$" in response.lower():
                    mention_text = mention(message.author.id)
                    response = response.replace("$mention$", mention_text)

                #sending message
                await message.channel.send(response)
                response = ""
                return

        # ENDE SIMPLE RESPONSE AUSLESEN

        # BÖSE WÖRTER AUSLESEN

        sql_bw = "SELECT * FROM bad_words WHERE guild_id = " + str(message.guild.id)
        botdbc.execute(sql_bw)
        bad_words = botdbc.fetchall()

        for bw in bad_words:

            lowercontent = message.content
            
            if lowercontent.lower() == bw["bad_message"]:
                
                sql_w = "SELECT * FROM warnings WHERE author_id  =" + str(message.author.id) + " AND guild_id = " + str(message.guild.id)
                botdbc.execute(sql_w)
                warnings = botdbc.fetchall()

                if botdbc.rowcount == 0:
                    # Nutzer hat zum ersten Mal eine Straftat begangen
                    response = mention(message.author.id) + " Verwarnung! (1/3)"
                    newcount = 1

                    await message.delete()

                    sql_warn = "INSERT INTO warnings (warning_count, guild_id, author_id) VALUES (%s, %s, %s)"
                    val_warn = (newcount, message.guild.id, message.author.id)
                    botdbc.execute(sql_warn, val_warn)
                    botdb.commit()

                    await message.channel.send(response, delete_after=4)
                    response = ""
                    return

                else:
                    for w in warnings:
                        if int(w["warning_count"]) >= 3:
                        #hier kommt später der im Web Interface angegebene Wert für Maßnamen rein 
                            response = mention(message.author.id) + " Konsequenzen! (" + str(w["warning_count"]) + "/3)"
                            await message.delete()
                            await message.channel.send(response, delete_after=4)
                            response = ""
                            newcount = w["warning_count"] + 1

                        else: 
                            response = mention(message.author.id) + " Verwarnung! (" + str(w["warning_count"]) + "/3)"
                            newcount = w["warning_count"] + 1
                            await message.delete()
                            await message.channel.send(response, delete_after=4)
                            response = ""

                        sql_warn = "UPDATE warnings SET warning_count = " + str(newcount) + " WHERE author_id  =" + str(message.author.id) + " AND guild_id = " + str(message.guild.id)
                        botdbc.execute(sql_warn)
                        botdb.commit()
                        return
        # ENDE BÖSE WÖRTER AUSLESEN
        if message.content == "!guildroles":
            guild = client.get_guild(message.guild.id)
            guild_roles = []
            for role in guild.roles:
                guild_roles.append(role.name)
            pprint(guild_roles)
            return

client = MyClient()
client.run('TOKEN')