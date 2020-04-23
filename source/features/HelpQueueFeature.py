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
        self.demonstration_queue = Queue()


        self.command_parser = HelpQueueFeatureCommandParser()
        self.command_parser.keywords = HelpQueueFeature.FEATURE_KEYWORDS
        
        self.mapped_pronouns = (
            CommandPronoun.INTERROGATIVE,
            CommandPronoun.UNIDENTIFIED
        )
        
        self.command_parser.callbacks = {
            str({'visa': ('kö', 'kön', 'hjälp')}): lambda: self.list_help_queue(),
            str({'visa': ('redovisning', 'redovisa')}): lambda: self.list_demonstration_queue(),
            str({'hjälp': ('mig',)}): self.enqueue,
            str({'help': ('mig', 'me')}): self.enqueue,
            str({'hjälp': ('nästa', 'next')}): self.dequeue,
            str({'jag': ('redovisa',)}): self.demonstrate_enqueue,
            str({'redovisa': ('nästa', 'next')}): self.demonstrate_dequeue,
            'hjälp': self.enqueue,
            'redovisa': self.demonstrate_enqueue
        }

        self.command_parser.interactive_methods = (
            self.enqueue,
            self.dequeue,
            self.demonstrate_enqueue,
            self.demonstrate_dequeue
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
    def list_help_queue(self) -> str:
        """
        Returns a concatenated string with all the members in 
        help queue, with their place in the queue as leading digit.
        """
        output = []
        if not self.help_queue.queue:
            return 'Hjälplistan är tom'
        for place, member in enumerate(self.help_queue.queue):
            output.append(f"‧ {place + 1}: `{member.name.strip('@')}`")
        return f'{os.linesep.join(output)}'

    @logger
    def list_demonstration_queue(self) -> str:
        """
        Returns a concatenated string with all the members in 
        demonstration queue, with their place in the queue as 
        leading digit.
        """
        output = []
        if not self.demonstration_queue.queue:
            return 'Listan för redovisningar är tom'
        for place, member in enumerate(self.demonstration_queue.queue):
            output.append(f"‧ {place + 1}: `{member.name.strip('@')}`")
        return f'{os.linesep.join(output)}'
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
            return ':warning: Hjälplistan är aktiv'
        self.latest_queue_state = self.help_queue.qsize()    @logger
    @logger
    def demonstrate_enqueue(self, message: discord.Message) -> str:
        """
        When this method is called, the author of any
        given parameter message is enqueued into the 
        demonstration queue, held separeate from the
        help queue structure.
        :param message:
            discord.Message object from chat
        :returns:
            str
        """
        for n, i in enumerate(self.demonstration_queue.queue):
            if i == message.author: 
                return f'{message.author.mention} du står redan i kön på plats {n + 1}'
        self.demonstration_queue.put(message.author)
        return f'{message.author.mention} skrevs upp. Du har plats {self.demonstration_queue.qsize()}'

    @logger
    def demonstrate_dequeue(self, message: discord.Message) -> str:
        """
        This method dequeues the next user in line
        for presenting their work to the teacher. 
        Dequeing is limited to members with the 
        "teacher" role only, this is checked first before
        dequeueing.
        :param message:
            discord.Message, the whole message object
            from the chat application
        """
        if not self.demonstration_queue.qsize():
            return 'Listan för presentationer är tom'

        try:
            if len([i for i in message.author.roles if i.name == 'teacher']):
                return f'Näst på kö för att presentera är {self.demonstration_queue.get().mention}'
        except AttributeError:
            return f'Du kan bara använda detta kommando i en av kanalerna, inte i PM'
        return f'{message.author.mention}, du saknar behörighet för detta'