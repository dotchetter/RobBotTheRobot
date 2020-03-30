import discord
import CommandIntegrator as ci
from CommandIntegrator.enumerators import CommandPronoun
from timeeditschedule import Schedule
from CommandIntegrator.logger import logger
from datetime import datetime

class ScheduleFeatureCommandParser(ci.FeatureCommandParserBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ScheduleFeature(ci.FeatureBase):

    FEATURE_KEYWORDS = (
        'schema', 'schemat',
        'lektion', 'klassrum',
        'sal', 'lektioner',
        'lektion'
    )
    
    def __init__(self, *args, **kwargs):
        self.command_parser = ScheduleFeatureCommandParser()
        self.command_parser.keywords = ScheduleFeature.FEATURE_KEYWORDS
        self.command_parser.callbacks = {
            'nästa': lambda: self.get_next_lesson(),
            'klassrum': lambda: self.get_next_lesson(),
            'idag': lambda: self.get_todays_lessons(),
            'imorgon': lambda: self.get_curriculum(),
            'imorn': lambda: self.get_curriculum(),
            'imorrn': lambda: self.get_curriculum(),
            'schema': lambda: self.get_curriculum(),
            'schemat': lambda: self.get_curriculum() 
        }

        self.mapped_pronouns = (
            CommandPronoun.INTERROGATIVE,
        )

        super().__init__(
            command_parser = self.command_parser,
            interface = Schedule(**kwargs)
        )

    @logger
    @ci.scheduledmethod
    def get_curriculum(self, return_if_none = True) -> str:
        """
        Return string with the schedule for as long as forseeable
        with Schedule object. Take in to acount the 2000 character
        message limit in Discord. Append only until the length
        of the total string length of all elements combined are within
        0 - 2000 in length.
        
        :param return_if_none:
            boolean for declaring interest in getting output from the
            method if no data is present or not. Not desired when simpy
            checking programatically, but may be desired when a user asks
            for a call of this method and a string should reutrn to the UI.
        """
        curriculum = []
        last_date = self.interface.curriculum[0].begin.date()
        allowed_length = 2000
        today = datetime.now().date()
        weekdays = {0: 'Måndag', 1: 'Tisdag', 2: 'Onsdag', 3: 'Torsdag', 4: 'Fredag'}
        
        for event in (self.interface.curriculum):
            if event.begin.date() >= self.interface.today:
                begin = event.begin.adjusted_time.strftime('%H:%M')
                end = event.end.adjusted_time.strftime('%H:%M')
                location = event.location
                name = event.name
                date = event.begin.date()
                date_header = f'**{weekdays[date.weekday()]} {date}**\n'
                class_header = f'{name} i {location}, kl. {begin} - {end}'
                
                if date != last_date:
                    phrase = f'\n{date_header}{class_header}'
                else:
                    phrase = f'{class_header}'
                
                if (allowed_length - len(phrase)) > 10 and (date - today).days <= 7:
                    curriculum.append(phrase)
                    allowed_length -= len(phrase)
                    last_date = event.begin.date()
                else:
                    break
        
        if curriculum:
            curriculum = '\n'.join(curriculum)        
            return f'Här är schemat 7 veckodagar framåt ' \
                   f':slight_smile:\n{curriculum}'

        elif not curriculum and not return_if_none:
            return 'Just nu ser det tomt ut på schemat...'

    @logger
    @ci.scheduledmethod
    def get_todays_lessons(self, return_if_none = True) -> str:
        """
        Return concatenated response phrase with all lessons for 
        the current date. If none, return a message that explains
        no lessons for current date.
        
        :param return_if_none:
            boolean for declaring interest in getting output from the
            method if no data is present or not. Not desired when simpy
            checking programatically, but may be desired when a user asks
            for a call of this method and a string should reutrn to the UI.
        """
        if self.interface.todays_lessons:
            lessons = '\n'.join(self.interface.todays_lessons)
            return f'Schemat för dagen:\n{lessons}'
        
        if return_if_none:
            return 'Det finns inga lektioner på schemat idag :sunglasses:'

    @logger
    def get_next_lesson(self) -> str:
        """
        Return string with concatenated variable values to tell the
        human which is the next upcoming lesson.
        """
        try:
            date = self.interface.next_lesson_date
            hour = self.interface.next_lesson_time
            classroom = self.interface.next_lesson_classroom
        except Exception as e:
            return e
        return f'Nästa lektion är i {classroom}, {date}, kl {hour} :slight_smile:'