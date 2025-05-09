# PhantomGamesBot
This is a Twitch and Discord chatbot used by https://twitch.tv/Phantom5800, written in python and fairly easy to edit and run.

## License

This project is licensed under MIT, see [License](LICENSE) for more details. While it is not required, it would be greatly appreciated for any forks to create pull requests back into the original repository. New features and optimizations are always welcome.

# Spam Propagation
The bot supports automatically posting nonsense based on messages it has read from twitch chat in the past. While chat logging is enabled, all twitch chat messages are logged to a text file. The next time the bot is restarted, it will generate a markov chain based on the current data set. These messages can be set to post automatically in chat on a timer using the `.env` configs.

### !chat ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Forces the bot to post an automatically generated message based on data it has been given through previous twitch chat messages.

# Default Commands
Default command set that can be used by anyone.

## Basic Commands

### !bot ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Provides a link to the github page for this bot's source code.

### !commands ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Get a list of all available commands the chatbot can reply to. In discord, the list provided only pulls from the custom commands created by moderators on twitch. Default bot commands in discord are provided by `!help`.

### !ctof ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Convert Celcius to Farenheit.

### !ftoc ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Convert Farenheit to Celcius.

### !follow ![](./readme/images/twitch.png)
Posts a generic message to follow the stream. If there is a follow goal on twitch, it will show the progress towards that goal as well.

Note: _This feature only works if a user specific OAUTH token is configured as part of the `.env`_

### !followage ![](./readme/images/twitch.png)
Gets the length of time a user has followed the channel for.

### !game ![](./readme/images/twitch.png)
Display the current game being played.

### !help ![](./readme/images/discord.png)
Provides a basic help dialog, giving discord users more detail into what the bot is capable of.

### !newvid ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Posts a link to the latest YouTube upload associated with the streamer.

### !subgoal ![](./readme/images/twitch.png)
Posts a generic sub message. If there is a monthly sub goal set by `!setsubgoal`, it will show the current progress towards the goal.

Note: _This feature only works if a user specific OAUTH token is configured as part of the `.env`_

### !title ![](./readme/images/twitch.png)
Get the current title for the stream.

### !youtube ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Posts a link to the streamers associated YouTube page as a chat announcement, starting with a subgoal if one exists.

## Fun Stuff

### !anime ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Recommends a random anime to a user.

### !animeinfo ![](./readme/images/discord.png)
Gives an embedded block of info on a given anime.

![](./readme/images/animeinfo.png)

### !pb ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Get the streamer's personal best speedrun time for given game and category. If no category is specified and the streamer has runs in multiple categories, a list will be given instead. The game is taken automatically from twitch.

```
!pb {category}
```

![Example of what a response looks like](./readme/images/pb.png)

On discord, this command behaves slightly different. Instead of taking a category, it takes a game, and returns all PB's recorded for the given game.

```
!pb {game}
```

![Example of a response in discord](./readme/images/pb_discord.png)

### !quote ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Display a random (or specified) quote from the internally stored list.

```
!quote
!quote {quote id}
!quote latest
```

### !slots ![](./readme/images/twitch.png) ![](./readme/images/discord.png)
Gives the user a slot machine style result of three random emotes.

![Example slots roll](./readme/images/slots.png)

### !speed ![](./readme/images/twitch.png) ![](./readme/images/discord.png)

Recommends a random game and speedrun category to a user.
```
!speed - get a completely random game and category
!speed [game] - get a random game and category that fits [game] as a search term for games
!speed user:[username] - gets a random game and category that a given user has done before
```

# Mod Commands
Set of commands that require moderator permissions in the channel in order to use.

### !so ![](./readme/images/twitch.png)
Give a shoutout to another user, typically would be used for raid's or vip's.

```
!so {username}
```

## Custom Commands
Custom commands are basic command -> response events that can be managed by the streamer and moderators with the following commands. All commands created in this way are available on both Twitch and Discord, however some command variables may not function as intended on both platforms.

### !addcommand ![](./readme/images/twitch.png)
Add a new custom command to the bot.

```
!addcommand {command} {response text}
```

Aliases: _!addcom_

### !editcommand ![](./readme/images/twitch.png)
Edit the response for an existing command.

```
!editcommand {command} {response text}
```

Aliases: _!editcom_

### !removecommand ![](./readme/images/twitch.png)
Remove a custom bot command.

```
!removecommand {command}
```

Aliases: _!removecom !delcom_

