import asyncio, concurrent, itertools, string, sqlite3
import discord
from discord.ext import commands
from collections import OrderedDict
class hjson:
    from hjson import dump, load

''' Automation '''

from sys import argv
if len(argv) > 1 and argv[1] == "setup":
    print('Setting up...')
    with open('setup/config_copy.hjson', 'r') as copy:
        copy = copy.read()
        with open('config.hjson', 'w') as f:
            f.write(copy)
    print('Done! Refer back to README to complete the process.')
    exit()
del argv

'''File loader/saving'''

def loaddisk(file):
    try:
        with open(file) as f:
            print(f'{file} accessed!')
            return hjson.load(f)
    except FileNotFoundError:
        print(f"""Please follow the instructions found in README.md,
        otherwise if error still occurs please report issues on GitHub.
        Missing file: {file}""")
        exit()

def loaddb(file):
    print(f'{file} accessed!')
    return sqlite3.connect(file)

def save(json=None, file=None, db=None):
    if json and file:
        with open(file, 'w') as f:
            print('Saving to disk..')
            hjson.dump(json, f, indent=4)
            print('Saved successfully!')
    if db:
        db.commit()

async def autosave(json=None, file=None, interval=0, db=None):
    interval = interval*60
    while True:
        await asyncio.sleep(interval)
        save(json, file, db)
        
CONFIG = loaddisk('config.hjson')
with open(f"{CONFIG['setup_directory']}/config_copy.hjson", 'r') as f:
    for key, value in hjson.load(f).items():
        if key not in CONFIG:
            CONFIG[key] = value
            print(f'{key} is missing! Using values from config_copy.hjson. Please read README.md for more information.')

'''Special functions'''

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

def str_bool(string):
    s = string.casefold()
    if s in ['true', 't', 'on']: return True
    elif s in ['false', 'f', 'off']: return False
    else: raise(f'`true`/`t`/`on` or `false`/`f`/`off`, not {s}') ###

'''Bot memory'''

class db:
    conn = loaddb(CONFIG['dbfilename'])
    cursor = conn.cursor()
    def __new__(cls):
        return db.cursor
    def fetch(sql, *parameters):
        db.cursor.execute(sql, *parameters)
        return db.cursor.fetchone()

    current_ver = cursor.execute('PRAGMA user_version') and cursor.fetchone()[0]
    with open(f"{CONFIG['setup_directory']}/db_maintenance.hjson") as f:
        for version, commands in hjson.load(f, object_pairs_hook=OrderedDict).items():
            if current_ver < int(version):
                cursor.executescript(commands)
        cursor.execute(f'PRAGMA user_version = {version};')
        print(f"Database version {cursor.execute('PRAGMA user_version') and cursor.fetchone()[0]}")

class json:
    json = loaddisk(CONFIG['filename'])
    def __new__(cls):
        return json.json
    def overwrite(path, value):
            append = {}
            path = path.split('/')
            node = nested_dict(path[:-1], append)
            node[path[-1]] = value
            merge_dict(append, json())

class setting:
    def __new__(cls, ctx, item):
        owo = db.fetch(f'SELECT {item} FROM settings WHERE serverID=?;', (ctx.guild.id,))[0]
        return owo if owo else CONFIG[f'default{item}']
        
    def update(ctx, item, value, conditions=None):
        guild_id = ctx.guild.id
        owo = db.fetch('SELECT ? FROM settings WHERE serverID=?;', (item, guild_id))
        if conditions is None or conditions(old=owo, new=value):
            if owo:
                db().execute(f'UPDATE settings SET {item}=? WHERE serverID=?;', (value, guild_id))
            else:
                db().execute(f'INSERT INTO settings ({item}, serverID) VALUES (?, ?);', (value, guild_id))

def command_prefix(bot, ctx):
    owo = db.fetch('SELECT command_prefix FROM settings WHERE serverID=?;', (ctx.guild.id,))[0]
    return owo if owo else CONFIG['defaultcommand_prefix']

'''Bot Logic'''

BOT = commands.Bot(command_prefix=command_prefix)

