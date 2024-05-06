import os
from selenium import webdriver
import selenium.common.exceptions as selexceptions
from selenium.webdriver.support.wait import WebDriverWait

LOCAL_USERNAME = os.environ.get('USER')
CHROME_PROFILE_DIR = '--user-data-dir=/Users/'+ LOCAL_USERNAME + '/Library/Application Support/Google/Chrome/Profile 1'


class SeleniumDriver:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option('detach', True)
        options.add_argument(CHROME_PROFILE_DIR)

        self.driver = webdriver.Chrome(options=options)

    def get_driver(self):
        return self.driver

    def wait_until_available(self, element, timeout=5, poll_frequency=.2):
        errors = [selexceptions.NoSuchElementException, selexceptions.ElementNotInteractableException]
        
        wait = WebDriverWait(driver, timeout=timeout, poll_frequency=poll_frequency, ignored_exceptions=errors)
        wait.until(lambda d : element.is_displayed())

    def quit(self):
        return self.driver.quit()


#NOTE: Using specific profile, it seems Chrome browser must be quit completely between tests, or selenium will throw error (Chrome failed to launch...). 
