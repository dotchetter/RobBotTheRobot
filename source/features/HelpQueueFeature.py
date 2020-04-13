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
			self.get_next_in_queue
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
		return f'{message.author.mention} har plats {self.help_queue.qsize()}'
		
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
				member = self.help_queue.get()
				remaining = self._get_remaining()
				msg = f'Näst på kö är {member.mention}. {remaining}'
				return msg
		except AttributeError:
			return f'Du kan bara utöva detta kommando i en av kanalerna, inte i PM.'
		return f'{message.author.mention}, du saknar behörighet för detta'

	@logger
	def _get_remaining(self) -> str:
		"""
		Returns a phrase to indicate the size of the queue.
		:returns: 
			str
		"""
		if self.help_queue.qsize():
			if self.help_queue.qsize() > 1:
				amt = 'personer'
			else:
				amt = 'person'
			return f'Det finns {self.help_queue.qsize()} {amt} på hjälplistan'
		return 'Hjälplistan är tom'

	@logger
	def get_next_in_queue(self):
		"""
		Returns the member next in queue without popping.
		:returns:
			str
		"""
		if self.help_queue.qsize():
			return f'Näst på kö är {self.help_queue.queue[0].mention}' 
		return 'Hjälplistan är tom'

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
			output.append(f'Plats **{place + 1}**: {member.mention}')
		return f'{os.linesep.join(output)}'