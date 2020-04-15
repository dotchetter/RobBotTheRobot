import discord
import CommandIntegrator as ci
import os
from CommandIntegrator.enumerators import CommandPronoun
from CommandIntegrator.logger import logger
from queue import Queue

class HelpQueueFeatureCommandParser(ci.FeatureCommandParserBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class HelpQueueFeature(ci.FeatureBase):

    FEATURE_KEYWORDS = (
        'hjälp',
        'help',
        'visa'
    )

    def __init__(self, *args, **kwargs):
        self.help_queue = Queue()
        self.latest_queue_state = 0
        self.command_parser = HelpQueueFeatureCommandParser()
        self.command_parser.keywords = HelpQueueFeature.FEATURE_KEYWORDS
        
        self.mapped_pronouns = (
            CommandPronoun.INTERROGATIVE,
            CommandPronoun.UNIDENTIFIED
        )

        self.command_parser.callbacks = {
            'mig': self.enqueue,
            'next': self.dequeue,
            'nästa': self.dequeue,
            'kö': lambda: self.list_queue(),
            'kön': lambda: self.list_queue()
        }

        self.command_parser.interactive_methods = (
            self.enqueue,
            self.dequeue,
        )

        super().__init__(
            command_parser = self.command_parser
        )

    @logger
    def enqueue(self, message: discord.Message) -> str:
        """
        This method enqueues a user in the help queue.
        It will also respond with the position in the
        queue for the newly enqueued user.

        :param message:
            discord.Message, the whole message object
            from the chat application
        :returns:
            str, message with queue position
        """
        for n, i in enumerate(self.help_queue.queue):
            if i == message.author: 
                return f'{message.author.mention} du står redan i kön på plats {n + 1}'
        self.help_queue.put(message.author)
        return f'{message.author.mention} skrevs upp. Du har plats {self.help_queue.qsize()}'
        
    @logger
    def dequeue(self, message: discord.Message) -> str:
        """
        This method dequeues the next user in line
        for recieving help from the teacher. 
        Dequeing is limited to members with the 
        "teacher" role only, this is checked first before
        dequeueing.
        :param message:
            discord.Message, the whole message object
            from the chat application
        """
        if not self.help_queue.qsize():
            return 'Hjälplistan är tom'

        try:
            if len([i for i in message.author.roles if i.name == 'teacher']):
                return f'Näst på kö är {self.help_queue.get().mention}'
        except AttributeError:
            return f'Du kan bara använda detta kommando i en av kanalerna, inte i PM'
        return f'{message.author.mention}, du saknar behörighet för detta'

    @logger
    def list_queue(self) -> str:
        """
        Returns a concatenated string with all the members in 
        queue, with their place in the queue as leading digit.
        """
        output = []
        if not self.help_queue.queue:
            return 'Hjälplistan är tom'
        for place, member in enumerate(self.help_queue.queue):
            output.append(f"‧ {place + 1}: `{member.name.strip('@')}`")
        return f'{os.linesep.join(output)}'

    def queue_went_active(self) -> str:
        """
        This method returns a phrase if the queue size went
        from 0 to 1 in size since last call. It can be
        used to call it continuously and get the phrase back
        only when the queue has been emptied but then reactivated 
        by someone signing up for help.
        :returns:
            str
        """
        if self.latest_queue_state == 0 and self.help_queue.qsize() == 1:
            return 'Hjälplistan är aktiv'
        self.latest_queue_state = self.help_queue.qsize()