# import os
from dotenv import find_dotenv, load_dotenv, set_key, unset_key, get_key
from linked_in import LinkedInScraper
from user_settings import SettingsControl, JobSearch
from logger import LoggingManager

env_file = find_dotenv()
load_dotenv(env_file)

logging_manager = LoggingManager()
logger = logging_manager.logger


ACCOUNTS = {'LINKEDIN': {'name': 'LinkedIn', 'search_bot': LinkedInScraper, 'defaults': {}}}


class AccountsManager:
    def __init__(self, job_search_config_control:SettingsControl=SettingsControl(JobSearch, 'job_search')):
        self.base_config = {account_key.lower(): value for account_key, value in ACCOUNTS.items()}
        self.user_config_job_search_ctrl: SettingsControl = job_search_config_control
        self.job_search_config: object = self.user_config_job_search_ctrl.get_as_dataclass()

        self.user_config: dict = self.job_search_config.linked_accounts
        self.user_config_defaults: dict = {}
        # self.accounts: dict = {}

        #Calculated
        self.calculated_each: dict = {}
        self.calculated_all: dict = {'setup_errors': [], 'enabled': []}
        self.available_accounts: list = []
        self.enabled_not_set_up:list = []

        
        self.refresh_calculated_data()

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
            calc = {'has_credentials': True,
                    'required_missing': []}
            
            credentials = self.get_account_credentials(account)

            if not credentials['username'] or not credentials['password']:
                calc['has_credentials'] = False
                if not credentials['username']:
                    calc['required_missing'].append('username')
                if not credentials['password']:
                    calc['required_missing'].append('password')
                # calc['required_missing'].append('username and/or password')

            if credentials['username']:
                calc['username'] = credentials['username']
                print('username [from calculated]: ', credentials['username'])
            user_config = self.user_config and self.user_config.get(account)

            if user_config:

                # print(user_config)
                if not user_config.get('search_url'):
                    calc['required_missing'].append('search URL')
                if user_config.get('enabled') == True:
                    enabled.append(account)
            else:        
                calc['required_missing'].append('search URL')  
  

            if calc['required_missing']:
                setup_errors.append(account)

            self.calculated_each[account] = calc
        
        self.calculated_all = {'enabled': enabled,
                               'setup_errors': setup_errors}
        self.available_accounts = [account for account in enabled if account not in setup_errors]
        # print('available accounts: ', self.available_accounts)

        self.enabled_not_set_up = [account for account in enabled if account in setup_errors]
        # print(self.enabled_not_set_up)


    def get_combined_info(self, accounts:list):
        accounts = [account.lower() for account in accounts]
        combined_info = {account: self.base_config[account] for account in accounts 
                         if self.is_valid_account(account)}
        
        for account_key, config in combined_info.items():
            try:
                config.update(self.user_config[account_key])
            except KeyError:
                pass

            config.update(self.calculated_each[account_key])
            
        return combined_info


    def get_account_credentials(self, account:str) -> dict:
        account = account.upper()
        
        username = get_key(env_file, f'{account}_USERNAME')
        password = get_key(env_file, f'{account}_PASSWORD')

        return {'username': username, 'password': password}


    def sort_and_save_form_data(self, parsed_form_data:dict):
        field_options = {'user_config': ['enabled', 'search_url'],
                         'credentials': ['username', 'password'],
                        #  'base_config': list(self.base_config.keys())
                         }
        
        updated = {key: {} for key in field_options.keys()}
        
        for account, fields in parsed_form_data.items():
            sorted_data = {key: {} for key in field_options.keys()}
            
            if self.is_valid_account(account):
                for field_name, value in fields.items():
                    for location, options in field_options.items():
                        if field_name in options:
                            sorted_data[location].update({field_name: value})
                            break
                
                print(f'sorted config data for account "{account}": ', sorted_data)


            # Add to "updated" only if changes were made
            
            if sorted_data['user_config']:
                current_config = self.user_config.get(account) if self.user_config.get(account) else {}
                updated_user_config = {**current_config, **sorted_data['user_config']}
                # print('updated_user_config: ',updated_user_config)
                if updated_user_config != current_config:
                    updated['user_config'][account] = updated_user_config

            if sorted_data['credentials']:
                current_credentials = self.get_account_credentials(account)
                updated_credentials = {**current_credentials, **sorted_data['credentials']}
                if updated_credentials != current_credentials:
                    updated['credentials'][account] = updated_credentials


        print('configs to update?: ', updated)

        # Save config(s) only if changes were made
        if updated['user_config']:   
    
            self.user_config = {**self.user_config, **updated['user_config']}
            self.save_user_config()
            logger.info(f'User config updated and saved for account(s): {", ".join(updated["user_config"])}')
        
        if updated['credentials']:
            for account, credentials in updated['credentials'].items():
                self.set_credentials(account, **credentials)
            # logger.info(f'Credentials saved for account(s): {", ".join(updated["credentials"])}')

        if not any([value for value in updated.values()]):
            logger.info('No changes made to account configs; no difference in given config values from current values.')
            logger.warning("Password field can't be cleared by leaving password field blank; use 'Clear' button instead.")



    def save_user_config(self) -> dict:
        # refresh job search settings data, in case other sections (not accounts-related) were updated elsewhere
        # since instantiation (e.g. via server.py)
        
        self.job_search_config = self.user_config_job_search_ctrl.get_as_dataclass()
        self.job_search_config.linked_accounts = self.user_config
        
        self.user_config_job_search_ctrl.save_to_file(self.job_search_config) 

        self.refresh_calculated_data()

        return self.user_config


    def update_user_config_for_account(self, account_key:str, data:dict) -> dict:
        account_key = account_key.lower()
        if not self.is_valid_account(account_key): 
            raise KeyError
        
        if account_key not in self.user_config:
            self.user_config[account_key] = self.user_config_defaults[account_key]
        
        self.user_config[account_key] = data
        self.save_user_config()
        
        return self.user_config[account_key]


    def is_valid_account(self, account_key:str) -> bool:
        if account_key.lower() in self.base_config:
            return True
        return False


    # def get_enabled_job_boards(self) -> dict:
    #     return {key: value for key, value in self.accounts.items() if value['enabled'] is True}
    
    
    def get_frontend_data(self) -> dict: 
        '''Aggregates just the info needed for the UI for all accounts.'''
       
        accounts_data = {}
        for account, config in self.base_config.items():            
            accounts_data[account] = {'name': config['name'],
                                    **(self.user_config[account] if self.user_config.get(account) else {}),
                                    **self.calculated_each[account]
                                    }
    
        accounts_summary = {'available': self.available_accounts,
                            'enabled_not_set_up': {'keys': self.enabled_not_set_up, 'names': [accounts_data[account]['name'] for account in self.enabled_not_set_up]},
                            **self.calculated_all}

        return {'accounts': accounts_data, 'summary': accounts_summary}


    def set_credentials(self, account:str, username:str, password:str):
        if not self.is_valid_account(account):
            raise ValueError(f'Account option not valid: {account}')

        key_prefix = account.upper() 
        credentials = {f'{key_prefix}_USERNAME':username, 
                        f'{key_prefix}_PASSWORD':password}
        credentials_to_set = {k:v for k,v in credentials.items() if v}
        
        for key, value in credentials_to_set.items():
            set_key(env_file, key, value)

        # logger.info(f'Credentials saved for account: {account}')

        self.refresh_calculated_data()


    def unset_credentials(self, account:str):
        if not self.is_valid_account(account):
            raise ValueError(f'Account option not valid: {account}')

        key_prefix = account.upper() 

        unset_key(env_file, f'{key_prefix}_USERNAME')
        unset_key(env_file, f'{key_prefix}_PASSWORD')
        
        logger.info(f'Credentials unset for account: {account}')
        
        self.refresh_calculated_data()


### TEMP:
    # def refresh_combined_accounts_info(self):
    #     combined_info = self.base_config
        
    #     for account_key, config in combined_info.items():
    #         try:
    #             config.update(self.user_config[account_key])
    #         except KeyError:
    #             pass
            
    #         config.update(self.calculated_each[account_key])
            
    #     self.accounts = combined_info