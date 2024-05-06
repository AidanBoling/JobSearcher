import selenium.common.exceptions as selexceptions
from linked_in import LinkedInScraper
from selenium_driver import SeleniumDriver

# TODO: Set up and connect database

def main():

    driver = SeleniumDriver()
    li_bot = LinkedInScraper(driver)

    # Login (skips if already logged in --> username field element won't be found, so throws error)
    try: 
        li_bot.login_to_linkedin()
    except selexceptions.NoSuchElementException:
        pass

    search_phrases = ['junior%20software%20engineer', 'software%20engineer']
    
    all_job_ids = []
    for phrase in search_phrases:
        ids = li_bot.search_jobs(phrase)
        all_job_ids.extend(ids)
    
    unique_jobs_found = dedupe_list(all_job_ids)
    print(f'\nUnique jobs found: {len(unique_jobs_found)}/{len(all_job_ids)}\n')
    
    jobs = li_bot.get_job_info_from_ids(unique_jobs_found)
    
    # Later TODO: Test data with pandas
    # Later TODO: Save data into db
    
    driver.quit()


def dedupe_list(flat_list):
    return list(dict.fromkeys(flat_list))


# NOTE: Using specific profile, it seems Chrome browser must be quit completely between tests, or selenium will throw error (Chrome failed to launch...). 


if __name__ == '__main__':
    main()
    # app.run(debug=True)


#--- TRASH ---

#  try:
#      driver = webdriver.Chrome(options=options)
#  except selexceptions.SessionNotCreatedException:
#      # todo: quit out of all sessions here

#/------------