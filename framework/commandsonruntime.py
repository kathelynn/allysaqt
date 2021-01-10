'''Custom commands handled at runtime'''
from . import loadstufftomemory

class CommandExists(Exception):
    '''An exception for of a command already exists'''

def if_global(command):
    '''If a command is global'''
    try:
        loadstufftomemory.access(guild_id="global", mode='', category='commands',
                             item=command, value=None)
        return True
    except KeyError:
        return False

def if_local(command, guild_id=None):
    '''If a command is local'''
    try:
        loadstufftomemory.access(guild_id=guild_id, mode='local', category='commands',
                             item=command, value=None)
        return True
    except KeyError:
        return False

def if_unused(command, guild_id=None):
    '''If a command is unused'''
    if if_global(command) or if_local(command, guild_id):
        return False
    return True

def create(command, ctx=None, guild_id=None, **kwargs):
    '''Create a new command'''
    if not if_unused(command, guild_id):
        raise CommandExists(f'{command} exists in dictionary!')
    if 'json' not in kwargs:
        json = {}
        items = ['content', 'embed']
        for item in items:
            try:
                json[item] = kwargs[item]
            except:
                pass
    if 'json' in locals(): 
        loadstufftomemory.access(guild_id=guild_id, mode='w*', category='commands',
                             item=command, value=json)
    else: raise TypeError('JSON cannot be empty')

def load(ctx=None, guild_id=None, mode='r*'):
    '''Load saved commands'''
    if not guild_id:
        guild_id = ctx.guild.id
    command = ctx.message.content[len(ctx.prefix):].split()
    if isinstance(command, list):
        args = command[1:] # pylint:disable=unused-variable
        command = command[0].lower()
    else:
        command.lower()
    commands = loadstufftomemory.access(guild_id=guild_id, mode=mode, category='commands', item=command[0])
    if '*' in mode:
        for key, value in commands.items():
            if command in key:
                return value
        raise KeyError(f'Command "{command}" is not found')
    else:
        return commands