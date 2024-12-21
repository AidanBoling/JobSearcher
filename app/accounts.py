import os
from dotenv import load_dotenv, find_dotenv, set_key
from linked_in import LinkedInScraper
from user_settings import SettingsControl, JobSearch

env_file = find_dotenv()
load_dotenv(env_file)

accounts = {'LINKEDIN': {'search_bot': LinkedInScraper}}

user_search_settings = SettingsControl(JobSearch, 'job_search').get_section_config()
user_accounts_settings = user_search_settings['linked_accounts']


for account_name, config in user_accounts_settings.items():
    name = account_name.upper()

    try:
        accounts[name].update(config)
    except KeyError:
        pass


def get_enabled_job_boards() -> dict:
    return {key: value for key, value in accounts.items() if value['enabled'] is True}

def get_account_credentials(account:str):
    prefix = account.upper()

    username = os.getenv(f'{prefix}_USERNAME')
    password = os.environ.get(f'{prefix}_PASSWORD')

    if username and password:
        return {'username': username, 'password': password}
    
    else:
        return None


def set_credentials(account:str, username:str, password:str):
    if not account.upper() in accounts.keys():
        raise ValueError('No such account option')

    key_prefix = account.upper() 

    set_key(env_file, f'{key_prefix}_USERNAME', username)
    set_key(env_file, f'{key_prefix}_PASSWORD', password)