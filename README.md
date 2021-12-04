# PhantomGamesBot
This is a Twitch chatbot used by https://twitch.tv/Phantom5800, written in python and fairly easy to edit and run.

## License

This project is licensed under MIT, see [License](LICENSE) for more details. While it is not required, it would be greatly appreciated for any forks to create pull requests back into the original repository. New features and optimizations are always welcome.

## Setup

1. Install Python 3.7+
2. Create a `.env` file (descripted below)
3. From a command line:
    * If you installed a version of Python that is not 3.9: `set PYVER=3.7`
    * `setup.bat`
    * `run.bat`

### Shortcuts
In Windows, it is possible to create a shortcut to the `run.bat` file and pin that to the start menu or task bar with a bit of effort.

1. Right click on `run.bat` and select `Create shortcut`
2. Right click on the new shortcut and change the target to `C:\Windows\System32\cmd.exe /c "C:\{path to bat file}\run.bat"`
3. Right click on the shortcut again and `Pin to Start`

## Env
At the root, anyone trying to run this will need a `.env` file that looks something like this:

```
TWITCH_OAUTH_TOKEN={OAUTH Token for bot account}
TWITCH_CLIENT_ID={Twitch Client ID}
BOT_NICK={Bot Account Name}
TWITCH_CHANNEL={Channel Name}
TIMER_CHAT_LINES=
TIMER_MINUTES=

BOT_PREFIX=!

SRC_USER={Speedrun.com username}

DISCORD_TOKEN={Discord bot Token}
```

In order to fill out the `.env`, you'll need to register as a [Twitch developer](https://dev.twitch.tv/console/apps/create) and create an application, this will get you a client id. Then [generate an oauth token](https://twitchapps.com/tmi/) and you'll be good to go for running the bot locally.

# Default Commands
Default command set that can be used by anyone.

### !bot
Provides a link to the github page for this bot's source code.

### !commands
Get a list of all available commands the chatbot can reply to.

### !game
Display the current game being played.

### !pb
Get the streamer's personal best speedrun time for given game and category. If no category is specified and the streamer has runs in multiple categories, a list will be given instead. The game is taken automatically from twitch.

```
!pb {category}
```

![Example of what a response looks like](./readme/images/pb.png)

### !quote
Display a random (or specified) quote from the internally stored list.

```
!quote
!quote {quote id}
```

### !title
Get the current title for the stream.

# Mod Commands
Set of commands that require moderator permissions in the channel in order to use.

### !so
Give a shoutout to another user, typically would be used for raid's or vip's.

```
!so {username}
```

## Custom Commands
Custom commands are basic command -> response events that can be managed by the streamer and moderators with the following commands. 

### !addcommand
Add a new custom command to the bot.

```
!addcommand {command} {response text}
```

### !editcommand
Edit the response for an existing command.

```
!editcommand {command} {response text}
```

### !removecommand
Remove a custom bot command.

```
!removecommand {command}
```

### !setcooldown
Set the cooldown on a custom command to restrict how often it can be used.

```
!setcooldown {command} {cooldown in seconds}
```

### Command Variables
These variables can be used in custom commands to fill in data dynamically.

* `$msg` - Replaced with the contents of the user's message (ignoring the command itself).
* `$randnum(min,max)` - Generates a random number in a range
    * `$randnum(10,500)` - Replaced with a random number in the inclusive range [10,500]
* `$randuser` - Mentions a random user in chat.
    * `$randmod` - Mentions a random moderator in chat.
    * `$randsub` - Mentions a random subscriber in chat.
* `$user` - Mentions the chatter that used the command.

## Quotes

### !addquote
Add a new quote to the list, current game and date are automatically added.

```
!addquote {new quote}
```

### !editquote
Edit an existing quote in case of typos, etc.

```
!editquote {quote id} {quote text}
```

### !removequote
Remove an existing quote, all quotes that appear after are shifted down accordingly so the ID sequence is never broken.

```
!removequote {quote id}
```

## Timer Events

Timer events are posted automatically at given intervals set by `TIMER_MINUTES` and `TIMER_CHAT_LINES` in `.env`. If a timer triggers and the required amount of chat messages have not passed, the timer will wait the full duration before checking again. This may need to be tweaked based on the streamer's chat and what they expect. In some cases it may be better to have shorter timers with a higher message requirement. Experimenting with the numbers is highly recommended.

### !disabletimer
Disable all bot timer messages.

### !enabletimer
Enable bot timer messages.

### !addtimer
Add a custom command to the timer queue.

```
!addtimer {command}
```

### !removetimer
Removes a command from the timer queue.

```
!removetimer {command}
```

### !timerevents
Get a list of all the current events added to the timer.
