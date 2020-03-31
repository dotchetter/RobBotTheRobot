import os
import discord
import CommandIntegrator as ci
from CommandIntegrator.enumerators import CommandPronoun
from CommandIntegrator.logger import logger
from scraper import Scraper
from datetime import datetime, timedelta


class LunchMenuFeatureCommandParser(ci.FeatureCommandParserBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
class LunchMenuFeature(ci.FeatureBase):

    FEATURE_KEYWORDS = (
        'lunch', 'mat',
        'käk', 'krubb',
        'föda', 'tugg',
        'matsedel', 'meny'
    )

    def __init__(self, **kwargs):
        
        self.command_parser = LunchMenuFeatureCommandParser()
        self.command_parser.keywords = LunchMenuFeature.FEATURE_KEYWORDS
        self.command_parser.callbacks = {
            'igår': lambda: self.menu_for_weekday_phrase(weekday = datetime.now() - timedelta(days = 1), when = 'igår'),
            'idag': lambda: self.menu_for_weekday_phrase(weekday = datetime.now(), when = 'idag'),
            'imorn': lambda: self.menu_for_weekday_phrase(weekday = datetime.now() + timedelta(days = 1), when = 'imorgon'),
            'imorgon': lambda: self.menu_for_weekday_phrase(weekday = datetime.now() + timedelta(days = 1), when = 'imorgon'),
            'imorron': lambda: self.menu_for_weekday_phrase(weekday = datetime.now() + timedelta(days = 1), when = 'imorgon'),
            'imorrn': lambda: self.menu_for_weekday_phrase(weekday = datetime.now() + timedelta(days = 1), when = 'imorgon'),
            'övermorgon': lambda: self.menu_for_weekday_phrase(weekday = datetime.now() + timedelta(days = 2), when = 'i övermorgon'),
            'övermorn': lambda: self.menu_for_weekday_phrase(weekday = datetime.now() + timedelta(days = 2), when = 'i övermorgon'),
            'övermorrn': lambda: self.menu_for_weekday_phrase(weekday = datetime.now() + timedelta(days = 2), when = 'i övermorgon'),
            'vecka': lambda: self.menu_for_week(),
            'veckan': lambda: self.menu_for_week(),
            'veckans': lambda: self.menu_for_week()
        }

        self.mapped_pronouns = (
            CommandPronoun.INTERROGATIVE,
        )        

        super().__init__(
            interface = Scraper(url = kwargs['url']),
            command_parser = self.command_parser
        )

    @logger
    def menu_for_week(self) -> str:
        """
        Return the entire week's menu with one empty line
        separating the lists of entries.
        """
        days = ('**Måndag**', '**Tisdag**', '**Onsdag**', '**Torsdag**', '**Fredag**')
        menu_for_week = self.interface.get_menu_for_week()
        output = str()
        
        for index, day in enumerate(menu_for_week):
            day.insert(0, days[index])
            if not len(day):
                day.append('Meny inte tillgänglig.')
            day.append(os.linesep)
        
        for day in menu_for_week:
            output += os.linesep.join(day)

        return f'Här är veckans meny :slight_smile:{os.linesep}{os.linesep}{output}'
    
    @logger
    def menu_for_weekday_phrase(self, weekday: datetime, when: str) -> str:
        """
        Return a user-friendly variant of the content
        retreived by the interface object's methods,
        for display on front end. The method .purge_cache
        will be called if the menu object is 5 days or older
        upon query, to prevent displaying old data from previous
        week.
        :param weekday:
            datetime for the day that the query concerns
        :when:
            string for matching tempus agains
        :returns:
            string
        """
        if self.interface.cache and (datetime.now().date() - self.interface.cache.creation_date).days >= 5:
            self.interface.purge_cache()

        if when == 'igår':
            tense = 'ades'
        else:
            tense = 'as'

        menu = self.interface.get_menu_for_weekday(weekday.weekday())
        if menu is None:
            return f'Jag ser inget på menyn för {tempus[when]}.'
        return f'Detta server{tense} {tempus[when]}!{os.linesep}{os.linesep}{os.linesep.join(menu)}'