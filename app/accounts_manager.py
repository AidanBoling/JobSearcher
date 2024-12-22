import os
from dotenv import load_dotenv, find_dotenv, set_key
from linked_in import LinkedInScraper
from user_settings import SettingsControl, JobSearch

env_file = find_dotenv()
load_dotenv(env_file)

ACCOUNTS = {'LINKEDIN': {'name': 'LinkedIn', 'search_bot': LinkedInScraper, 'defaults': {}}}


class AccountsManager:
    def __init__(self):
        self.base_config = ACCOUNTS
        self.user_config_job_search_ctrl = SettingsControl(JobSearch, 'job_search')
        self.user_config: dict = self.user_config_job_search_ctrl.get_section_config()['linked_accounts']
        self.calculated_info: dict = {}
        self.accounts = {}
        self.user_config_defaults: dict = {}

        self.refresh_calculated_info()
        self.refresh_combined_accounts_info()

        for account, config in self.base_config.items():
            try:
                url = config['defaults']['search_url']
            except KeyError:
                url = ''
            
            self.user_config_defaults[account] = {'search_url': url}
        

    def get_account_credentials(self, account:str) -> dict:
        prefix = account.upper()

        username = os.getenv(f'{prefix}_USERNAME')
        password = os.getenv(f'{prefix}_PASSWORD')

        return {'username': username, 'password': password}


    def refresh_calculated_info(self):
        for account in self.base_config:
            calculated = {}
            credentials = self.get_account_credentials(account)
            
            calculated['has_credentials'] = credentials['username'] and credentials['password']
            if calculated['has_credentials']:
                calculated['username'] = credentials['username']

            self.calculated_info[account] = calculated


    def refresh_combined_accounts_info(self):
        combined_info = self.base_config
        
        for account_key, config in combined_info.items():
            try:
                config.update(self.user_config[account_key.lower()])
            except KeyError:
                pass
            
            config.update(self.calculated_info[account_key])
            
        self.accounts = combined_info


    def update_user_config(self, account_key, data:dict) -> dict:
        if not self.is_valid_account(account_key): 
            raise KeyError
        
        if account_key not in self.user_config:
            self.user_config[account_key] = self.user_config_defaults[account_key]

        self.user_config[account_key] = data

        # refresh user config data:
        self.user_config_job_search_ctrl = SettingsControl(JobSearch, 'job_search')
        
        job_search_settings = self.user_config_job_search_ctrl.get_as_dataclass()
        job_search_settings.linked_accounts[account_key.lower()] = self.user_config[account_key]
        
        self.user_config_job_search_ctrl.save_to_file(job_search_settings) 

        self.refresh_calculated_info()
        self.refresh_combined_accounts_info()

        return self.user_config[account_key]


    def is_valid_account(self, account_key:str) -> bool:
        if account_key.upper() in self.base_config:
            return True
        return False


    def get_enabled_job_boards(self) -> dict:
        return {key: value for key, value in self.accounts.items() if value['enabled'] is True}
    
    
    def get_frontend_data(self) -> dict: 
        accounts_data = {}
        
        for account_key, config in self.user_config.items():
            if self.is_valid_account(account_key):
                accounts_data[account_key] = config
                calculated = self.calculated_info[account_key.upper()]
                accounts_data[account_key].update(calculated)
                accounts_data[account_key]['name'] = self.base_config[account_key.upper()]['name']

        return accounts_data


    def set_credentials(self, account:str, username:str, password:str):
        if not self.is_valid_account():
            raise ValueError('No such account option')

        key_prefix = account.upper() 

        set_key(env_file, f'{key_prefix}_USERNAME', username)
        set_key(env_file, f'{key_prefix}_PASSWORD', password)
