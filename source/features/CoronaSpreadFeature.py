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
        'många',
        'corona',
        'coronafall'
    )

    data_timestamp_1 = {'när': ('uppdaterad', 'uppdaterades', 'statistik', 'statistiken')}
    data_timestamp_2 = {'hur': ('gammal', 'data', 'datan')}

    total_deaths = {'totalt': ('dött', 'omkommit', 'döda')}
    total_recoveries = {'totalt': ('friska', 'tillfrisknat', 'återhämtat')}
    total_cases = {'totalt': ('smittade', 'smittats', 'sjuka')}

    most_deaths = {'flest': ('döda', 'dödsfall', 'omkommit', 'omkomna', 'dött')}
    most_recoveries = {'flest': ('friska', 'tillfrisknat')}
    most_cases = {'flest': ('smittade', 'sjuka')}

    least_deaths = {'minst': ('döda', 'dödsfall', 'omkomna', 'omkommit', 'dött')}
    least_recoveries = {'minst': ('smittade', 'sjuka')}
    least_cases = {'minst': ('friska', 'tillfrisknat')}

    infections_by_query_1 = {'har': ('smittats', 'sjuka')}
    infections_by_query_2 = {'är': ('smittade', 'sjuka')}
    deaths_by_query = {'har': ('dött', 'omkommit')}
    recoveries_by_query = {'har': ('friska', 'tillfrisknat')}
    new_cases_by_query = {'hur': ('nya', 'nytt', 'fall')}    


    FEATURE_SUBCATEGORIES = {
        str(data_timestamp_1): CommandSubcategory.CORONA_DATA_TIMESTAMP,
        str(data_timestamp_2): CommandSubcategory.CORONA_DATA_TIMESTAMP,
        str(total_deaths): CommandSubcategory.CORONA_SPREAD_TOTAL_DEATHS,
        str(total_recoveries): CommandSubcategory.CORONA_SPREAD_TOTAL_RECOVERIES,
        str(total_cases): CommandSubcategory.CORONA_SPREAD_TOTAL_INFECTIONS,
        str(most_deaths): CommandSubcategory.CORONA_SPREAD_MOST_DEATHS,
        str(most_recoveries): CommandSubcategory.CORONA_SPREAD_MOST_RECOVERIES,
        str(most_cases): CommandSubcategory.CORONA_SPREAD_MOST_INFECTIONS,
        str(least_cases): CommandSubcategory.CORONA_SPREAD_LEAST_INFECTIONS,
        str(least_deaths): CommandSubcategory.CORONA_SPREAD_LEAST_DEATHS,
        str(least_recoveries): CommandSubcategory.CORONA_SPREAD_LEAST_RECOVERIES,
        str(infections_by_query_1): CommandSubcategory.CORONA_INFECTIONS_BY_QUERY,
        str(infections_by_query_2): CommandSubcategory.CORONA_INFECTIONS_BY_QUERY,
        str(deaths_by_query): CommandSubcategory.CORONA_DEATHS_BY_QUERY,
        str(recoveries_by_query): CommandSubcategory.CORONA_RECOVERIES_BY_QUERY,
        str(new_cases_by_query): CommandSubcategory.CORONA_NEW_CASES_BY_QUERY
    }

    def __init__(self, *args, **kwargs):
        self.translation_file_path = kwargs['translation_file_path']
        self.command_parser = CoronaSpreadFeatureCommandParser(
            category = CommandCategory.CORONA_SPREAD,
            keywords = CoronaSpreadFeature.FEATURE_KEYWORDS,
            subcategories = CoronaSpreadFeature.FEATURE_SUBCATEGORIES
        )

        self.callbacks = {
            CommandSubcategory.CORONA_SPREAD_TOTAL_DEATHS: lambda: self.get_total_deaths(),
            CommandSubcategory.CORONA_SPREAD_TOTAL_RECOVERIES: lambda: self.get_total_recoveries(),
            CommandSubcategory.CORONA_SPREAD_TOTAL_INFECTIONS: lambda: self.get_total_infections(),
            CommandSubcategory.CORONA_SPREAD_MOST_DEATHS: lambda: self.get_most_deaths(),
            CommandSubcategory.CORONA_SPREAD_MOST_RECOVERIES: lambda: self.get_most_recoveries(),
            CommandSubcategory.CORONA_SPREAD_MOST_INFECTIONS: lambda: self.get_most_infections(),
            CommandSubcategory.CORONA_SPREAD_LEAST_INFECTIONS: lambda: self.get_least_infections(),
            CommandSubcategory.CORONA_SPREAD_LEAST_DEATHS: lambda: self.get_least_deaths(),
            CommandSubcategory.CORONA_SPREAD_LEAST_RECOVERIES: lambda: self.get_least_recoveries(),
            CommandSubcategory.CORONA_DATA_TIMESTAMP: lambda: self.interface.get_data_timestamp(),
            CommandSubcategory.CORONA_INFECTIONS_BY_QUERY: self.get_cases_by_country,
            CommandSubcategory.CORONA_DEATHS_BY_QUERY: self.get_deaths_by_country,
            CommandSubcategory.CORONA_RECOVERIES_BY_QUERY: self.get_recoveries_by_country,
            CommandSubcategory.CORONA_NEW_CASES_BY_QUERY: self.get_new_cases_by_country
        }

        self.interactive_methods = (
            self.get_cases_by_country,
            self.get_recoveries_by_country,
            self.get_deaths_by_country,
            self.get_new_cases_by_country
        )

        self.mapped_pronouns = (
            CommandPronoun.INTERROGATIVE,
        )

        api_handle = coronafeatureclient.ApiHandle(uri = kwargs['CORONA_API_URI'], standby_hours = 1)
        api_handle.add_header('x-rapidapi-host', kwargs['CORONA_API_RAPIDAPI_HOST'])
        api_handle.add_header('x-rapidapi-key', kwargs['CORONA_API_RAPIDAPI_KEY'])

        super().__init__(
            command_parser = self.command_parser,
            callbacks = self.callbacks,
            interface = coronafeatureclient.Client(api_handle, self.translation_file_path),
            interactive_methods = self.interactive_methods
        )

    @logger
    def get_total_deaths(self):
        response = self.interface.get_total_deaths()
        return f'Totalt har {response} omkommit globalt'
    
    @logger
    def get_total_recoveries(self):
        response = self.interface.get_total_recoveries()
        return f'Totalt har {response} tillfrisknat globalt'
    
    @logger
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
        return f'Totalt har {response} insjuknat globalt'
    
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
    def get_new_cases_by_country(self, message: discord.Message) -> str:
        """
        Get new cases by country. New cases are defined by API.
        :param message:
            original message from Discord
        :returns:
            str
        """
        try:
            country = message.content[-1].strip(fw.FeatureCommandParserBase.IGNORED_CHARS)
            response = self.interface.get_by_query(query = 'new_cases', country_name = country)
            
            if int(response.replace(',','').strip()) > 1: 
                new = 'nya'
            else:
                new = 'nytt'

            return f' {response} {new} fall av corona i {country.capitalize()}'
        except Exception as e:
            pass

    @logger
    def get_cases_by_country(self, message: discord.Message) -> str:
        """
        Get cases by country.
        :param message:
            original message from Discord
        :returns:
            str
        """
        try:
            country = message.content[-1].strip(fw.FeatureCommandParserBase.IGNORED_CHARS)
            response = self.interface.get_by_query(query = 'cases', country_name = country)
            return f'Totalt {response} har smittats av corona i {country.capitalize()}'
        except Exception as e:
            pass

    @logger
    def get_recoveries_by_country(self, message: discord.Message) -> str:
        """
        Get recoveries by country.
        :param message:
            original message from Discord
        :returns:
            str
        """
        try:
            country = message.content[-1].strip(fw.FeatureCommandParserBase.IGNORED_CHARS)
            response = self.interface.get_by_query(query = 'total_recovered', country_name = country)
            return f'Totalt {response} har tillfrisknat i corona i {country.capitalize()}'
        except Exception as e:
            pass

    @logger
    def get_deaths_by_country(self, message: discord.Message) -> str:
        """
        Get deaths by country.
        :param message:
            original message from Discord
        :returns:
            str
        """
        try:
            country = message.content[-1].strip(fw.FeatureCommandParserBase.IGNORED_CHARS)
            response = self.interface.get_by_query(query = 'deaths', country_name = country)
            return f'Totalt {response} har omkommit i corona i {country.capitalize()}'
        except Exception as e:
            pass