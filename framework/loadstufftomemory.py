from . import formatting
import json

def config(item):
    ''' Loads config'''
    with open('config.json') as cfg:
        cfg = json.load(cfg)
        return cfg[item]

def loadfile(file):
    '''Loads the file'''
    try:
        with open(file) as handle:
            print('Disk read!')
            return json.load(handle)
    except FileNotFoundError:
        print("If you'd like to run this bot, please follow the instructions found in README.md")

FILENAME = config('filename')
MEMORY = loadfile(FILENAME)

def savefile(memory, file):
    '''Saves the file'''
    with open(file, 'w') as handle:
        print('Disk read!')
        json.dump(memory, handle, indent=4)
        print('Memory saved!')

def access(guild_id=None, category=None, item=None, value=None, mode=''):
    if isinstance(guild_id, int):
        guild_id = str(guild_id)

    if 'w' in mode:
        newdict = {guild_id: {category: {item: value}}}
        formatting.merge_dict(newdict, MEMORY)
    if 's' in mode:
        savefile(MEMORY, FILENAME)

    if '*' in mode:
        try:
            return MEMORY[guild_id][category] + MEMORY["global"][category]
        except KeyError:    
            if 'local' in mode:
                return MEMORY["global"][category]
            raise KeyError(f'{category} does not exist')
    else:
        try:
            MEMORY[guild_id][category][item]
            return MEMORY[guild_id][category][item]
        except KeyError:
            if value:
                return value
            if 'local' in mode:
                return MEMORY["global"][category][item]
            raise KeyError("No default value was set!")

if config('defaultprefix') != MEMORY["global"]["settings"]["prefix"]:
    access(guild_id="global", category="settings", item="prefix", value=config('defaultprefix'), mode='ws')

def prefix(bot=None, ctx=None, guild_id=None, mode='', prefix=None): # mode should be same as on storagehandler.store
    '''Prefix ??'''
    if not guild_id:
        guild_id = ctx.guild.id
    prefix = access(guild_id=guild_id, mode=mode,
                  category="settings", item="prefix", value=prefix)
    return prefix