# import selenium.common.exceptions as selexceptions
import os
from pathlib import Path
from selenium_driver import SeleniumDriver
from job_db_control import JobDbControl
from linked_in import LinkedInScraper
from user_settings import SearchSettings, SettingsControl


ROOT_DIR = Path(__file__).parent
# jobs_db = ROOT_DIR / "instance/jobs.db"
EXCLUDED_IDS_DIR = ROOT_DIR / 'instance/excluded_id_lists'
if not os.path.exists(EXCLUDED_IDS_DIR):
    os.mkdir(EXCLUDED_IDS_DIR)

HEADLESS = True
LIMIT_PAGES = 1
MAX_ATTEMPTS_PER_ID = 2

TEST = True
# SEARCH_PHRASES = ['junior software engineer', 'software engineer']
    

def run_search(db_control: JobDbControl=None, search_settings: object=None):
    driver = SeleniumDriver(is_headless=HEADLESS)
    
    job_board = 'LinkedIn'
    search_bot = LinkedInScraper(driver, limit_result_pages=LIMIT_PAGES, max_attempts=MAX_ATTEMPTS_PER_ID)

    if search_settings is None:
        search_settings_controller = SettingsControl(SearchSettings, 'search_settings')
        search_settings = search_settings_controller.get_as_dataclass()
    
    search_phrases = search_settings.search_phrases
    if TEST:
        search_phrases = ['junior software engineer']
    
    jobs = []
    
    all_job_ids = login_and_search(search_bot, search_phrases)
    new_job_posts = trim_search_results(all_job_ids, db_control, job_board)
    
    if new_job_posts:
        jobs = get_details(search_bot, new_job_posts)
        update_excluded_ids_file(search_bot, job_board)

    else:
        print('No new job posts to add from LinkedIn.') 
    

    return jobs


def login_and_search(search_bot: object, search_phrases: list):

    search_bot.login()

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
    
    # new_job_posts = get_not_in_db(unique_jobs_found, db_control, job_board)
    # new_job_posts = get_not_excluded(new_job_posts, job_board)
    
    # if not new_job_posts:
    #     new_job_posts = unique_jobs_found
    

    print(f'\nNew jobs found: {len(new_job_posts)}/{jobs_found}\n')
    
    return new_job_posts


def get_not_excluded(job_board, jobs):
    # Filter out excluded ids (if any)
    excluded_ids_file = f'{EXCLUDED_IDS_DIR}/{job_board}.txt'
    excluded_ids = []
    try:
        with open(excluded_ids_file, 'r') as file:
            excluded_ids = file.readlines()
    except FileNotFoundError:
        pass
    
    return [id for id in jobs if id not in excluded_ids]


def get_not_in_db(jobs, db_control, job_board):
    # Pull post ids from DB for this job board; remove ids from "unique_jobs" list that match
    existing_ids = []
    if db_control is not None:
        existing_ids = db_control.get_post_ids(job_board=job_board)
        print('Existing ids:', existing_ids)
    
    return [id for id in jobs if int(id) not in existing_ids]


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