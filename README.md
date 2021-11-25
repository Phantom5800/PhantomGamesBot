# PhantomGamesBot
This is a Twitch chatbot used by https://twitch.tv/Phantom5800, written in python and fairly easy to edit and run.

## Setup

1. Install Python 3.7+
2. Create a `.env` file (descripted below)
3. From a command line:
    * `pip install pipenv`
    * `pipenv --python 3.7` (or whatever version you installed)
    * `pipenv install twitchio`
    * `pipenv install srcomapi`
    * `run.bat` or `pipenv run python bot.py`

## Env
At the root, anyone trying to run this will need a `.env` file that looks something like this:

```
TMI_TOKEN={OAUTH Token}
CLIENT_ID={Twitch Client ID}
BOT_NICK={Bot Account Name}
BOT_PREFIX=!
CHANNEL={Channel Name}
SRC_USER=
TWITTER=
GITHUB=
YOUTUBE=
```

In order to fill out the `.env`, you'll need to register as a [Twitch developer](https://dev.twitch.tv/console/apps/create) and create an application, this will get you a client id. Then [generate an oauth token](https://twitchapps.com/tmi/) and you'll be good to go for running the bot locally.

## Default Commands

### !bot
Provides a link to the github page for this bot's source code.

### !game
Display the current game being played.

### !pb
Get the streamer's personal best speedrun time for given game and category. If no category is specified and the streamer has runs in multiple categories, a list will be given instead. The game is taken automatically from twitch.

```
!pb {category}
```

### !quote
Display a random (or specified) quote from the internally stored list.

```
!quote
!quote {quote id}
```

### !github
Provides a link to the streamer's github profile.

### !twitter
Provides a link to the streamer's twitter page.

### !youtube
Provides a link to the streamer's youtube channel.

## Mod Commands

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