@BOT.event
async def on_ready():
    print(f'Logged on as {BOT.user} ({BOT.user.id})')
    if CONFIG['autosave']:
        asyncio.create_task(autosave(json(), CONFIG['filename'], CONFIG['autosaveinterval'], db.conn))

@BOT.event
async def on_message(message):
    print(f'{message.author} from {message.channel}: {message.content}')
    await BOT.process_commands(message)

class CMD:
    def __new__(cls, ctx=None, command=None):
        guild_id = str(ctx.guild.id)
        if command:
            command = ctx.message.content[len(ctx.prefix):].split()
            if len(command) > 1:
                args = command[1:]
            command[0] = command[0].lower()

        if ctx and command:
            for key, value in json()[guild_id]['commands'].items():
                if command[0] in key:
                    return value
            raise KeyError(f'Command `{command}`')
        elif command:
            for key,value in json()['global']['commands'].items():
                if command[0] in key:
                    return value
            raise KeyError(f'Command `{command}`')
        elif ctx:
            return json()[guild_id]['commands']
        else:
            pass
        
    def if_global(command):
        for key, value in json()['global']['commands'].items():
            if command in key:
                return True
        return False
    def if_local(ctx, command):
        for key,value in json()[str(ctx.guild.id)]['commands'].items():
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
    errortype = type(error.__cause__) if hasattr(error, '__cause__') else type(error)
    if errortype is concurrent.futures._base.TimeoutError:
        pass
    if errortype is commands.CommandNotFound:
        try:
            output = CMD(ctx, ctx.message.content)
        except KeyError:
            if setting(ctx, 'command_error'):
                    embed = discord.Embed.from_dict({"description":"Command not found", "color":16711680})
                    await ctx.send(embed=embed)
        else:
            send = {}
            items = ctx.message
            for key, value in output.items():
                # need to copy instead of pointing to output var'
                if key in ['content','tts','embed','file']:
                    send[key] = string.Template(value).safe_substitute(**items)
            if 'embed' in send:
                send['embed'] = discord.Embed.from_dict(send['embed'])
            await ctx.send(**send)
    elif setting(ctx, 'command_error'):
        if setting(ctx, 'command_error'):
                embed = discord.Embed.from_dict({'description':'An error occured', 'color':16711680}) ###
                await ctx.send(embed=embed)
        print(errortype)
        raise error
    else:
        repr(error)
        raise error

### Playing around a bit here
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

class interactive_embed:
    class reaction:
        def __init__(self, iterable, up=False):
            self.reactions = iterable
            self.up = up
    class message:
        def __init__(self, message, up=False):
            self.message = message
            self.up = up

    async def __new__(cls, ctx, botmsg, userinput):
        # replace isinstance with classes 
        if isinstance(userinput, interactive_embed.reaction):
            reactions = userinput.reactions
            if userinput.up:
                reactions['◀'] = None
            reactions['❎'] = None
        elif isinstance(userinput, interactive_embed.message):
            reactions = {'✏': None, '◀': None, '❎': None}
        else:
            raise Exception() ###
        
        tasks = set()
        for reaction, name in reactions.items():
            tasks.add(asyncio.ensure_future(botmsg.add_reaction(reaction)))
        def check(reaction, user):
            return str(reaction.emoji) in reactions and user.id is ctx.author.id and reaction.message.id == botmsg.id
        reaction, user = await BOT.wait_for('reaction_add', check=check, timeout=EMBED_TIMEOUT)
        emoji = str(reaction.emoji)

        if emoji == '✏':
            await botmsg.clear_reactions()
            embed = {'description': userinput.message}
            await botmsg.edit(embed=discord.Embed(description=userinput.description))
            def check(message):
                return message.author is ctx.author and message.channel is botmsg.channel
            message = await BOT.wait_for('message', check=check, timeout=EMBED_TIMEOUT)
            await message.delete(delay=0) # delay puts task in background and ignores if it cant be deleted
            return message.content, botmsg
        elif emoji == '◀':
            return '..'
        elif emoji == '❎':
            await botmsg.clear_reactions()
            return 0, botmsg
        else:
            return userinput.reactions[emoji], botmsg

