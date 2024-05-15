# import selenium.common.exceptions as selexceptions
from pathlib import Path
from selenium_driver import SeleniumDriver
from job_db_control import JobDbControl
from linked_in import LinkedInScraper

ROOT_DIR = Path(__file__).parent
jobs_db = ROOT_DIR / "instance/jobs.db"

HEADLESS = True
LIMIT_PAGES = 1
MAX_ATTEMPTS_PER_ID = 2

SEARCH_PHRASES = ['junior software engineer', 'software engineer']


def run_search(db_control: JobDbControl=None):
    driver = SeleniumDriver(is_headless=HEADLESS)
    search_bot = LinkedInScraper(driver, limit_result_pages=LIMIT_PAGES, max_attempts=MAX_ATTEMPTS_PER_ID)

    # search_phrases = ['junior software engineer', 'software engineer']
    search_phrases = ['junior software engineer']
    jobs = []
    
    all_job_ids = login_and_search(search_bot, search_phrases)
    new_job_posts = trim_search_results(all_job_ids, db_control)
    
    if new_job_posts:
        jobs = get_details(search_bot, new_job_posts)        
    else:
        print('No new job posts to add from LinkedIn.') 
   
    return jobs


def login_and_search(search_bot, search_phrases: list):

    search_bot.login()

    all_job_ids = []
    for phrase in search_phrases:
        print('Searching for:', phrase)
        ids = search_bot.search_jobs(phrase)
        all_job_ids.extend(ids)
    
    return all_job_ids


def trim_search_results(job_ids: list, db_control: JobDbControl):

    # De-duplicate results list
    unique_jobs_found = list(dict.fromkeys(job_ids))
    print(f'\nUnique jobs found: {len(unique_jobs_found)}/{len(job_ids)}')
    
    new_job_posts = []
    if jobs_db and db_control is not None:
        # [x] TODO: Pull post ids from DB for this job board; remove ids from "unique_jobs" list that match
        existing_ids = db_control.get_post_ids(job_board='LinkedIn')
        print('Existing ids:', existing_ids)
        
        if existing_ids:
            new_job_posts = [id for id in unique_jobs_found if int(id) not in existing_ids]
        else:
            new_job_posts = unique_jobs_found
    else:
        new_job_posts = unique_jobs_found
    print(f'\nNew jobs found: {len(new_job_posts)}/{len(job_ids)}\n')
    
    return new_job_posts


def get_details(search_bot, new_posts: list):
    total_posts = len(new_posts)
    search_bot.set_job_ids(new_posts)
    jobs = search_bot.get_job_info_from_ids()
    print(f'\nJobs collected: {len(jobs)}/{total_posts}')
    # TODO: log_failed(new_posts)
    print(f'\nFailed to get jobs: {new_posts}')

    return jobs


if __name__ == '__main__':
    run_search()