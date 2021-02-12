### This bot is an experiment.

You can use anything from my projects as you wish. Please help me fix bugs and optimize code, any feedback is appreciated!


#### Dependencies:
* Python 3.7
* `discord.py` packages
* `hjson` packages



#### To update the bot:
> Please keep in mind that the bot does not update the config.hjson file at the moment. To fix that, you may run the setup again from 1-3 found below after updating.
```
git pull
```

#### If you still want to run this bot locally, please do the following by order:
1. Run the following in the terminal:
```python3 bot.py setup```
2. A file named `config.hjson` will be created. Open the file with any text editor and read carefully.
3. Change the token found in the file to your Discord Bot's token. You can find this at `discord.com/developers > Selected App (i.e. the bot account) > Settings > Bot > Token > Click to Reveal Token`.
4. Create a file named `allysaqt.hjson` (or the filename you set in config). Inside the file, place the following:   
```json
{
    "global": {
        "commands": {
            "hi hello hey": {
                "content": "Hiii qt!"
            }
        }
    },
    "TESTING SERVER ID HERE": {
        "commands": {
            "ping": {
                "content": "Pong!"
            }
        }
    }
}
```

I can't guarantee security and stable functionality when you deploy this. I can't fix bot issues related to your environment. I will gladly accept support and suggestions that won't conflict with my demands. Thank you!