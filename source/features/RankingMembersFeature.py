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
		
		self.command_parser = RankingMembersFeatureCommandParser()
		self.command_parser.keywords = RankingMembersFeature.FEATURE_KEYWORDS,
		self.command_parser.callbacks  = {
			str(rank_up): self.rank_up,
			str(rank_down): self.rank_down,
			str(rank_for_all): lambda: self.rank_for_all(),
			'för': self.rank_for_member,
			'for': self.rank_for_member
		}
		
		self.command_parser.interactive_methods = (
			self.rank_up,
			self.rank_down,
			self.rank_for_member
		)

		self.user_rankings = {}
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
				self.user_rankings[member] += 1
			except KeyError:
				self.user_rankings[member] = 1
			output.append(f'{member.mention} ökade till {self.user_rankings[member]}')
		return f'{os.linesep.join(output)}'

	@logger
	def rank_down(self, message: discord.Message) -> str:
		"""
		Rank down a user upon command
		"""
		output = []
		for member in message.mentions:
			try:
				self.user_rankings[member] -= 1
			except KeyError:
				self.user_rankings[member] = -1
			output.append(f'{member.mention} minskade till {self.user_rankings[member]}')
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
	def rank_for_all(self):
		"""
		Return ranks for all members in a list
		"""
		output = []
		for member in self.user_rankings:
			output.append(f'{member.mention} rankar {self.user_rankings[member]}')
		return f'{os.linesep.join(output)}'