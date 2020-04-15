import discord
import os
import json
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

        self.rank_data = dict()
        self.rank_data['userid_rank'] = dict()
        self.rank_data['opted_out_members'] = list()
        self.mapped_pronouns = (CommandPronoun.UNIDENTIFIED,)
        super().__init__(command_parser = self.command_parser)
        self._read_from_file()


    @logger
    def _read_from_file(self) -> None:
        """
        Read ranks from file. If not present, an 
        empty file will be created. If file is 
        empty, the empty structure is written.
        """
        try:
            with open('ranking_data.json', 'r') as f:
                self.rank_data = json.loads(f.read())
        except Exception:
            pass
            
    @logger
    def _write_to_file(self, obj) -> None:
        """
        Write structure in parameter to file.
        :param obj:
            structure to serialize and write to file
        :returns:
            None
        """
        with open('ranking_data.json', 'w') as f:
            json.dump(obj, f)

    @logger
    def rank_up(self, message: discord.Message) -> str:
        """
        Rank up a user upon command
        """
        output = []
        for member in message.mentions:
            try:
                mention_id = member.mention
                if message.author == member:
                    continue
                elif mention_id in self.rank_data['opted_out_members']:
                    return 'Denna medlem har valt att gå ur ranking funktionen'
                self.rank_data['userid_rank'][member.mention] += 1
            except KeyError:
                self.rank_data['userid_rank'][member.mention] = 1
            _new_rank = self.rank_data['userid_rank'][mention_id]
            _out_str = f':small_red_triangle: {member.mention} ökade till {_new_rank}'
            output.append(_out_str)
        if len(output):
            return f'{os.linesep.join(output)}'

    @logger
    def rank_down(self, message: discord.Message) -> str:
        """
        Rank down a user upon command
        """
        output = []
        for member in message.mentions:
            mention_id = member.mention
            try:
                if message.author == member:
                    continue
                elif mention_id in self.rank_data['opted_out_members']:
                    return 'Denna medlem har valt att gå ur ranking funktionen'
                self.rank_data['userid_rank'][mention_id] -= 1
            except KeyError:
                self.rank_data['userid_rank'][mention_id] = -1
            _new_rank = self.rank_data['userid_rank'][mention_id]
            _out_str = f':small_red_triangle_down: {member.mention} minskade till {_new_rank}'
            output.append(_out_str)
        if len(output):
            return f'{os.linesep.join(output)}'

    @logger
    def rank_for_member(self, message: discord.Message) -> str:
        """
        Return the current rank for a member
        """
        output = []
        for member in message.mentions:
            mention_id = member.mention
            try:
                rank = self.rank_data['userid_rank'][mention_id]
                output.append(f'{mention_id} rankar {rank}')
            except KeyError:
                output.append(f'{mention_id} har inte rankats')
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
        ranks = self.rank_data['userid_rank']
        sorted_by_rank = sorted(ranks, key = lambda i: ranks[i], reverse = True)
        
        if len(ranks) < 4:
            for place, member in enumerate(sorted_by_rank):
                output.append(f':star: **{member}**:    **{ranks[member]}**')
        else:
            for place, member in enumerate(sorted_by_rank):
                if place == 0:
                    output.append('** H  I  G  H          S  C  O  R  E **')  
                    output.append(':small_orange_diamond:' * 8)
                if (place + 1) < 4:
                    place_emoji = emojis[place + 1]
                else:
                    if not inserted_separator:
                        output.append(':small_orange_diamond:' * 8)
                        output.append(os.linesep)
                        inserted_separator = True
                    place_emoji = ':star:'
                output.append(f'{place_emoji} **{member}**:    **{ranks[member]}**')

        self._write_to_file(self.rank_data)
        return f'{os.linesep.join(output)}'

    @logger
    def opt_out(self, message: discord.Message) -> str:
        """
        Disable the ranking feature for whoever wrote the
        opt out command (message author)
        """
        self.rank_data['opted_out_members'].append(message.author.mention)
        try:
            self.rank_data['userid_rank'].pop(message.author.mention)
        except:
            pass
        self._write_to_file(self.rank_data)
        return f'Ranking för {message.author.mention} har spärrats'

    @logger
    def opt_in(self, message: discord.Message) -> str:
        """
        Re-enable the ranking feature for whoever wrote the
        opt out command (message author)
        """
        self.rank_data['opted_out_members'].remove(message.author.mention)
        self._write_to_file(self.rank_data)
        return f'Ranking för {message.author.mention} har återaktiverats'