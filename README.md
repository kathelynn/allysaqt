#### This bot is an experiment, and is not meant to be ran individually.
You can use anything from my projects as you wish. Please help me fix bugs and optimize code, any feedback is appreciated!

If you still want to run this bot locally, please do the following by order:
1. Create a file named `config.json`. Inside the file, place the following:
```json
{
    "token": "TOKEN HERE",
    "filename":"allysaqt.json",
    "defaultprefix":"a$",
    "autosaveinterval":10,
    "embedtimeout":15
}
```
2. Change the token to your Discord Bot's token. You can find this at `discord.com/developers > Selected App (i.e. the bot account) > Settings > Bot > Token > Click to Reveal Token`.
3. Create a file named `allysaqt.json` (or the filename you set in config). Inside the file, place the following:   
```json
{
    "global": {
        "settings": {
            "prefix": "a$"
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

If you want to contact me in case you want to help me on hosting this bot, [you could try contacting me on Discord](https://discord.bio/p/kathelynn).