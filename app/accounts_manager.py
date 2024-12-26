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
        self.user_config_job_search_ctrl: SettingsControl = SettingsControl(JobSearch, 'job_search')
        self.user_config: dict = self.user_config_job_search_ctrl.get_section_config()['linked_accounts']
        self.user_config_defaults: dict = {}
        # self.accounts: dict = {}

        #Calculated
        self.calculated_each: dict = {}
        self.calculated_all: dict = {'setup_errors': [], 'enabled': []}
        self.accounts_available:list = []
        self.enabled_not_set_up:list = []

        self.refresh_calculated_data()
        # self.refresh_combined_accounts_info()

        for account, config in self.base_config.items():
            try:
                url = config['defaults']['search_url']
            except KeyError:
                url = ''
            
            self.user_config_defaults[account] = {'search_url': url}
        

    def refresh_calculated_data(self):
        setup_errors = []
        enabled = []

        for account in self.base_config:
            account = account.lower()
            calc = {'has_credentials': True,
                    'required_missing': []}
            
            credentials = self.get_account_credentials(account)
            
            if not credentials['username'] or not credentials['password']:
                calc['has_credentials'] = False
                calc['required_missing'].append('username or password')

            if credentials['username']:
                calc['username'] = credentials['username']

            user_config = self.user_config.get(account)

            if user_config:
                print(user_config)
                if not user_config.get('search_url'):
                    calc['required_missing'].append('search url')
                if user_config.get('enabled') == True:
                    enabled.append(account)
            else:        
                calc['required_missing'].append('search url')  
  


            if calc['required_missing']:
                setup_errors.append(account)

            self.calculated_each[account] = calc
        
        self.calculated_all = {'enabled': enabled,
                               'setup_errors': setup_errors}
        self.available_accounts = [account for account in enabled if account not in setup_errors]
        print('available accounts: ',self.available_accounts)

        self.enabled_not_set_up = [account for account in enabled if account in setup_errors]
        print(self.enabled_not_set_up)



    # def refresh_combined_accounts_info(self):
    #     combined_info = self.base_config
        
    #     for account_key, config in combined_info.items():
    #         account_key = account_key.lower()
    #         try:
    #             config.update(self.user_config[account_key])
    #         except KeyError:
    #             pass
            
    #         config.update(self.calculated_each[account_key])
            
    #     self.accounts = combined_info


    def get_account_credentials(self, account:str) -> dict:
        account = account.upper()

        username = os.getenv(f'{account}_USERNAME')
        password = os.getenv(f'{account}_PASSWORD')

        return {'username': username, 'password': password}


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

        self.refresh_calculated_data()
        # self.refresh_combined_accounts_info()

        return self.user_config[account_key]


    def is_valid_account(self, account_key:str) -> bool:
        if account_key.upper() in self.base_config:
            return True
        return False


    def get_enabled_job_boards(self) -> dict:
        return {key: value for key, value in self.accounts.items() if value['enabled'] is True}
    
    
    def get_frontend_data(self) -> dict: 
        '''Aggregates just the info needed for the UI for all accounts.'''
       
        accounts_data = {}
        for key, config in self.base_config.items():
            account = key.lower()
            accounts_data[account] = {'name': config['name'],
                                    **self.user_config[account],
                                    **self.calculated_each[account]
                                    }
    
        accounts_summary = {'available': self.available_accounts,
                            'enabled_not_set_up': {'keys': self.enabled_not_set_up, 'names': [accounts_data[account]['name'] for account in self.enabled_not_set_up]},
                            **self.calculated_all}

        return {'accounts': accounts_data, 'summary': accounts_summary}


    def set_credentials(self, account:str, username:str, password:str):
        if not self.is_valid_account():
            raise ValueError('No such account option')

        key_prefix = account.upper() 

        set_key(env_file, f'{key_prefix}_USERNAME', username)
        set_key(env_file, f'{key_prefix}_PASSWORD', password)

        self.refresh_calculated_data()
        # self.refresh_combined_accounts_info()
