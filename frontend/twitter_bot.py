import asyncio
from datetime import datetime
import os
import random
from requests_oauthlib import OAuth1Session
from commands.markov import MarkovHandler

class PhantomGamesBot:
    def __init__(self, markovHandler: MarkovHandler):
        self.markov = markovHandler
        self.twitter_auth_keys = {
            "consumer_key"          : os.environ["TWITTER_CONSUMER_KEY"],
            "consumer_secret"       : os.environ["TWITTER_CONSUMER_SECRET"],
            "access_token"          : os.environ["TWITTER_ACCESS_TOKEN"],
            "access_token_secret"   : os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
        }

        self.oauth = OAuth1Session(
            self.twitter_auth_keys["consumer_key"],
            client_secret=self.twitter_auth_keys["consumer_secret"],
            resource_owner_key=self.twitter_auth_keys["access_token"],
            resource_owner_secret=self.twitter_auth_keys["access_token_secret"]
        )

        self.last_tweet_time = datetime.now()
        try:
            with open("./commands/resources/twitter.txt", "r", encoding="utf-8") as f:
                time = f.read()
                self.last_tweet_time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        except:
            print("twitter.txt does not exist")

    def post_tweet(self):
        # create tweet
        message = self.markov.get_markov_string()
        tweet_payload = {"text" : message}

        # make the post
        response = self.oauth.post("https://api.twitter.com/2/tweets", json=tweet_payload)

        if response.status_code != 201:
            print(f"[Twitter Error] {response.status_code, response.text}")
        else:
            print(f"[{datetime.now()}] Generated Tweet: {message}")
            self.last_tweet_time = datetime.now()
            with open("./commands/resources/twitter.txt", "w", encoding="utf-8") as f:
                f.write(self.last_tweet_time.strftime("%Y-%m-%d %H:%M:%S"))

def run_twitter_bot(eventLoop, markovHandler: MarkovHandler):
    async def runBot():
        bot = PhantomGamesBot(markovHandler)
        while True:
            # post a tweet
            now = datetime.now()
            timelapse = now - bot.last_tweet_time
            if (timelapse.days >= 1 or timelapse.seconds / 3600 >= 14) and now.hour > 10:
                bot.post_tweet()

            # sleep for an hour and some random amount of minutes
            minutes = random.randrange(0, 29)
            await asyncio.sleep(60 * 60 + minutes * 60)

    eventLoop.create_task(runBot())
