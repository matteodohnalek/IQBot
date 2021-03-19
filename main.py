# LIBARIES
import discord
from discord.ext import commands
from credentials import *

client = discord.Client()

# FUNKTIONEN
def mention(author_id):
    return "<@" + str(author_id) + ">"

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

    if message.content.startswith("!listroles"):
        await message.add_reaction("✅")
        guild = client.get_guild(message.guild.id)
        guild_roles = []
        for role in reversed(guild.roles):
            guild_roles.append(role.name + "    ID:  " + str(role.id) + "\n")
        response = discord.Embed(
            title = "All roles:",
            description = ''.join(guild_roles), 
            colour = discord.Colour.blue()
        )
        await message.channel.send("Here is a list of all roles on this server",embed = response)
        response = ""
        return
    ## NOT FINISHED -> Status: Split the arguments apart... now i need to assign the role to the user / strip ids from mention
    elif message.content.startswith("!giverole"):
        message_stripped = (message.content).strip("!giverole ")
        arg1, arg2 = message_stripped.split(' ', 1)
        print(arg1 + "     " + arg2)
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