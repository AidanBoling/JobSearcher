# import selenium.common.exceptions as selexceptions
import os
from pathlib import Path
from selenium_driver import SeleniumDriver
from db_control import JobDbControl
from user_settings import SearchSettings, SettingsControl, JobSearch

from accounts_manager import AccountsManager
# from dotenv import load_dotenv

# load_dotenv()
# load_dotenv(ROOT_DIR / '.env')

ROOT_DIR = Path(__file__).parent

EXCLUDED_IDS_DIR = ROOT_DIR / 'instance/excluded_id_lists'
if not os.path.exists(EXCLUDED_IDS_DIR):
    os.mkdir(EXCLUDED_IDS_DIR)

TEST = True

HEADLESS = True
LIMIT_PAGES = 1
MAX_ATTEMPTS_PER_ID = 2


def run_search(db_control: JobDbControl=None, search_settings: object=None):
    driver = SeleniumDriver(is_headless=HEADLESS)

    accounts_manager = AccountsManager()

    if search_settings is None:
        job_search_config = SettingsControl(JobSearch, 'job_search').get_as_dataclass()
        search_settings = job_search_config.search_settings
   
    search_phrases = search_settings.search_phrases
    if TEST:
        search_phrases = ['junior software engineer']

    
    available_job_boards = accounts_manager.get_combined_info(accounts_manager.available_accounts)
    

    all_jobs = []
    for job_board in available_job_boards:
        board_name = job_board['name']
        # print(board_name) --> log...
        credentials = accounts_manager.get_account_credentials(board_name)
        search_url = job_board['search_url']
        search_bot = job_board['search_bot'](driver, search_url, limit_result_pages=LIMIT_PAGES, max_attempts=MAX_ATTEMPTS_PER_ID)

        jobs = []
        
        all_job_ids = login_and_search(search_bot, credentials, search_phrases)
        new_job_posts = trim_search_results(all_job_ids, db_control, job_board)
        
        if new_job_posts:
            jobs = get_details(search_bot, new_job_posts)
            update_excluded_ids_file(search_bot, job_board)

        else:
            print(f'No new job posts to add from {board_name}.') 
        
        all_jobs.extend(jobs)

    
    return all_jobs


def login_and_search(search_bot: object, credentials: dict, search_phrases: list):

    search_bot.login(credentials)

    all_job_ids = []
    for phrase in search_phrases:
        print('Searching for:', phrase)
        ids = search_bot.search_jobs(phrase)
        all_job_ids.extend(ids)
    
    return all_job_ids


def trim_search_results(job_ids: list, db_control: JobDbControl, job_board: str):

    # De-duplicate results list
    jobs_found = len(job_ids)
    unique_jobs_found = list(dict.fromkeys(job_ids))
    print(f'\nUnique jobs found: {len(unique_jobs_found)}/{jobs_found}')
    
    excluded_ids_file = ROOT_DIR / f'instance/excluded_id_lists/{job_board}.txt'
    excluded_ids = []
    try:
        with open(excluded_ids_file, 'r') as file:
            for line in file:
                excluded_ids.append(line.strip('\n'))
    except FileNotFoundError:
        pass

    existing_ids = []
    if db_control is not None:
        existing_ids = db_control.get_post_ids(job_board=job_board)
        print('Existing ids:', existing_ids)
    
    new_job_posts = [id for id in unique_jobs_found if int(id) not in existing_ids and id not in excluded_ids]  

    print(f'\nNew jobs found: {len(new_job_posts)}/{jobs_found}\n')
    
    return new_job_posts


def get_details(search_bot: object, new_posts: list):
    total_posts = len(new_posts)
    search_bot.set_job_ids(new_posts)
    jobs = search_bot.get_job_info_from_ids()
    print(f'\nJobs collected: {len(jobs)}/{total_posts}')
    # TODO: log_failed(new_posts)
    print(f'\nFailed to get jobs: {new_posts}')

    return jobs


def update_excluded_ids_file(search_bot: object, job_board: str):
    excluded_ids = search_bot.excluded_ids
    print('Excluded ids: ', excluded_ids)
    excluded_ids_file = f'{EXCLUDED_IDS_DIR}/{job_board}.txt'
    
    try:
        with open(excluded_ids_file, 'a') as file:
            for id in excluded_ids:
                file.write(f'{id}\n')
    except FileNotFoundError:
        with open(excluded_ids_file, 'w+') as file:
            for id in excluded_ids:
                file.write(f'{id}\n')


if __name__ == '__main__':
    run_search()
