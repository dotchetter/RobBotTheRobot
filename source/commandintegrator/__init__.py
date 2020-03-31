import pytz
import random
import json
import discord
import traceback
import sys
from .logger import logger
from .enumerators import CommandPronoun
from ast import literal_eval
from pprint import pprint
from os import system
from datetime import datetime, timedelta, time
from enum import Enum, auto
from dataclasses import dataclass
from abc import ABC, abstractmethod
from timeit import default_timer as timer

VERSION = '1.2.3'

"""
Details:
    2020-03-31
    
    CommandIntegrator framework source file

Module details:
    
    This file contains abstract and base classes for 
    the framework called CommandIntegrator. 

    In order for a developer to integrate their software
    with a way to bind certain actions and methods in their
    code, the developer needs a way to follow a set of routines
    that guarantees a seamless integration with the front end
    of the application. This framework provides base classes
    to inherit from with a strict set of rules and methods
    already provided to make it easier for the application 
    to scale, as well as letting developers easily integrate
    their software to the front end with their own interfaces.

    To read instructions and see examples how to use this 
    framework with your application - please read the full
    documentation which can be found in the wiki on GitHub
"""

@dataclass
class _cim:
    """
    This class is only used as a namespace
    for internal messages used by exceptions
    or elsewhere by CommandIntegrator classes
    and functions. Not for instantiating.
    """
    warn: str = "CommandIntegrator WARNING"
    err: str = "CommandIntegrator ERROR"

def is_dst(dt: datetime = datetime.now(), timezone: str = "Europe/Stockholm"):
    """
    Method for returning a bool whether or not a timezone
    currently is in daylight savings time, useful for servers
    that run systems outside of the user timezone.
    :param dt:
        datetime object, default is .now()
    :param timezone:
        string, timezone to give pytz for the dst query.
        look up available timezones at this url:
        https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones
    :returns:
        bool
    """
    timezone = pytz.timezone(timezone)
    timezone_aware_date = timezone.localize(dt, is_dst = None)
    return timezone_aware_date.tzinfo._dst.seconds != 0


def scheduledmethod(func):
    """
    Scheduled method decorator. In certain applications
    the ability to automatically call functions by the
    means of a schedule in some manner, for example with
    a schedule.Scheduler() instance object, it can be 
    desired to direct messages to different channels in 
    the front end application such as a Discord or Slack
    server. If, however the method is called as per usual,
    the bahavior is not altered. Add this decorator above
    a method in your stack, and then add the parameter 
    'channel' when you call it through the scheduler routine.

    The returned value from this will be a dictionary where
    the function output is under the 'result' key, and the
    channel is under the 'channel' key, as seen below.
    """
    def _inner(*args, **kwargs):
        try:
            channel = kwargs['channel']
        except KeyError:
            return func(*args, **kwargs)
        else:
            kwargs.pop('channel')
            return {
                'result': func(*args, **kwargs), 
                'channel': channel
            }
    return _inner
    


class PollCache:
    """
    This object is designed to act as a cushion between a 
    function or other callable, and its caller, and only 
    give returns when new data from the function is identified.

    This way you can pass functions to an instance of this class
    and loop indefinitely, where only new results will be returned.

    The PollCache object will treat every function and its 
    constellation of arguments and keyword arguments as unique,
    meaning that you can use the same function or other callable
    with different parameters in a loop, and it will not be 
    overwritten in the PollCache just because the function is 
    the same, but will be treated as its own cache.

    This class uses the __call__ method as its main interface.
    Call the instance of this class as you would a function.

    The syntax is simply: 

    >>    cache = PollCache()
    >>    cache(function_name, parameter1 = val, parameter2 = val2, ...)


    :silent_first_call:
        Boolean. Set it to True if the desired behavior is to
        build up a cache, and only start returning values if 
        any of the cached method returns deviate.
        Default is that all initial calls with a new function
        or a past function with new arguments, will return 
        values. Suppress this with this parameter.
    
    ---- Example with default behavior--------------------------------------
    
    >>    cache = PollCache()
    >>    cache(function, a = 1, b = 2)   #  Will produce a return value
    >>    cache(function, a = 1, b = 2)   #  Will NOT produce a return value (identical output)
    >>    cache(function, a = 10, b = 20) #  Will produce a return value (new output)

    ----- Example with silent first call -----------------------------------
    
    >>    cache = PollCache(silent_first_call = True)
    >>    cache(function, a = 1, b = 2)   #  Will NOT produce a return value
    >>    cache(function, a = 1, b = 2)   #  Will NOT produce a return value (identical output)
    >>    cache(function, a = 10, b = 20) #  Will produce a return value (new output)
    """
    
    def __init__(self, silent_first_call = False):
        self.cached_polls = dict()
        self.silent_first_call = silent_first_call

    def __call__(self, func: 'function', *args, **kwargs):
        try:
            new_result = func(*args, **kwargs)
        except:
            raise

        if not func in self.cached_polls.keys():            
            self.cached_polls[func] = [
                {'args': args,
                 'kwargs': kwargs,
                 'result': new_result,
                 'calls': 1}]
            
            return new_result if not self.silent_first_call else None

        for call in self.cached_polls[func]:
            if call['args'] == args and call['kwargs'] == kwargs and call['result'] != new_result:
                call['result'] = new_result
                call['calls'] += 1
                return new_result
                
        if not [i for i in self.cached_polls[func] if i['args'] == args and i['kwargs'] == kwargs]:
            self.cached_polls[func].append({
                'args': args, 
                'kwargs': kwargs, 
                'result': new_result, 
                'calls': 1})
            
            return new_result if not self.silent_first_call else None


