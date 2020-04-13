import discord
import os
import CommandIntegrator as ci
from CommandIntegrator.enumerators import CommandPronoun
from CommandIntegrator.logger import logger

class RankingMembersFeatureCommandParser(ci.FeatureCommandParserBase):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

class RankingMembersFeature(ci.FeatureBase):

	FEATURE_KEYWORDS = (
		'rank',
		'ranks'
	)

	def __init__(self, *args, **kwargs):
	
		rank_for_all = {'rank': ('alla', 'all')}
		rank_up = {'rank': ('upp', 'up')}
		rank_down = {'rank': ('ner', 'ned', 'down')}
		rank_opt_out = {'hoppa': ('ur', 'ut', 'out')}
		rank_opt_in = {'hoppa': ('in',)}
		
		self.command_parser = RankingMembersFeatureCommandParser()
		self.command_parser.keywords = RankingMembersFeature.FEATURE_KEYWORDS
		self.command_parser.callbacks  = {
			str(rank_up): self.rank_up,
			str(rank_down): self.rank_down,
			str(rank_for_all): lambda: self.rank_for_all(),
			str(rank_opt_out): self.opt_out,
			str(rank_opt_in): self.opt_in,
			'för': self.rank_for_member,
			'for': self.rank_for_member
		}
		
		self.command_parser.interactive_methods = (
			self.rank_up,
			self.rank_down,
			self.rank_for_member,
			self.opt_in,
			self.opt_out
		)

		self.user_rankings = dict()
		self.opted_out_members = list()
		self.mapped_pronouns = (CommandPronoun.UNIDENTIFIED,)
		super().__init__(command_parser = self.command_parser)

	@logger
	def rank_up(self, message: discord.Message) -> str:
		"""
		Rank up a user upon command
		"""
		output = []
		for member in message.mentions:
			try:
				if message.author == member:
					continue
				elif member in self.opted_out_members:
					return 'Denna medlem har valt att gå ur ranking funktionen'
				self.user_rankings[member] += 1
			except KeyError:
				self.user_rankings[member] = 1
			output.append(f'{member.mention} ökade till {self.user_rankings[member]}')
		if len(output):
			return f'{os.linesep.join(output)}'

	@logger
	def rank_down(self, message: discord.Message) -> str:
		"""
		Rank down a user upon command
		"""
		output = []
		for member in message.mentions:
			try:
				if message.author == member:
					continue
				elif member in self.opted_out_members:
					return 'Denna medlem har valt att gå ur ranking funktionen'
				self.user_rankings[member] -= 1
			except KeyError:
				self.user_rankings[member] = -1
			output.append(f'{member.mention} minskade till {self.user_rankings[member]}')
		if len(output): 
			return f'{os.linesep.join(output)}'

	@logger
	def rank_for_member(self, message: discord.Message) -> str:
		"""
		Return the current rank for a member
		"""
		output = []
		for member in message.mentions:
			try:
				output.append(f'{member.mention} rankar {self.user_rankings[member]}')
			except KeyError:
				output.append(f'{member.mention} har inte rankats')
		return f'{os.linesep.join(output)}'

	@logger
	def rank_for_all(self) -> str:
		"""
		Return ranks for all members in a list. The highscore
		are the top three, and they are displayed with different
		emojis from the others, as well as surrounded in a pattern
		of diamonds.
		"""
		output = []
		inserted_separator = False
		emojis = {1: ':first_place:', 2: ':second_place:', 3: ':third_place:'}
		
		for place, member in enumerate(sorted(self.user_rankings, key = lambda i: self.user_rankings[i], reverse = True)):
			if place == 0:
				output.append(':small_orange_diamond:' * 10)
				output.append('** H  I  G  H    S  C  O  R  E **')	
			if (place + 1) < 4:
				place_emoji = emojis[place + 1]
			else:
				if not inserted_separator:
					output.append(':small_orange_diamond:' * 10)
					output.append(os.linesep)
					inserted_separator = True
				place_emoji = ':star:'
			output.append(f'{place_emoji} **{member.name}**: **{self.user_rankings[member]}**')
		return f'{os.linesep.join(output)}'

	@logger
	def opt_out(self, message: discord.Message) -> str:
		"""
		Disable the ranking feature for whoever wrote the
		opt out command (message author)
		"""
		self.opted_out_members.append(message.author)
		try:
			self.user_rankings.pop(message.author)
		except:
			pass
		return f'Ranking för {message.author.mention} har spärrats'

	@logger
	def opt_in(self, message: discord.Message) -> str:
		"""
		Re-enable the ranking feature for whoever wrote the
		opt out command (message author)
		"""
		self.opted_out_members.remove(message.author)
		return f'Ranking för {message.author.mention} har återaktiverats'