@BOT.command(aliases=['set'])
async def settings(ctx, *args, botmsg=None):
    embed = {}
    userinput = None
    guild_id = str(ctx.guild.id)

    def prefix(new):
        def conditions(old, new):
            if old == new:
                raise Exception('Pick a different prefix') ###
            characters = f'{string.digits}{string.ascii_letters}{string.punctuation}'
            if len(new) > 3:
                raise Exception('3 too many')
            for character in new:
                if character not in characters:
                    raise Exception(f'Invalid character {character}') ###
            return True
        setting.update(ctx, 'command_prefix', new, conditions)
        return {
            "description": f"Prefix for this server has been changed to `{db.fetch('SELECT command_prefix FROM settings WHERE serverID=?', (ctx.guild.id,))[0]}`.", # the index cleans up the tuple
            "color": 65280
        }
    
    def cmdalerts(new):
            setting.update(ctx, 'command_error', str_bool(new))
            return {
                "description": f"Command alerts for this server is set to `{bool(db.fetch('SELECT command_prefix FROM settings WHERE serverID=?', (ctx.guild.id,))[0])}`.",
                "color": 65280
            }

    ### work in progress
    template = {
        "header": {
            "name": f"{' / '.join([x.title() for x in itertools.chain((ctx.guild.name,), args)])}",
            "icon_url": str(ctx.guild.icon_url)
        },
        "default": {
            "embed": {
                "title": "Settings",
                "description": f"{ctx.prefix}set ..."
            },
            "links": ['prefix', 'cmdalerts']
        },
        "prefix": {
            "title": "Prefix",
            "icon": "1️⃣",
            "info": f"{ctx.prefix}",
            "action": {
                "permission": ctx.author.guild_permissions.manage_guild,
                "do": prefix
            }
        },
        "cmdalerts": {
            "title": "Command Alerts",
            "icon": "2️⃣",
            "info":  f"{bool(setting(ctx, 'command_error'))}",
            "action": {
                "permission": ctx.author.guild_permissions.manage_guild,
                "do": cmdalerts
            }
        }
    }

    if not args:
        embed = template['default']['embed']
        embed['fields'] = []
        userinput = {}
        for name in template['default']['links']:
            icon = template[name]['icon']
            userinput[icon] = name
            embed['fields'].append( {
                "name": f"{icon} {template[name]['title']}",
                "value": f"{name} {template[name]['info']}"
            } )
        userinput = interactive_embed.reaction(userinput)
    else:
        navigate = template[args[0]]
        for arg in args[1:]:
            if arg in navigate:
                navigate = navigate[arg]
            else:
                if 'action' in navigate and navigate['action']['permission']:
                    async with ctx.channel.typing():
                        botmsg = None
                        embed = navigate['action']['do'](*args[args.index(arg):]) ### will probably need a faster initiative
                if 'links' in navigate:
                    for name in template['default']['links']:
                        icon = template[name]['icon']
                        userinput[icon] = name
                        embed['fields'].append( {
                            "name": f"{icon} {template[name]['title']}",
                            "value": f"{name} {template[name]['info']}"
                        } )
                    userinput = interactive_embed.reaction(userinput)
        if not embed:
            embed = {
                "title": navigate['title'], 
                "description": navigate['info'] 
            }
        if 'action' in navigate and not navigate['action']['permission']:
            embed['footer'] = {'text': 'You do not have permission to change this setting'} ###

    embed['author'] = template['header']
    
    embed = discord.Embed.from_dict(embed)
    if botmsg:
        await botmsg.edit(embed=embed)
    else:
        botmsg = await ctx.send(embed=embed)

    if userinput:
        userinput.up = len(args) > 0
        path, botmsg = await interactive_embed(ctx, botmsg, userinput)
        if path == '..':
            await asyncio.create_task(settings(ctx, *args[:-1], botmsg=botmsg))
        elif path:
            await asyncio.create_task(settings(ctx, *args, path, botmsg=botmsg))
        await botmsg.clear_reactions()

import atexit
atexit.register(save, json(), CONFIG['filename'], db.conn)
BOT.run(CONFIG['token'])