class PronounLookupTable:
    """
    Provide a grammatic framework that 
    returns a tuple of matches for certain
    grammatic classes of words found in a given
    sentence. 
    """

    def __init__(self):
        self._lookup_table = {
            CommandPronoun.INTERROGATIVE: (
                'vad', 'vem',
                'hur', 'varför',
                'vilken', 'vilket',
                'hurdan', 'hurudan',
                'undrar', 'när'),

            CommandPronoun.PERSONAL: (
                'jag', 'vi',
                'du', 'ni',
                'han', 'hon',
                'den', 'de',
                'dem'),

            CommandPronoun.POSSESSIVE: (
                'mitt', 'mina',
                'min', 'vårt',
                'vår', 'våra',
                'vårt', 'din',
                'ditt', 'dina',
                'ert', 'er',
                'era', 'sin',
                'sitt', 'sina')
        }

    def __repr__(self):
        return f'PronounLookupTable({self._lookup_table})'

    def lookup(self, message: list) -> tuple:
        """
        Split a given string by space if present, to iterate
        over a sentence of words. Returns a tuple with enum
        instances representing the pronouns that make up the
        composition of the string received. If none is found,
        a tuple with a single CommandPronoun.UNIDENTIFIED is 
        returned.
        """
        pronouns = []

        for word in message:
            for key in self._lookup_table:
                if word in self._lookup_table[key]:
                    pronouns.append(key)
            if '?' in word:
                pronouns.append(CommandPronoun.INTERROGATIVE)

        if len(pronouns):
            return tuple(sorted(set(pronouns)))
        return (CommandPronoun.UNIDENTIFIED,)


@dataclass
class Interpretation:
    """
    This object represents the output from the
    CommandProcessor class. 

    command_pronouns: A collection of pronouns
    identified in the message.

    feature_name: Name of the feature responsible
    and ultimately selected to provide a response.

    callback_binding: Name of the method that
    is bound to the subcategory for the feature.

    original_message: The original message in 
    a tuple, split by space.

    response: The callable object that was returned
    from the Feature.

    error: Any exception that was caught upon parsing
    the message. 
    """
    command_pronouns: tuple(CommandPronoun) = ()
    feature_name: str = None,
    callback_binding: str = None,
    original_message: tuple = ()
    response: callable = None
    error: Exception = None

    def __repr__(self):
        return str(self.__dict__)


class FeatureCommandParserABC(ABC):
    """
    Describe a data structure that binds certain
    keywords to a certain feature. As the feature
    stack grows, this class is used as a template
    for base classes that work with decomposing 
    a message string, trying to understand its context
    and intent.
    """
    IGNORED_CHARS = '?=)(/&%¤#"!,.-;:_^*`´><|'

    def __init__(self, *args, **kwargs):
        self.ignored_chars = dict()
        super().__init__()
        for key in kwargs:
            setattr(self, key, kwargs[key])

    @abstractmethod
    def __contains__(self, word: str) -> bool:
        return

    @abstractmethod
    def ignore_all(self, char: str):
        pass

    @abstractmethod
    def is_contender_for_processing(self, message: discord.Message) -> bool:
        return
    
    @abstractmethod
    def get_callback(self, message: discord.Message) -> 'function':
        return

    @property
    @abstractmethod
    def keywords(self) -> tuple:
        return
    
    @keywords.setter
    @abstractmethod
    def keywords(self, keywords: tuple):
        pass

    @property
    @abstractmethod
    def callbacks(self) -> dict:
        return

    @callbacks.setter
    @abstractmethod
    def callbacks(self, callbacks: dict):
        pass

    @property
    @abstractmethod
    def ignored_chars(self) -> dict:
        return

    @ignored_chars.setter
    @abstractmethod
    def ignored_chars(self, table: dict):
        pass

    @property
    @abstractmethod
    def interactive_methods(self) -> list:
        return
    
    @interactive_methods.setter
    @abstractmethod
    def interactive_methods(self):
        pass


