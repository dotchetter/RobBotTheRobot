import discord
import praw
import CommandIntegrator as ci
from CommandIntegrator.enumerators import CommandPronoun
from CommandIntegrator.logger import logger
from redditjoke import RedditJoke


class RedditJokeFeatureCommandParser(ci.FeatureCommandParserBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RedditJokeFeature(ci.FeatureBase):

    FEATURE_KEYWORDS = (
        'skämt', 'meme',
        'skoja', 'skoj',
        'humor', 'roligt',
        'skämta'
    )

    def __init__(self, *args, **kwargs):
        self.command_parser = RedditJokeFeatureCommandParser()
        self.command_parser.keywords = RedditJokeFeature.FEATURE_KEYWORDS
        self.command_parser.callbacks = {
            'meme': self.get_random_joke,
            'skämt': self.get_random_joke,
            'skämta': self.get_random_joke,
            'skoja': self.get_random_joke,
            'skoj': self.get_random_joke,
            'humor': self.get_random_joke,
            'roligt': self.get_random_joke
        }
        
        self.mapped_pronouns = (
            CommandPronoun.INTERROGATIVE,
        )

        super().__init__(
            command_parser = self.command_parser,
            interface = RedditJoke(reddit_client = praw.Reddit(**kwargs))
        )

    @logger
    def get_random_joke(self) -> str:
        return self.interface.get()