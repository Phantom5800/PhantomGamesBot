# PhantomGamesBot
This is a Twitch chatbot used by https://twitch.tv/Phantom5800, written in python and fairly easy to edit and run.

## Setup
I'll add instructions here eventually maybe

## Env
At the root, anyone trying to run this will need a `.env` file that looks something like this:

> TMI_TOKEN={OAUTH Token}  
> CLIENT_ID={Twitch Client ID}  
> BOT_NICK={Bot Account Name}  
> BOT_PREFIX=!  
> CHANNEL={Channel Name}  
> TWITTER=  
> GITHUB=  
> YOUTUBE=  

## Default Commands

### !bot
Provides a link to the github page for this bot's source code.

### !game
Display the current game being played.

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