class FeatureCommandParserBase(FeatureCommandParserABC):

    def __init__(self, *args, **kwargs):
        self.interactive_methods = tuple()
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f'FeatureCommandParser({self.callbacks})'

    def __contains__(self, word: str) -> bool:
        return word in self._keywords

    def ignore_all(self, char: str):
        self.ignored_chars[char] = ''

    def is_contender_for_processing(self, message: discord.Message) -> bool:
        """
        Iterate over the words in received message, and 
        see if any of the words line up with the keywords
        provided for an instance of this class. If a match
        is found, return True, else False.
        """
        for key in self.ignored_chars:
            message.content = [word.replace(key, self._ignored_chars[key]) for word in message.content]

        for word in message.content:
            if word.strip(FeatureCommandParserBase.IGNORED_CHARS) in self:
                return True
        return False
    
    def get_callback(self, message: discord.Message) -> 'function':
        """
        Returns the method (function object) bound to a 
        subcategory in the feature implementation. This method 
        should be overloaded if a different return behavior 
        in a no-match-found scenario is desired.
        """

        strip_chars = lambda string: string.strip(FeatureCommandParserBase.IGNORED_CHARS)
        complex_subcategories = []
        simple_subcategories = []
        
        for key in self._callbacks.keys():
            try:
                complex_subcategories.append(literal_eval(key))
            except:
                simple_subcategories.append(key)


        for subcategory in complex_subcategories:
            for word in message.content:
                word = strip_chars(word)
                try:
                    subset = subcategory[word]
                except KeyError:
                    pass
                else:
                    if [strip_chars(i) for i in message.content if strip_chars(i) in subset]:
                        return self._callbacks[str(subcategory)]
    
        for word in message.content:
            word = strip_chars(word)
            if word in simple_subcategories:
                return self._callbacks[word]
        return None

    @property
    def keywords(self) -> tuple:
        return self._keywords
    
    @keywords.setter
    def keywords(self, keywords: tuple):
        if not isinstance(keywords, tuple):
            raise TypeError(f'{_cim.warn} keywords must be tuple, got {type(keywords)}')
        for i in keywords:
            if not isinstance(i, str):
                raise TypeError(f'{_cim.warn} keyword "{i}" must be str, got {type(i)}')
        self._keywords = keywords

    @property
    def callbacks(self) -> dict:
        return self._callbacks
    
    @callbacks.setter
    def callbacks(self, callbacks: dict):
        if not isinstance(callbacks, dict):
            raise TypeError(f'{_cim.warn} callbacks must be dict, got {type(callbacks)}')
        self._callbacks = callbacks

    @property
    def ignored_chars(self) -> dict:
        return self._ignored_chars

    @ignored_chars.setter
    def ignored_chars(self, table: dict):
        if not isinstance(table, dict):
            raise TypeError(f'{_cim.warn} category must be dict, got {type(table)}')
        self._ignored_chars = table
    
    @property
    def interactive_methods(self) -> tuple:
        return self._interactive_methods
    
    @interactive_methods.setter
    def interactive_methods(self, arg: tuple):
        if not isinstance(arg, tuple):
            raise TypeError(f'{_cim.warn} interactive methods must be enclosed in tuple, got {type(arg)}')
        for i in arg:
            if not callable(i):
                raise TypeError(f'{_cim.warn} Warning: interactive method not callable: {i}')
        self._interactive_methods = arg
    

