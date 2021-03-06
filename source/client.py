import os
import json
import asyncio
import discord

from schedule import Scheduler
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from dotenv import load_dotenv
from pathlib import Path
from custom_errs import *
from event import Event
from weekdays import Weekdays

from features.LunchMenuFeature import LunchMenuFeature
from features.RedditJokeFeature import RedditJokeFeature
from features.ScheduleFeature import ScheduleFeature
from features.CoronaSpreadFeature import CoronaSpreadFeature
from features.RankingMembersFeature import RankingMembersFeature
from features.HelpQueueFeature import HelpQueueFeature
from CommandIntegrator.logger import logger
from CommandIntegrator import CommandProcessor, PronounLookupTable, PollCache

"""
Details:
    2020-04-24 Simon Olofsson

Module details:
    Service main executable

Synposis:
    Initialize the bot with api reference to Discords
    services. Instantiate bot intelligence from separate
    modules. 
"""


class RobBotClient(discord.Client):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)

        self._scheduler = Scheduler()
        self._pollcache = PollCache(silent_first_call = True)
                        
        self.loop.create_task(self.run_scheduler())
        self.loop.create_task(
            self.send_to_role(
                method = helpqueue_ft.get_notification_if_helpqueue_changed, 
                role = 'teacher'))
        
        self._guild = kwargs['DISCORD_GUILD']
    
    @property
    def scheduler(self):
        return self._scheduler

    @logger
    async def on_ready(self) -> None:
        """
        This method is called as soon as the bot is online.
        """
        for guild_name in client.guilds:
            if guild_name == self._guild:
                break
    @logger
    async def on_member_join(self, member: discord.Member) -> None:
        """
        If a new member just joined our server, greet them warmly!
        """
        with open('greeting.dat', 'r', encoding = 'utf-8') as f:
            greeting_phrase = f.read()
            await member.create_dm()
            await member.dm_channel.send(greeting_phrase)
    
    @logger    
    async def on_message(self, message: discord.Message) -> None: 
        """
        Respond to a message in the channel if someone
        calls on the bot by name, asking for commands.
        """

        if message.content.lower().startswith('!') and message.author != client.user:
            response = processor.process(message).response()
            if response: await message.channel.send(response)

    @logger
    async def send_to_role(self, method: callable, role: str) -> None:
        """
        Send string message to users in the guild with 
        the @teacher role only, as a private message.
        :param method:
            method to call with pollcache instance
            looping over infinitely, only sending 
            deviating results (updates)
        :param role:
            string, the name of the role on the server
            to send messages to.
        """
        while not self.is_closed():
            res = self._pollcache(method)
            if not res:
                await asyncio.sleep(0.01)
                continue
            for user in self.get_all_members():
                if len([i for i in user.roles if i.name == role]):
                    await user.create_dm()
                    await user.dm_channel.send(res)
            await asyncio.sleep(0.01)

    @logger            
    async def run_scheduler(self) -> None:
        """
        Loop indefinitely and send messages that are pre-
        defined on a certain day and a certain time. 
        """

        await client.wait_until_ready()

        while not self.is_closed(): 
            result = self.scheduler.run_pending(passthrough = True)

            if not result or datetime.now().hour >= 22 or datetime.now().hour < 8:
                await asyncio.sleep(0.1)
                continue
            
            for _, method_return in result.items():
                if not method_return:
                    continue
                if isinstance(method_return, dict):
                    channel = method_return['channel']
                    message = method_return['result']
                    channel = self.get_channel(channel)
                    if message:
                        await channel.send(message)
                else:
                    channel = self.get_channel(self.default_autochannel)
                    await channel.send(method_return)
            await asyncio.sleep(0.1)

    @property
    def default_autochannel(self):
        return self._default_autochannel

    @default_autochannel.setter
    def default_autochannel(self, value):
        self._default_autochannel = value
   

def load_environment(env_var_strings: list) -> dict:
    """
    Return a dictionary comprehended with values for
    environment variables used to authenticate various
    interfaces throughout the bot application, loaded
    from an .env file by the use of load_dotenv().

    :param env_var_strings: 
        list with all keys to populate with value, the 
        same as in the ones in the .env file
    """
    load_dotenv()
    var_dict = {}

    for var in env_var_strings:
        var_dict[var] = os.getenv(var)

    return var_dict

