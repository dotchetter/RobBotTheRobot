try:
    import discord
except ImportError:
    print('Could not import discord, did you activate your virtual env?')

"""
This file contains code that can be used to test the CI
framework. The code here has been moved from the __init__ file
and is not changed since then in the current state.
""" 
from CoronaSpreadFeature import CoronaSpreadFeature
import json
from CommandIntegrator.ci import * 

if __name__ == "__main__":
    with open('CommandIntegrator\\commandintegrator.settings.json', 'r', encoding = 'utf-8') as f:
        default_responses = json.loads(f.read())['default_responses']
    
    processor = CommandProcessor(
        pronoun_lookup_table = PronounLookupTable(), 
        default_responses = default_responses
    )
    
    processor.features = (       
        CoronaSpreadFeature(
            CORONA_API_URI = '',
            CORONA_API_RAPIDAPI_HOST = '',
            CORONA_API_RAPIDAPI_KEY = '',
            translation_file_path = ''
        ),
    )

    # --- FOR TESTING THE COMMANDINTEGRATOR COMMANDPROCESSOR OBJECT --- 

    mock_message = discord.Message

    print(f'\n# Test mode initialized, running CommandIntegrator version: {VERSION}')
    print('# Features loaded: ', '\n')
    [print(f'  * {i}') for i in processor.features]
    print(f'\n# Write a message and press enter, as if you were using your app front end.')
    
    while True:
        mock_message.content = input('->')
        if not len(mock_message.content):
            continue

        before = timer()
        a = processor.process(mock_message)
        after = timer()

        print(f'Responded in {round(1000 * (after - before), 3)} milliseconds')

        if callable(a.response):
            print(f'\nINTERPRETATION:\n{a}\n\nEXECUTED RESPONSE METHOD: {a.response()}')
            if a.error:
                print('Errors occured, see caught traceback below.')
                pprint(a.error)
        else:
            print(f'was not callable: {a}')