class FeatureABC(ABC):
    """ 
    Represent the template for a complete and 
    ready-to-use feature. 
    """
    def __init__(self, *args, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    @abstractmethod
    def __call__(self, message: list):
        pass

    @property
    def mapped_pronouns(self) -> tuple:
        return

    @mapped_pronouns.setter
    def mapped_pronouns(self, pronouns: tuple):
        pass
    
    @property
    @abstractmethod
    def interface(self) -> object:
        return
    
    @interface.setter
    @abstractmethod
    def interface(self, interface: object):
        pass

    @property
    @abstractmethod
    def command_parser(self) -> FeatureCommandParserBase:
        return

    @command_parser.setter
    @abstractmethod
    def command_parser(self, command_parser: FeatureCommandParserBase):
        pass


class FeatureBase(FeatureABC):
    """
    Base class for features coupled to the chatbot. 
    Use this class as a base class to inherit from when
    connecting your feature's interface to the bot.
    """

    def __init__(self, *args, **kwargs):
        self.interactive_methods = tuple()
        super().__init__(*args, **kwargs)

    def __call__(self, message: discord.Message) -> callable:
        try:
            feature_function = self._command_parser.get_callback(message)
            if feature_function is None:
                return None

            if feature_function in self._command_parser.interactive_methods:
                return lambda message = message: feature_function(message)
        except KeyError:
            raise NotImplementedError(f'{_cim.warn} no mapped function call for {feature_function} in self')

        return feature_function

    def __repr__(self):
        return f'Feature({__class__.__name__})'
    
    @property
    def mapped_pronouns(self) -> tuple:
        return self._mapped_pronouns

    @mapped_pronouns.setter
    def mapped_pronouns(self, pronouns: tuple = ()):
        if not isinstance(pronouns, tuple):
            raise TypeError(f'{_cim.warn} pronouns must be enclosed in a tuple, got {type(pronouns)}')
                
        self._mapped_pronouns = list(pronouns)
        self._mapped_pronouns.insert(0, CommandPronoun.UNIDENTIFIED)
        self._mapped_pronouns = tuple(self._mapped_pronouns)

    @property
    def interface(self) -> object:
        return self._interface
    
    @interface.setter
    def interface(self, interface: object):
        self._interface = interface

    @property
    def command_parser(self) -> FeatureCommandParserBase:
        return self._command_parser

    @command_parser.setter
    def command_parser(self, command_parser: FeatureCommandParserBase):
        if not isinstance(command_parser, FeatureCommandParserBase):
            raise TypeError(f'{_cim.warn} command_parser must inherit from FeatureCommandParserBase')
        self._command_parser = command_parser


class CommandProcessor:
    """
    This object, while integrated to a front end
    works as a way to parse and understand what a
    human is asking for. An object containing the 
    representation of the interpretation of said
    sentence or word is returned of class 
    Interpretation.
    """

    def __init__(self, pronoun_lookup_table: PronounLookupTable, default_responses: dict):
        self._pronoun_lookup_table = pronoun_lookup_table
        self._feature_pronoun_mapping = dict()
        self._default_responses = default_responses

    @property
    def features(self) -> tuple:
        return self._features
    
    @features.setter
    def features(self, features: tuple):
        if not isinstance(features, tuple):
            raise TypeError(f'{_cim.warn} expected tuple, got {type(features)}')
        
        for feature in features:
            self._feature_pronoun_mapping[feature] = feature.mapped_pronouns
        self._features = features

    @logger
    def process(self, message: discord.Message) -> Interpretation:
        """
        Part of the public interface. This method takes a discord.Message
        object  and splits the .content property on space characters
        turning it in to a list. The message is decomposed by the
        private _interpret method for identifying pronouns, which
        funnel the message to the appropriate features in the 
        self._features collection. As an instance of Interpretation
        is returned from this call, it is passed on to the caller.
        """
        message.content = message.content.lower().split(' ')
        try:
            return self._interpret(message)
        except Exception as e:
            sys.stderr.write(f'{_cim.err} Error occured in CommandProcessor _interpret function: {e}')
            return Interpretation(error = traceback.format_exc(),
                        response = lambda: f'CommandProcessor: Internal error, see logs.',
                        original_message = tuple(message.content))
   
    def _interpret(self, message: discord.Message) -> Interpretation:
        """
        Identify the pronouns in the given message. Try to 
        match the pronouns aganst the mapped pronouns property
        for each featrure. If multiple features match the set of
        pronouns, the message is given to each feature for keyword
        matching. The feature that returns a match is given the
        message for further processing and ultimately returning
        the response.
        """
        mapped_features = list()
        return_callable = None
        found_pronouns = self._pronoun_lookup_table.lookup(message.content)
        
        for feature in self._features:
            if bool(set(self._feature_pronoun_mapping[feature]).intersection(found_pronouns)):                
                if feature.command_parser.is_contender_for_processing(message): 
                    mapped_features.append(feature)

        if not mapped_features:
            return Interpretation(
                command_pronouns = found_pronouns,
                feature_name = None,
                original_message = tuple(message.content),
                response = lambda: random.choice(self._default_responses['NoResponse']))

        for feature in mapped_features:
            try:
                return_callable = feature(message)
            except NotImplementedError as e:
                return Interpretation(
                    command_pronouns = found_pronouns,
                    feature_name = feature.__class__.__name__,
                    callback_binding = None,
                    response = lambda: random.choice(self._default_responses['NoImplementation']),
                    original_message = tuple(message.content),
                    error = e)
            else:
                if return_callable is None:
                    continue
                return Interpretation(
                    command_pronouns = found_pronouns,
                    feature_name = feature.__class__.__name__,
                    callback_binding = None,
                    response = return_callable,
                    original_message = tuple(message.content))

        return Interpretation(command_pronouns = found_pronouns,
            feature_name = feature.__class__.__name__,
            callback_binding = None,
            response = lambda: random.choice(self._default_responses['NoSubCategory']),
            original_message = tuple(message.content))