### !setcooldown ![](./readme/images/twitch.png)
Set the cooldown on a custom command to restrict how often it can be used.

```
!setcooldown {command} {cooldown in seconds}
```

### !setrng ![](./readme/images/twitch.png)
Sets the random chance the bot will respond to a given message.

```
!setrng {command} [1,100]
```

### Command Variables
These variables can be used in custom commands to fill in data dynamically.

#### Twitch-Only Variables ![](./readme/images/twitch.png)

* `$msg` - Replaced with the contents of the user's message (ignoring the command itself).
* `$randuser` - Mentions a random user in chat.
    * `$randmod` - Mentions a random moderator in chat.
    * `$randsub` - Mentions a random subscriber in chat.
* `$user` - Mentions the chatter that used the command.

#### Shared Variables ![](./readme/images/twitch.png) ![](./readme/images/discord.png)

* `$count` - The number of times this command has been called (will not track previous calls if this variable has been added later).
* `$randnum(min,max)` - Generates a random number in the inclusive range [min,max].

## Quotes

### !addquote ![](./readme/images/twitch.png)
Add a new quote to the list, current game and date are automatically added.

```
!addquote {new quote}
```

### !editquote ![](./readme/images/twitch.png)
Edit an existing quote in case of typos, etc.

```
!editquote {quote id} {quote text}
```

### !removequote ![](./readme/images/twitch.png)
Remove an existing quote, all quotes that appear after are shifted down accordingly so the ID sequence is never broken.

```
!removequote {quote id}
```

Aliases: _!delquote_

## Timer Events

Timer events are posted automatically at given intervals set by `TIMER_MINUTES` and `TIMER_CHAT_LINES` in `.env`. If a timer triggers and the required amount of chat messages have not passed, the timer will wait the full duration before checking again. This may need to be tweaked based on the streamer's chat and what they expect. In some cases it may be better to have shorter timers with a higher message requirement. Experimenting with the numbers is highly recommended.

### !addtimer ![](./readme/images/twitch.png)
Add a custom command to the timer queue.

```
!addtimer {command}
```

### !removetimer ![](./readme/images/twitch.png)
Removes a command from the timer queue.

```
!removetimer {command}
```

### !timerevents ![](./readme/images/twitch.png)
Get a list of all the current events added to the timer.


