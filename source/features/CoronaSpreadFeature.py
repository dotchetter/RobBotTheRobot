import discord
import CommandIntegrator as ci
import fake_useragent
import coronafeatureclient as coronafeatureclient
from CommandIntegrator.enumerators import CommandPronoun
from CommandIntegrator.logger import logger


class CoronaSpreadFeatureCommandParser(ci.FeatureCommandParserBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class CoronaSpreadFeature(ci.FeatureBase):

    FEATURE_KEYWORDS = (
        'land',
        'totalt',
        'många',
        'corona',
        'coronafall'
    )

    def __init__(self, *args, **kwargs):
        
        data_timestamp_1 = {'när': ('uppdaterad', 'uppdaterades', 'statistik', 'statistiken')}
        data_timestamp_2 = {'hur': ('gammal', 'data', 'datan')}

        total_deaths = {'totalt': ('dött', 'omkommit', 'döda')}
        total_recoveries = {'totalt': ('friska', 'tillfrisknat', 'återhämtat')}
        total_cases = {'totalt': ('smittade', 'smittats', 'sjuka')}

        most_deaths = {'flest': ('döda', 'dödsfall', 'omkommit', 'omkomna', 'dött')}
        most_recoveries = {'flest': ('friska', 'tillfrisknat')}
        most_cases = {'flest': ('smittade', 'sjuka')}

        least_deaths = {'minst': ('döda', 'dödsfall', 'omkomna', 'omkommit', 'dött')}
        least_recoveries = {'minst': ('friska', 'tillfrisknat', 'återhämtat')}
        least_cases = {'minst': ('smittade', 'smittats', 'sjuka')}

        infections_by_query_1 = {'har': ('smittats', 'sjuka')}
        infections_by_query_2 = {'är': ('smittade', 'sjuka')}
        
        deaths_by_query_1 = {'hur': ('dött', 'omkommit', 'döda')}
        deaths_by_query_2 = {'har': ('dött', 'omkommit', 'döda')}
        
        recoveries_by_query = {'har': ('friska', 'tillfrisknat')}
        new_cases_by_query = {'hur': ('nya', 'nytt', 'fall')}    

        self.command_parser = CoronaSpreadFeatureCommandParser()
        self.command_parser.keywords = CoronaSpreadFeature.FEATURE_KEYWORDS
        self.command_parser.interactive_methods = (
            self.get_cases_by_country,
            self.get_recoveries_by_country,
            self.get_deaths_by_country,
            self.get_new_cases_by_country
        )
        
        self.command_parser.callbacks = {
            str(data_timestamp_1): lambda: self.interface.get_data_timestamp(),
            str(data_timestamp_2): lambda: self.interface.get_data_timestamp(),
            str(total_deaths): lambda: self.get_total_deaths(),
            str(total_recoveries): lambda: self.get_total_recoveries(),
            str(total_cases): lambda: self.get_total_infections(),
            str(most_deaths): lambda: self.get_most_deaths(),
            str(most_recoveries): lambda: self.get_most_recoveries(),
            str(most_cases): lambda: self.get_most_infections(),
            str(least_cases): lambda: self.get_least_infections(),
            str(least_deaths): lambda: self.get_least_deaths(),
            str(least_recoveries): lambda: self.get_least_recoveries(),
            str(infections_by_query_1): self.get_cases_by_country,
            str(infections_by_query_2): self.get_cases_by_country,
            str(deaths_by_query_1): self.get_deaths_by_country,
            str(deaths_by_query_2): self.get_deaths_by_country,
            str(recoveries_by_query): self.get_recoveries_by_country,
            str(new_cases_by_query): self.get_new_cases_by_country,
            'smittade': self.get_cases_by_country,
            'sjuka': self.get_cases_by_country,
            'dött': self.get_deaths_by_country,
            'döda': self.get_deaths_by_country,
            'friska': self.get_recoveries_by_country,
            'tillfrisknat': self.get_recoveries_by_country,
            'tillfrisknade': self.get_recoveries_by_country
        }

        self.translation_file_path = kwargs['translation_file_path']
        self.mapped_pronouns = (CommandPronoun.INTERROGATIVE,)

        api_handle = coronafeatureclient.ApiHandle(uri = kwargs['CORONA_API_URI'], standby_hours = 1)
        api_handle.add_header('x-rapidapi-host', kwargs['CORONA_API_RAPIDAPI_HOST'])
        api_handle.add_header('x-rapidapi-key', kwargs['CORONA_API_RAPIDAPI_KEY'])

        super().__init__(
            command_parser = self.command_parser,
            interface = coronafeatureclient.Client(api_handle, self.translation_file_path)
        )

    @logger
    @ci.scheduledmethod
    def get_total_deaths(self):
        response = self.interface.get_total_deaths()
        return f'Totalt har {response} omkommit globalt'
    
    @logger
    @ci.scheduledmethod
    def get_total_recoveries(self):
        response = self.interface.get_total_recoveries()
        return f'Totalt har {response} tillfrisknat globalt'
    
    @logger
    @ci.scheduledmethod
    def get_total_infections(self):
        response = self.interface.get_total_infections()
        return f'Totalt har {response} insjuknat globalt'
    
    @logger
    def get_most_deaths(self):
        response = self.interface.get_deaths()
        return f'Flest har omkommit i {response}'
    
    @logger
    def get_most_recoveries(self):
        response = self.interface.get_recoveries()
        return f'Flest har tillfrisknat i {response}'
    
    @logger
    def get_most_infections(self):
        response = self.interface.get_infections()
        return f'Flest har smittats i {response}'
    
    @logger
    def get_least_infections(self):
        response = self.interface.get_infections(sort_by_highest = False)
        return f'Minst antal insjuknade har {response}'
    
    @logger
    def get_least_deaths(self):
        response = self.interface.get_deaths(sort_by_highest = False)
        return f'Minst antal dödsfall har {response}'
   
    @logger
    def get_least_recoveries(self):
        response = self.interface.get_recoveries(sort_by_highest = False)
        return f'Minst tillfrisknade: {response}'

    @logger
    @ci.scheduledmethod
    def get_new_cases_by_country(self, message: discord.Message) -> str:
        """
        Get new cases by country. New cases are defined by API.
        :param message:
            original message from Discord
        :returns:
            str
        """
        try:
            country = message.content[-1].strip(ci.FeatureCommandParserBase.IGNORED_CHARS)
            response = self.interface.get_by_query(query = 'new_cases', country_name = country)
            
            if int(response.replace(',','').strip()) > 1: 
                new = 'nya'
            else:
                new = 'nytt'

            return f' {response} {new} fall av corona i {country.capitalize()}'
        except Exception as e:
            pass

    @logger
    @ci.scheduledmethod
    def get_cases_by_country(self, message: discord.Message) -> str:
        """
        Get cases by country.
        :param message:
            original message from Discord
        :returns:
            str
        """
        try:
            country = message.content[-1].strip(ci.FeatureCommandParserBase.IGNORED_CHARS)
            response = self.interface.get_by_query(query = 'cases', country_name = country)
        except:
            try:
                country = str().join(message.content).strip(ci.FeatureCommandParserBase.IGNORED_CHARS)
                response = self.interface.get_by_query(query = 'cases', country_name = country)
            except:
                return f'Jag förstod inte.. landet du frågar om behöver vara sist i din mening.'
        else:
            return f'Totalt {response} har smittats av corona i {country.capitalize()}'
            


    @logger
    @ci.scheduledmethod
    def get_recoveries_by_country(self, message: discord.Message) -> str:
        """
        Get recoveries by country.
        :param message:
            original message from Discord
        :returns:
            str
        """
        try:
            country = message.content[-1].strip(ci.FeatureCommandParserBase.IGNORED_CHARS)
            response = self.interface.get_by_query(query = 'total_recovered', country_name = country)
        except:
            try:
                country = str().join(message.content).strip(ci.FeatureCommandParserBase.IGNORED_CHARS)
                response = self.interface.get_by_query(query = 'total_recovered', country_name = country)
            except:
                return f'Jag förstod inte.. landet du frågar om behöver vara sist i din mening.'
        else:
            return f'Totalt {response} har tillfrisknat i corona i {country.capitalize()}'
            

    @logger
    @ci.scheduledmethod
    def get_deaths_by_country(self, message: discord.Message) -> str:
        """
        Get deaths by country.
        :param message:
            original message from Discord
        :returns:
            str
        """
        try:
            country = message.content[-1].strip(ci.FeatureCommandParserBase.IGNORED_CHARS)
            response = self.interface.get_by_query(query = 'deaths', country_name = country)
        except:
            try:
                country = str().join(message.content).strip(ci.FeatureCommandParserBase.IGNORED_CHARS)
                response = self.interface.get_by_query(query = 'deaths', country_name = country)
            except:
                return f'Jag förstod inte.. landet du frågar om behöver vara sist i din mening.'
        else:
            return f'Totalt {response} har omkommit i corona i {country.capitalize()}'
            