if __name__ == '__main__':

    enviromnent_strings = [
        'DISCORD_GUILD',
        'TIMEEDIT_URL',
        'LUNCH_MENU_URL',
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
        'REDDIT_USER_AGENT',
        'GOOGLE_API_KEY',
        'GOOGLE_CSE_ID',
        'DISCORD_TOKEN',
        'CORONA_API_URI',
        'CORONA_API_RAPIDAPI_HOST',
        'CORONA_API_RAPIDAPI_KEY'
    ]

    CommandIntegrator_settings_file = Path('CommandIntegrator') / 'commandintegrator.settings.json'
    corona_translation_file = 'country_eng_swe_translations.json'

    with open(CommandIntegrator_settings_file, 'r', encoding = 'utf-8') as f:
        default_responses = json.loads(f.read())['default_responses']

    environment_vars = load_environment(enviromnent_strings)
    
    

    #  --- Instantiate the key backend objects used and the discord client ---

    helpqueue_ft = HelpQueueFeature()
    ranking_ft = RankingMembersFeature()
    lunchmenu_ft = LunchMenuFeature(url = environment_vars['LUNCH_MENU_URL'])
    schedule_ft = ScheduleFeature(url = environment_vars['TIMEEDIT_URL'])
    corona_ft = CoronaSpreadFeature(
                    CORONA_API_URI = environment_vars['CORONA_API_URI'],
                    CORONA_API_RAPIDAPI_HOST = environment_vars['CORONA_API_RAPIDAPI_HOST'],
                    CORONA_API_RAPIDAPI_KEY = environment_vars['CORONA_API_RAPIDAPI_KEY'],
                    translation_file_path = corona_translation_file)

    redditjoke_ft = RedditJokeFeature(
                        client_id = environment_vars['REDDIT_CLIENT_ID'], 
                        client_secret = environment_vars['REDDIT_CLIENT_SECRET'],
                        user_agent = environment_vars['REDDIT_USER_AGENT'])

    processor = CommandProcessor(
        pronoun_lookup_table = PronounLookupTable(), 
        default_responses = default_responses)
    
    processor.features = (
        lunchmenu_ft, 
        schedule_ft, 
        corona_ft, 
        redditjoke_ft, 
        ranking_ft,
        helpqueue_ft
    )
    
    client = RobBotClient(**environment_vars)
    client.default_autochannel = 'DISCORD_CHANNEL_HERE'
    

    """
    Add scheduled methods here. If your method needs parameters, 
    simply add them after the name of the method. here's an example:
    
    <<< client.scheduler.every(1).minute.do(add_integers, a = 10, b = 5) >>>
    """
    @dataclass
    class message_mock:
        content: list

    pollcache = PollCache(silent_first_call = True)

    client.scheduler.every().day.at('08:30').do(
        schedule_ft.get_todays_lessons, return_if_none = False, channel = client.default_autochannel
    )

    client.scheduler.every().sunday.at('15:00').do(
        schedule_ft.get_curriculum, return_if_none = False, channel = client.default_autochannel
    )
    
    client.scheduler.every(20).to(24).hours.do(
        redditjoke_ft.get_random_joke, channel = client.default_autochannel
    ) 

    swe_cases_request = message_mock
    swe_cases_request.content = 'hur många har smittats i sverige'.split(' ')

    swe_recoveries_request = message_mock
    swe_recoveries_request.content = 'hur många har tillfrisknat i sverige'.split(' ')

    swe_deaths_request = message_mock
    swe_deaths_request.content = 'hur många har omkommit i sverige'.split(' ')
    
    client.scheduler.every(1).minutes.do(
        pollcache, func = corona_ft.get_cases_by_country, message = swe_cases_request,
        channel = 'DISCORD_CHANNEL_HERE'
    )

    client.scheduler.every(1).minutes.do(
        pollcache, func = corona_ft.get_recoveries_by_country, message = swe_recoveries_request,
        channel = 'DISCORD_CHANNEL_HERE'
    )

    client.scheduler.every(1).minutes.do(
        pollcache, func = corona_ft.get_deaths_by_country, message = swe_deaths_request,
        channel = 'DISCORD_CHANNEL_HERE'
    )

    # --- Turn the key and start the bot ---
    client.run(environment_vars['DISCORD_TOKEN'])