# Discord Settings
PhantomGamesBot supports discord as well. The only setup required is to create an application in the [Discord Developer Portal](https://discord.com/developers/applications) and copy the token for the bot into `.env`. Other settings in the portal depend entirely on what you would be using the bot for.

![Discord token location](./readme/images/discord_token.png)

# YouTube Integration
Support for getting information about a designated YouTube channel such as latest video, subscriber counts, etc.
These queries are used by the Twitch and Discord bots to provide information in useful commands.

This integration can be configured with extra commands that are only usable by the streamer. The only environment variable required for this integration is `YOUTUBE_API_KEY` which can be acquired through a Google developer account (example: https://console.cloud.google.com/apis/credentials/).

### !setyoutubechannel ![](./readme/images/twitch.png)
This command sets the youtube channel info associated with the twitch account. This should only ever have to be used once unless these values change for whatever reason. These values are used internally when performing YouTube API queries.

```
!setyoutubechannel {username} {channel_id}
```

Example:
```
!setyoutubechannel Phantom5801 UCBi_wHL3iqQJJ3j4KU-jUOA
```
Note: username is the actual username of the account, not the "YouTube Handle."

### !setyoutubehandle ![](./readme/images/twitch.png)
Sets the handle for the streamers associated YouTube channel. This is entirely optional, but if provided, will be used instead of the channel_id when using the `!youtube` command.

### !setyoutubesubgoal ![](./readme/images/twitch.png)
Sets the YouTube subgoal to be displayed in Twitch chat with a designated message. If the goal is set to 0, only the message will be displayed by the `!youtube` command without any subgoal reference.

```
!setyoutubesubgoal 1000 Once we hit this goal we will be doing a thing!
```

# Twitter Settings
This bot will occasionally post on a connected Twitter account using text generated by Twitch chat logs. In order to do this, you will need a Twitter developer account with which you wish to post messages to and fill in `TWITTER_CONSUMER_KEY_*` with the API Key and Secret in your Twitter Developer Dashboard, and `TWITTER_ACCESS_TOKEN_*` with the relevant Access Token and Secret. Once configured, messages will be posted approximately once a day around the middle of the day with some amount of small variance.

# Setup

If anyone else wants to run a version of this bot, or fork it.

## Initial Setup

1. Install Python 3.7+ (make sure it goes in AppData on Windows!!!)
2. Create a `.env` file (described below)
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
# Twitch Auth
TWITCH_OAUTH_TOKEN={OAUTH Token for bot account}
TWITCH_CLIENT_ID={Twitch Client ID}
TWITCH_CHANNEL_TOKEN_{channel_name}={OAUTH Token for channel specific features}
TWITCH_CHANNEL_ID_{channel_name}={Use: https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/}

# Twitch Connections
BOT_NICK={Bot Account Name}
TWITCH_CHANNEL={comma seperated list of channel names}

# Twitch Auto Timer
TIMER_CHAT_LINES=
TIMER_MINUTES=

# Twitch Markov posting channel overrides
AUTO_CHAT_LINES_MIN_{channel}={minimum number of lines posted in [channel] before the bot posts a message}
AUTO_CHAT_LINES_MOD_{channel}=
AUTO_CHAT_MINUTES=

# Bot command prefix
BOT_PREFIX=!

# Speedrun.com Data
SRC_USER={comma seperated list of speedrun.com username}

# Discord bot settings
DISCORD_TOKEN={Discord bot Token}
DISCORD_SHARED_API_PROFILE={twitch name for shared resources like custom commands and quotes}
DISCORD_STREAMER_ID={Copy ID from Server Owner}
DISCORD_SERVER_ID={Copy ID from Server}
DISCORD_LIVE_NOW_ID={Copy ID from "Live Now" role}

# YouTube Settings
YOUTUBE_API_KEY={https://console.cloud.google.com/apis/credentials/}

# Twitter API Settings
TWITTER_CONSUMER_KEY=
TWITTER_CONSUMER_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
```

In order to fill out the `.env`, you'll need to register as a [Twitch developer](https://dev.twitch.tv/console/apps/create) and create an application, this will get you a client id. Then [generate an oauth token](https://twitchapps.com/tmi/) and you'll be good to go for running the bot locally.

## OAuth
This is an example URI used to generate a valid OAuth user token for all Twitch APIs used:

```
https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=<enter your client id here>&redirect_uri=http%3A//localhost%3A3000&scope=bits%3Aread+chat%3Aread+chat%3Aedit+channel%3Aedit%3Acommercial+channel%3Amanage%3Abroadcast+channel%3Amoderate+channel%3Amanage%3Apolls+moderator%3Aread%3Achat_settings+moderator%3Amanage%3Achat_settings+moderator%3Aread%3Ashoutouts+moderator%3Amanage%3Ashoutouts+channel%3Amanage%3Apredictions+channel%3Aread%3Agoals+channel%3Aread%3Aredemptions+channel%3Aread%3Asubscriptions+channel%3Amanage%3Avips+moderator%3Aread%3Achatters+moderator%3Amanage%3Aannouncements+moderator%3Amanage%3Abanned_users+channel%3Aread%3Aads+channel%3Amanage%3Aads+channel%3Amanage%3Aschedule+moderator%3Aread%3Afollowers+moderator%3Amanage%3Awarnings
```

For readability sake, this is the list of permissions granted to the bot:

* bits:read - bit events
* chat:read - read chat messages
* chat:edit - post in chat
* channel:edit:commercial - run ads (currently not used, but could be)
* channel:read:ads - ad schedule
* channel:read:goals - read sub and follower goals set for stream
* channel:read:redemptions - channel point redemptions
* channel:read:subscriptions - view list of subscribers to a channel and check if user is subscribed
* channel:manage:ads - allows snoozing ads
* channel:manage:broadcast - modify game, title, etc.
* channel:manage:polls - view, create and end polls
* channel:manage:predictions - create and end predictions
* channel:manage:schedule - post schedules automatically
* channel:manage:vips - view, add and remove vips
* channel:moderate - moderator actions
* moderator:read:chat_settings - check for chat settings like slow mode, sub mode, etc.
* moderator:read:chatters - view list of people in chat
* moderator:read:followers - check follower info
* moderator:read:shoutouts - view shoutouts
* moderator:manage:announcements - post announcements
* moderator:manage:banned_users - can timeout / ban users
* moderator:manage:chat_settings - modify chat settings like slow mode, sub mode, etc.
* moderator:manage:shoutouts - send shoutouts
* moderator:manage:warnings - can provide warnings to users
