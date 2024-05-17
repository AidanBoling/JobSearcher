import os
import sys
from time import sleep
import random
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions as selexceptions
from selenium_driver import SeleniumDriver
from user_settings import SearchSettings, SettingsControl


LINKEDIN_USERNAME = os.environ.get('LINKEDIN_USERNAME')
LINKEDIN_PASSWORD = os.environ.get('LINKEDIN_PASSWORD')

LINKEDIN_LOGIN_URL = 'https://www.linkedin.com/login'

# Later TODO: For easier changing of search params, change below so can paste the entire url from an example
# search, and get the START and END from that.
LI_SEARCH_URL_START = 'https://www.linkedin.com/jobs/search/?f_E=2&f_TPR=r604800&f_WT=2&geoId=103644278&keywords='
LI_SEARCH_URL_END = '&location=United%20States&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true'
LI_JOB_PAGE_BASE_URL = 'https://www.linkedin.com/jobs/view/'

DEFAULT_MAX_ATTEMPTS = 2



# class JobBoardScraper:
#     def __init__(self, driver_control: SeleniumDriver, settings: object):
#         self.sel = driver_control
#         self.driver = driver_control.get_driver()
#         self.user_settings = 


class LinkedInScraper:

    def __init__(self, driver_control: SeleniumDriver, limit_result_pages='', max_attempts=DEFAULT_MAX_ATTEMPTS):
        # super().__init__(driver_control)
        self.sel = driver_control
        self.driver = driver_control.get_driver()
        self.current_results_page = 1
        self.total_pages = 1
        self.result_pages_limit = limit_result_pages
        self.job_ids = []
        self.max_attempts = max_attempts
        self.excluded_ids = []

        # search_settings_controller = SettingsControl(SearchSettings, 'search_settings')
        self.user_settings = SettingsControl(SearchSettings, 'search_settings').get_section_config()


    def set_job_ids(self, ids: list):
        self.job_ids = ids


    def login(self):
        self.driver.get(LINKEDIN_LOGIN_URL)
        
        try:
            username_field = self.driver.find_element(By.NAME, 'session_key')
            password_field = self.driver.find_element(By.NAME, 'session_password')
        
            self.sel.wait_until_available(username_field)
        
            username_field.send_keys(LINKEDIN_USERNAME)
            sleep(random.choice([1,2,3]))
            password_field.send_keys(LINKEDIN_PASSWORD, Keys.ENTER)

        except selexceptions.NoSuchElementException:
            # Skips if already logged in --> username field element won't be found, so throws error
            return

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


    def search_jobs(self, search_phrase: str):
        '''Searches LinkedIn for given search_phrase, and returns list of all job ids found in results.'''
        
        search_phrase = search_phrase.replace(' ', '%20')
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
        total_pages = self.total_pages
        if self.result_pages_limit:
            total_pages = self.result_pages_limit
        
        while  self.current_results_page <= total_pages:
            # Get all job cards on results page
            job_cards_on_page = self.driver.find_elements(By.CSS_SELECTOR, 'div.jobs-search-results-list > ul > li')

            # Get ids from job cards
            ids = [self.job_ids.append(card.get_attribute('data-occludable-job-id')) for card in job_cards_on_page]
            print(f'Page {self.current_results_page} -- IDs collected: {len(ids)}/{len(job_cards_on_page)}')
            
            if self.current_results_page < total_pages > 1:
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
        '''
        For each job id, navigate to job page and try to get info. If sufficient info is pulled, job details added to jobs list 
        and job removed from ids list. Any jobs left in ids list (insufficient info) are retried, until max_attempts limit is reached.
        '''
        jobs = []
          
        for n in range(0, self.max_attempts):
            attempt = n+1
            print(f'\nAttempt: {attempt}/{self.max_attempts}')
            
            if len(self.job_ids) > 0:
                for id in self.job_ids:
                    retry, job = self.get_job_info(id, attempt_num=attempt)
                    # Some non-critical fields can trigger retry=true if error finding info (more chances to get missing info). 
                    # But if is final attempt, job will still save as long as have enough critical info.
                    if job:
                        if not retry or n+1 >= self.max_attempts:
                            jobs.append(job)
                            self.job_ids.remove(id)
                    if not job and not retry:
                        self.job_ids.remove(id)
                print('Jobs left to retry: ', self.job_ids)
            
            else:
                break
                    
        return jobs


    def job_ids_match(self, list_item_id):
        job_title_a = self.driver.find_element(By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__container--two-pane div h1 a')
        job_link = job_title_a.get_attribute('href').split('/?')[0]
        job_id = job_link.split('/')[-1]

        if job_id == list_item_id:
            return True
        return False


    def get_job_info(self, job_id:str, attempt_num:int=1):
        job = {}
        retry = False
        el_wait_timeout = 5 + (5 * attempt_num)

        job_link = LI_JOB_PAGE_BASE_URL + job_id
        self.driver.get(job_link)
        
        sleep(3 * (attempt_num - 1))

        try:
            job_view = self.driver.find_element(By.CSS_SELECTOR, 'div.jobs-details')
            self.sel.wait_until_available(job_view, timeout=el_wait_timeout)
        # If times out, return true to add id to retry list
        except selexceptions.NoSuchElementException or selexceptions.TimeoutException:
            return True, []
        

        # MAIN POST DETAILS
        # ...Post title and link: 
        job['post_title'] = job_view.find_element(By.TAG_NAME, 'h1').text
        job['post_id'] = job_id
        job['post_link'] = job_link
        print(f'title: {job["post_title"]} [#{job["post_id"]}]')


        # ...Company and posting details
        try:
            company_posting_details_el = job_view.find_element(By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__primary-description-container div')
            self.sel.wait_until_available(company_posting_details_el, timeout=el_wait_timeout)
            
        except selexceptions.NoSuchElementException or selexceptions.TimeoutException:            
            retry = True
            # If not yet at max attempts, stop scraping and go to next id. Otherwise, continue collecting but leave fields blank.
            if attempt_num < self.max_attempts:
                return retry, []
            else:
                job['company_name'] = ''
                job['company_location'] = ''
                # job['posted_date'] = ''

        else:
            company_posting_details = [item.strip() for item in company_posting_details_el.text.split('·')]
            
            job['company_name'] = company_posting_details[0]
            if self.is_excluded(job_id, job['company_name'], 'exclude_companies'):
                print(f'Job excluded based on user filter: Company ({job["company_name"]})')
                # If excluded, skip to next job id. This id will not be re-tried. 
                return False, []
            
            job['company_location'] = company_posting_details[1]
            job['posted_date'] = company_posting_details[2]
            print(f'Company: {job["company_name"]} ({job["company_location"]})')

            
        # [-] TODO: if company name is in list of filters of companies to exclude 

        # ...More about company:
        try:
            company_details_other_els = job_view.find_elements(By.CSS_SELECTOR, 'div > ul > li')
            sleep(.02)
            company_info_other = []
            for element in company_details_other_els:
                icon_type = element.find_element(By.CSS_SELECTOR, 'li-icon').get_attribute('type')
                if icon_type == 'company':
                    company_info_other = [item.strip() for item in element.text.split('·')]
                    job['company_other'] = ', '.join(company_info_other)
                    # print('Company info - other: ', company_info_other)
        except selexceptions.NoSuchElementException:
            pass

        # ...More about job: 
        job['salary'] = ''
        job_details_list = []
        
        try:
            job_details_other_els = job_view.find_elements(By.CSS_SELECTOR, 'div > ul > li > span > span')
            sleep(.02)

        except selexceptions.NoSuchElementException or selexceptions.StaleElementReferenceException:
            pass
        else:
            job_details_list = self.get_job_details_list(job_details_other_els)
        

        if len(job_details_list) == 0:
            retry = True

        else:
            # Search first item in list for salary -- If starts with '$', remove from list, set as job salary 
            match = re.search(r"^\$\d+", job_details_list[0])
            if match is not None:
                job['salary'] = job_details_list.pop(0)
            
            options = {'workplace_type': ['On-site', 'Remote', 'Hybrid'],
                       'employment_type': ['Full-time', 'Part-time', 'Contract', 'Volunteer', 'Internship', 'Other'],
                       'level': ['Internship', 'Entry level', 'Associate', 'Mid-Senior level', 'Director', 'Executive']
                       }
            
            for detail in ['workplace_type', 'employment_type', 'level']:
                job[detail] = self.get_detail_from_list(job_details_list, options[detail])


            # fields_map = {0: 'workplace_type', 1: 'employment_type', 2: 'level'}   
            # for i in range(len(job_details_list)):
            #     if i <= 2:

            #         job[fields_map[i]] = job_details_list[i]
            #         # print(f'{fields_map[i]}: {job_details_list[i]}')

        if not job['salary']:
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
                    # print('Job salary: ', job['salary'])
        

        # JOB DESCRIPTION
        try:
            job_description_el = self.driver.find_element(By.CSS_SELECTOR, 'div.jobs-description')
            self.sel.wait_until_available(job_description_el, timeout=el_wait_timeout)

        except selexceptions.TimeoutException or selexceptions.NoSuchElementException:
            retry = True
            # If not yet at max attempts, stop scraping and go to next id.
            if attempt_num < self.max_attempts:
                return retry, []
            else:
                # If at max attempts but company name is not blank, leave description blank. 
                # Otherwise, stop scraping and go to next (failed to get info).
                if job['company_name']:
                    job['description'] = ''
                else:
                    return retry, []
                
        else: 
            job['description'] = self.get_job_description(job_description_el)


        job['job_board'] = 'LinkedIn'
        
        return retry, job
    

    def get_job_details_list(self, elements_list):
        job_details_list = []
        
        job_details_list = [item.text.split('\n')[0] for item in elements_list]
        [job_details_list.remove('%') for _ in range(job_details_list.count('%'))]
        print('Job details list: ', job_details_list)
    
        return job_details_list
    

    def get_detail_from_list(self, details: list, options_list: list):
        for i, item in enumerate(details):
            if item.strip() in options_list:
                return details.pop(i)
        return ''
    

    def get_job_description(self, description_el):
        job_card_classes = description_el.get_attribute("class")
        is_truncated = job_card_classes.find('jobs-description--is-truncated')
        if is_truncated != -1:
            see_more_button = description_el.find_element(By.CSS_SELECTOR, 'footer button')
            see_more_button.click()
            sleep(0.25)
        
        description = description_el.text
        
        # Cleanup
        description = re.sub(r'(^(About the job)\n)|(\n(See less)$)', '', description)
        # section_headers = re.findall(r'\n([A-Z][a-z]*)(\s[A-Z][a-z]*)?:?\s*\n', description)
        # for header in section_headers:
        #     description = re.sub(header, '<i>' + header + '</i>', description)
        
        return description
    
    def is_excluded(self, job_id, item, filter_name):
        if self.user_settings[filter_name]: 
            if item in self.user_settings[filter_name]:
                self.excluded_ids.append(job_id)
                return True
        return False