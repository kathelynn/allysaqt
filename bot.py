import asyncio
from os import sendfile
import discord
from discord import channel
from discord.ext import commands
import string

'''File loader/saver'''

from json import load, dump
def loaddisk(file):
    try:
        with open(file) as f:
            print(f'{file} accessed!')
            return load(f)
    except FileNotFoundError:
        print(f"""Please follow the instructions found in README.md,
        otherwise if error still occurs please report issues on GitHub.
        Missing file: {file}""")

def save(memory, file):
    with open(file, 'w') as f:
        print('Saving to disk..')
        dump(memory, f, indent=4)
        print('Saved successfully!')
async def autosave(memory, file, interval=None):
    interval = interval*60
    while True:
        await asyncio.sleep(interval)
        save(memory, file)
        
CONFIG = loaddisk('config.json')

'''Dict modifiers'''

def merge_dict(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            merge_dict(value, node)
        else:
            destination[key] = value

def nested_dict(source, destination):
    if len(source) > 1:
        node = destination.setdefault(source[0], {})
        return nested_dict(source[1:], node)
    else:
        destination[source[0]] = {}
        return destination[source[0]]

'''Bot database'''

class MEMORY:
    database = loaddisk(CONFIG['filename'])
    def __new__(cls):
        return MEMORY.database
    def merge(path, value):
            append = {}
            path = path.split('/')
            node = nested_dict(path[:-1], append)
            node[path[-1]] = value
            merge_dict(append, MEMORY.database)

def setting(ctx, item):
    try:
        return MEMORY()[str(ctx.guild.id)]['settings'][item] # type: ignore
    except KeyError:
        return MEMORY()['global']['settings'][item] # type: ignore

def command_prefix(bot, ctx):
    return setting(ctx, 'command_prefix')

'''Bot Logic'''

BOT = commands.Bot(command_prefix=command_prefix)

@BOT.event
async def on_ready():
    print(f'Logged on as {BOT.user} ({BOT.user.id})')
    if CONFIG['autosave']:
        await autosave(MEMORY(), CONFIG['filename'], CONFIG['autosaveinterval']) 

@BOT.event
async def on_message(message):
    print(f'{message.author} from {message.channel}: {message.content}')
    await BOT.process_commands(message)

class CMD:
    def __new__(cls, ctx=None, command=None):
        guild_id = str(ctx.guild.id)
        if command:
            command = ctx.message.content[len(ctx.prefix):].split()
            if command > 1:
                args = command[1:]
            command[0] = command[0].lower()

        if ctx and command:
            for key, value in MEMORY()[guild_id]['commands'].items():
                if command[0] in key:
                    return value
            raise KeyError(f'Command `{command}`')
        elif command:
            for key,value in MEMORY()['global']['commands'].items():
                if command[0] in key:
                    return value
            raise KeyError(f'Command `{command}`')
        elif ctx:
            return MEMORY()[guild_id]['commands']
        else:
            pass
        
    def if_global(command):
        for key, value in MEMORY()['global']['commands'].items():
            if command in key:
                return True
        return False
    def if_local(ctx, command):
        for key,value in MEMORY()[str(ctx.guild.id)]['commands'].items():
            if command in key:
                return True
        return False
    def if_unused(ctx, command):
        if CMD.if_global(command) or CMD.if_local(ctx, command):
            return False
        else:
            return True

@BOT.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        try:
            output = CMD(ctx, ctx.context)
            send = {}
            items = ctx.message
            for key, value in output.items():
                # need to copy instead of pointing to output var'
                if key in ['content','tts','embed','file']:
                    send[key] = string.Template(value).safe_substitute(**items)
            if 'embed' in send:
                send['embed'] = discord.Embed.from_dict(send['embed'])
            await ctx.send(**send)
        except KeyError:
            if setting(ctx, 'command_error'):
                    embed = discord.Embed.from_dict({"description":"Command not found", "color":16711680})
                    await ctx.send(embed=embed)
        except:
            await on_command_error(ctx, Exception)
    else:
        if setting(ctx, 'command_error'):
                embed = discord.Embed.from_dict({'description':'An error occured', 'color':16711680}) ###
                await ctx.send(embed=embed)
        raise error

# Playing around a bit here
#@BOT.event
#async def on_raw_message_delete(payload):
#    channel = await BOT.fetch_channel(payload.channel_id)
#    if payload.cached_message:
#        await channel.send(content=payload.cached_message.content)
#        if payload.cached_message.embeds:
#            for embed in payload.cached_message.embeds:
#                await channel.send(embed=embed)
#    else:
#        await channel.send('A message was deleted')
        
EMBED_TIMEOUT = CONFIG['embedtimeout']

class userinput:
    class emote:
        pass
    class text:
        pass
    def __init__(self, input_type, info):
        self.type = input_type
        self.info = info

async def interactive_embed(cls, ctx, botmsg, path, userinput):
    buttons = []
    # replace isinstance with classes 
    if userinput.type is userinput.emote:
        try:
            userinput.remove('..')
            buttons += ['◀']
        except: pass
        buttons += [button[0] for button in userinput] + ['❎']
    elif userinput.type is userinput.text:
        buttons = ['✏', '◀', '❎']
    else:
        raise Exception() ###
    
    for reaction in buttons:
        await botmsg.add_reaction(reaction)
    def check(reaction, user):
        return str(reaction.emoji) in buttons and user is ctx.author and reaction.message is botmsg
    reaction, user = await BOT.wait_for('reaction_add', check=check, timeout=EMBED_TIMEOUT)
    emoji = str(reaction.emoji)

    if emoji == '✏':
        await botmsg.clear_reactions()
        embed = {'description': userinput.description}
        await botmsg.edit(embed=discord.Embed(description=userinput.description))
        def check(message):
            return message.author is ctx.author and message.channel is botmsg.channel
        message = await BOT.wait_for('message', check=check, timeout=EMBED_TIMEOUT)
        await message.delete(delay=0)
        return message.content, botmsg
    elif emoji == '◀':
        return '..'
    elif emoji == '❎':
        await botmsg.clear_reactions()
        return 0, botmsg
    else:
        path = buttons.index(emoji)
        return userinput[path], botmsg

@BOT.command(aliases=['set'])
async def settings(ctx, *args, botmsg=None):
    try:
        embed = {}
        userinput = []

        guild_id = str(ctx.guild.id)
        guild_icon = str(ctx.guild.icon_url)
        
        def str_bool(string):
            _type = type(string)
            if string is bool:
                return string
            elif string is str:
                string = string.lower()
                if string in ['true', 't', 'yes', 'y', 'on']:
                    return True
                elif string in ['false', 'f', 'no', 'n', 'off']:
                    return False
                else:
                    raise TypeError('str_bool() argument must be a boolean string, not ' + string)
            else:
                raise TypeError('str_bool() cannot')

        if not args:
            userinput = [('1️⃣', 'prefix'), ('2️⃣', 'cmdalerts')]
            prefix = ctx.prefix
            embed += {
                "author": {
                    "name": ctx.guild.name,
                    "icon_url": guild_icon
                },
                "title": "Settings",
                "description": f"{prefix}set ",
                "fields": [
                    {
                        "name": f"1️⃣ Prefix",
                        "value": f"{prefix}set "
                    },
                    {
                        "name": "2️⃣ Cmdalerts",
                        "value":  f"Command alerts set to {not setting(ctx, 'command_error')}"
                    }
                ]
            }
        elif len(args) < 3:
            if args[0] == 'prefix':
                if len(args) < 2:
                    if ctx.author.guild_permissions.manage_guild:
                        userinput = 'Change the command'
                    embed = {
                        "author": {
                            "name": f"{ctx.guild.name} / Settings ",
                            "icon_url": guild_icon
                        },
                        "title": "Prefix"
                        "description": f"*{ctx.prefix}*"
                    }
                else:
                    if not ctx.author.guild_permissions.manage_guild:
                        raise Exception('`manage_guild` permission missing') ###
                    elif ctx.prefix == args[1]:
                        raise Exception('Pick a different prefix') ###
                    elif len(args[1]) > 3:
                        raise Exception('Arg is too long') ###
                    else:
                        for character in args[1]:
                            if character not in string.hexdigits + string.punctuation:
                                raise Exception(f'Invalid character {character}') ###
                        MEMORY.merge(f'{guild_id}/settings/command_prefix', args[1])
                        embed = {
                            "description": f"Prefix for this server has been changed to `{MEMORY()[guild_id]['settings']['prefix']}`.",
                            "color": 65280
                        }
            elif args[0] == 'cmdalerts':
                command_error = setting(ctx, 'command_error')
                if len(args) < 2:
                    if ctx.author.guild_permissions.manage_guild:
                        userinput = [not setting(ctx, 'command_error')]
                        embed = {
                            "author": {
                                "name": f"{ctx.guild.name} / Command Alerts",
                                "icon_url": str(guild_icon)
                            },
                            "description": f"{setting(ctx, 'command_error')}"
                        }
                else:
                    try:
                        MEMORY.merge(f'{guild_id}/settings/command_error', str_bool(args[1]))
                    except TypeError:
                        raise TypeError(f'{args[1]} not an accepted value') ###
                        
        else:
            raise Exception('Arguments are incorrect')
        
        embed = discord.Embed.from_dict(embed)
        if botmsg:
            await botmsg.clear_reactions()
            await botmsg.edit(embed=embed)
        else:
            botmsg = await ctx.send(embed=embed)
        
        if userinput:
            path, botmsg = await interactive_embed(ctx, botmsg, path, userinput)
            if path == '..':
                await settings(ctx, *args[:-1], botmsg=botmsg)
            elif path:
                await settings(ctx, *args, path, botmsg=botmsg)

    except Exception as e:
        if isinstance(e, asyncio.TimeoutError):
            await botmsg.clear_reactions()
        else:
            embed = discord.Embed.from_dict({'description': str(e), 'color': 16711680})
            if locals()['botmsg']:
                await botmsg.clear_reactions()
                await botmsg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
            raise(e)


import atexit
atexit.register(save, MEMORY.database, CONFIG['filename'])
BOT.run(CONFIG['token'])