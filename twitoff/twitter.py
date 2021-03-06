"""Retrieve tweets, embeddings, and put them in our Database"""
from os import getenv
import tweepy
import spacy
from .models import DB, Tweet, User


TWITTER_API_KEY = getenv('TWITTER_API_KEY')
TWITTER_API_KEY_SECRET = getenv('TWITTER_API_KEY_SECRET')

TWITTER_AUTH = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_KEY_SECRET)

TWITTER = tweepy.API(TWITTER_AUTH)

nlp = spacy.load('my_model')


def vectorize_tweet(tweet_text):
    return nlp(tweet_text).vector


def update_or_add_user(username):
    try:
        """Create user based on `username`"""
        twitter_user = TWITTER.get_user(username)

        # crazy syntax:
        # If they exist then update that user, if we get something back
        # then instantiate a new user
        db_user = (User.query.get(twitter_user.id)) or User(
            id=twitter_user.id, name=username)

        # Add the user to our database
        DB.session.add(db_user)

        tweets = twitter_user.timeline(
            count=200,
            exclude_replies=True,
            include_rts=False,
            tweet_mode='Extended',
            since_id=db_user.newest_tweet_id
        )  # a list of tweets from `username`

        # empty tweets = false
        if tweets:
            db_user.newest_tweet_id = tweets[0].id

        for tweet in tweets:
            # vectorize each tweet
            vectorized_tweet = vectorize_tweet(tweet.text)
            # Create tweet to add to DB
            db_tweet = Tweet(id=tweet.id, text=tweet.text,
                             vect=vectorized_tweet)
            # Append each tweet from `username` to username.tweets
            db_user.tweets.append(db_tweet)
            # Add db_tweet to Tweet DB
            DB.session.add(db_tweet)
    except Exception as e:
        print(f'Error processing {username}: {e}')
        raise e
    else:
        # Commit
        DB.session.commit()
