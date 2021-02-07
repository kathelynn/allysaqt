### This bot is an experiment.

You can use anything from my projects as you wish. Please help me fix bugs and optimize code, any feedback is appreciated!

#### Dependencies:
* Python 3.7
* `discord.py` packages


#### If you still want to run this bot locally, please do the following by order:
1. Create a file named `config.json`. Inside the file, place the following:
```json
{
    "token": "TOKEN HERE",
    "filename":"allysaqt.json",
    "defaultprefix":"a$",
    "autosave":true,
    "autosaveinterval":1,
    "embedtimeout":15
}
```
2. Change the token to your Discord Bot's token. You can find this at `discord.com/developers > Selected App (i.e. the bot account) > Settings > Bot > Token > Click to Reveal Token`.
3. Create a file named `allysaqt.json` (or the filename you set in config). Inside the file, place the following:   
```json
{
    "global": {
        "settings": {
            "command_prefix": "a$",
            "command_error": false
        }, 
        "commands": {
            "ping": {
                "content":"Pong!"
            },
            "hi hello hey": {
                "content":"Hello~"
            }
        }
    }
}
```   
4. Optional: Inside on_ready function in bot.py, the channel ID should be replaced to your testing channel ID.

I can't guarantee the security and stable functionality when you deploy this. I can't fix bot issues related to your environment. I will gladly accept support and suggestions that won't conflict with my demands. Thank you!