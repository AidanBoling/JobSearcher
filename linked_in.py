import os
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions as selexceptions
from selenium_driver import SeleniumDriver
from time import sleep
import random
import re

LINKEDIN_USERNAME = os.environ.get('LINKEDIN_USERNAME')
LINKEDIN_PASSWORD = os.environ.get('LINKEDIN_PASSWORD')

LINKEDIN_LOGIN_URL = 'https://www.linkedin.com/login'

LI_SEARCH_URL_START = 'https://www.linkedin.com/jobs/search/?f_E=2&f_TPR=r604800&f_WT=2&geoId=103644278&keywords='
LI_SEARCH_URL_END = '&location=United%20States&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true'
LI_JOB_PAGE_BASE_URL = 'https://www.linkedin.com/jobs/view/'

MAX_ATTEMPTS = 2


class LinkedInScraper:

    def __init__(self, driver_control: SeleniumDriver):
        self.sel = driver_control
        self.driver = driver_control.get_driver()
        self.current_results_page = 1
        self.total_pages = 1
        self.job_ids = []
        self.retry_ids_list = []


    def login_to_linkedin(self):
        self.driver.get(LINKEDIN_LOGIN_URL)

        username_field = self.driver.find_element(By.NAME, 'session_key')
        password_field = self.driver.find_element(By.NAME, 'session_password')

        self.sel.wait_until_available(username_field)
        
        username_field.send_keys(LINKEDIN_USERNAME)
        sleep(random.choice([1,2,3]))
        password_field.send_keys(LINKEDIN_PASSWORD, Keys.ENTER)

        # Allow time for user to complete captcha and confirm 2fa auth -- do 10-second loop to check page header (max wait of 60 seconds)
        awaiting_verification = True
        i = 6
        while awaiting_verification and i > 0:
            sleep(10)
            header = self.driver.find_element(By.TAG_NAME, 'h1').text
            print(header)
            header_words = header.lower().split()
            if 'check' in header_words:
                awaiting_verification = True
                print('Verification page detected. Waiting.')
            else:
                awaiting_verification = False
            i -= 1

        # Later TODO: Improve handling of 404 page
        #Check if on 404 page -- exits program if so
        try:
            is_404_page = self.driver.find_element(By.ID, 'error404')
            print('Landed on 404 page -- troubleshooting required.')
            sys.exit()
            # return login_to_linkedin()
        except selexceptions.NoSuchElementException: 
            pass

        if awaiting_verification: 
            print('Verification took too long. Aborting.')
            self.driver.quit()
            sys.exit()


    def search_jobs(self, search_phrase):
        '''Searches LinkedIn for given search_phrase, and returns list of all job ids found in results.'''

        self.driver.get(LI_SEARCH_URL_START + search_phrase + LI_SEARCH_URL_END)
        sleep(2)
        
        # Get pagination info from page (skips if error b/c only one page of results)
        try: 
            self.set_current_page()
            page_button_els = self.get_pagination_buttons()
            self.total_pages = int(page_button_els[-1].get_attribute('data-test-pagination-page-btn'))
            print(f'\nPages: {self.total_pages}')
        except selexceptions.NoSuchElementException:
            pass
        except IndexError:
            pass

        # Go through each page of results and get job ids

        # TODO: Test page cycling when there are many result pages
        # while current_page <= total_pages:
        while self.current_results_page <= 2:            
            # Get all job cards on results page
            job_cards_on_page = self.driver.find_elements(By.CSS_SELECTOR, 'div.jobs-search-results-list > ul > li')

            # Get ids from job cards
            ids = [self.job_ids.append(card.get_attribute('data-occludable-job-id')) for card in job_cards_on_page]
            print(f'Page {self.current_results_page} -- IDs collected: {len(ids)}/{len(job_cards_on_page)}')
            
            if self.total_pages > 1:     
                self.go_to_next_page()
            else:
                break
        
        return self.job_ids


    def set_current_page(self):
        selected_page_button_el = self.driver.find_element(By.CSS_SELECTOR, 'div.jobs-search-results-list__pagination ul li.selected')
        self.sel.wait_until_available(selected_page_button_el, timeout=5)
        
        self.current_results_page = int(selected_page_button_el.text)
        # return int(selected_page_button_el.text)


    def get_pagination_buttons(self):
        pagination_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'div.jobs-search-results-list__pagination ul li')
        return pagination_buttons


    def go_to_next_page(self):
        # Go to next page & update current_page
        next_page = self.current_results_page + 1
        while next_page > self.current_results_page:
            page_button_els = self.get_pagination_buttons()
            for button in page_button_els:
                button_number = button.get_attribute('data-test-pagination-page-btn')
                if button_number == f'{next_page}':
                    button.click()
                    break

            sleep(1)
            self.set_current_page()


    def get_job_info_from_ids(self):
        '''For each job id, navigate to job page and try to get info. Tries again (up to given maximum attempts) on jobs for which 
        sufficient info couldn't be pulled.'''
        jobs = []

        # For each job id, navigate to job page and get info for each job id. 
        # If can't pull sufficient info for a job, job id is added to retry list.
        for id in self.job_ids:
            retry_id = self.get_job_info(id, jobs)
            if retry_id:
                self.retry_ids_list.append(id)
        
        print(f'\nJobs to retry: {self.retry_ids_list}\n')
        
        # Retry jobs which failed/have missing info. If retry is successful, id is removed from retry list.
        for _ in range(MAX_ATTEMPTS - 1):
            while len(self.retry_ids_list) > 0:
                for id in self.retry_ids_list:
                    retry = self.get_job_info(id, jobs, attempt_num=2)
                    if not retry:
                        self.retry_ids_list.remove(id)
        
        print('\nJobs collected: ', len(jobs))
        print('Jobs not collected: ', self.retry_ids_list)
        
        return jobs


    def job_ids_match(self, list_item_id):
        job_title_a = self.driver.find_element(By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__container--two-pane div h1 a')
        job_link = job_title_a.get_attribute('href').split('/?')[0]
        job_id = job_link.split('/')[-1]

        if job_id == list_item_id:
            return True
        return False


    def get_job_info(self, job_id:str, jobs:list, attempt_num:int=1):
        job = {}
        job_link = LI_JOB_PAGE_BASE_URL + job_id
        retry = False
        self.driver.get(job_link)
        
        try:
            job_view = self.driver.find_element(By.CSS_SELECTOR, 'div.jobs-details')
            self.sel.wait_until_available(job_view, timeout=5)
        except selexceptions.NoSuchElementException:
            return True
        
        if attempt_num > 1:
            sleep(3)
        
        # MAIN POST DETAILS
        # ...Post title and link: 
        job['post title'] = job_view.find_element(By.TAG_NAME, 'h1').text
        job['id'] = job_id
        job['post link'] = job_link
        print(f'title: {job["post title"]} [#{job["id"]}]')

        # ...Company and posting details
        try:
            company_posting_details_el = job_view.find_element(By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__primary-description-container div')
            self.sel.wait_until_available(company_posting_details_el, timeout=10)
            
        except selexceptions.NoSuchElementException:
        # NOTE: Would be better to use try/catch outside of function? Might depend on whether pandas requires all keys present for each item in a dict...
            
            retry = True
            # If not yet at max attempts, stop scraping and go to next id. Otherwise, continue collecting but leave fields blank.
            if attempt_num < MAX_ATTEMPTS:
                return retry
            else:
                job['company name'] = ''
                job['company location'] = ''
                job['posted date'] = ''

        else:
            company_posting_details = [item.strip() for item in company_posting_details_el.text.split('·')]
            # print('company and post details: ', company_posting_details)
            
            job['posted date'] = company_posting_details[2]
            job['company name'] = company_posting_details[0]
            job['company location'] = company_posting_details[1]
            print(f'Company: {job["company name"]} ({job["company location"]})')
        
        # ...More about company:
        try:
            company_details_other_els = job_view.find_elements(By.CSS_SELECTOR, 'div > ul > li')
            sleep(.02)
            company_info_other = []
            for element in company_details_other_els:
                icon_type = element.find_element(By.CSS_SELECTOR, 'li-icon').get_attribute('type')
                if icon_type == 'company':
                    company_info_other = [item.strip() for item in element.text.split('·')]
                    job['company other'] = company_info_other
                    # print('Company info - other: ', company_info_other)
        except selexceptions.NoSuchElementException:
            pass

        # ...More about job: 
        job_details_list = []
        try:
            job_details_other_els = job_view.find_elements(By.CSS_SELECTOR, 'div > ul > li > span > span')
            sleep(.02)
        except selexceptions.NoSuchElementException:
            pass
        else:
            job_details_list = [item.text.split('\n')[0] for item in job_details_other_els]
            [job_details_list.remove('%') for _ in range(job_details_list.count('%'))]
            print('Job details list: ', job_details_list)
        
        if len(job_details_list) == 0:
            retry = True
        else:
            job['salary'] = None
            # If the first item in job_details_list is money $0, remove from list, set as job salary 
            match = re.search(r"^\$\d+", job_details_list[0])
            if match is not None:
                job['salary'] = job_details_list.pop(0)

            fields_map = {0: 'workplace type', 1: 'employment type', 2: 'level'}   
            for i in range(len(job_details_list)):
                if i <= 2:
                    job[fields_map[i]] = job_details_list[i]
                    # print(f'{fields_map[i]}: {job_details_list[i]}')

        if job['salary'] is None:
            # Check for salary again, a different way
            try:
                job_benefits_el = self.driver.find_element(By.CSS_SELECTOR, '#SALARY')
                salary_card = job_benefits_el.find_element(By.CSS_SELECTOR, 'div[data-view-name="job-salary-card"]')
                h3 = salary_card.find_element(By.TAG_NAME, 'h3')
            except selexceptions.NoSuchElementException:
                # print('No salary card element found.')
                pass
            else:
                if h3.text == 'Base salary':
                    job_salary_info_list = [item.strip() for item in salary_card.text.split('\n')]
                    job['salary'] = job_salary_info_list[-1]
                    print('Job salary: ', job['salary'])
        

        # JOB DESCRIPTION
        job_description_el = self.driver.find_element(By.CSS_SELECTOR, 'div.jobs-description')
        self.sel.wait_until_available(job_description_el)
        job['description'] = job_description_el.text
    
        jobs.append(job)

        return retry