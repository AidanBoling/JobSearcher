import os
from selenium import webdriver
import selenium.common.exceptions as selexceptions
from selenium.webdriver.support.wait import WebDriverWait

LOCAL_USERNAME = os.environ.get('USER')
CHROME_PROFILE_DIR = '--user-data-dir=/Users/'+ LOCAL_USERNAME + '/Library/Application Support/Google/Chrome/Profile 1'


class SeleniumDriver:
    def __init__(self, is_headless: bool=False):
        options = webdriver.ChromeOptions()
        # options.add_experimental_option('detach', True)   # Uncomment this only if you have headless OFF and want browser window to stay open for troubleshooting.
        options.add_argument(CHROME_PROFILE_DIR)
        if is_headless:
            options.add_argument("--headless=new")

        self.driver = webdriver.Chrome(options=options)

    def get_driver(self):
        return self.driver

    def wait_until_available(self, element, timeout=10, poll_frequency=.2):
        errors = [selexceptions.NoSuchElementException, selexceptions.ElementNotInteractableException]
        
        wait = WebDriverWait(self.driver, timeout=timeout, poll_frequency=poll_frequency, ignored_exceptions=errors)
        wait.until(lambda d : element.is_displayed())

    def quit(self):
        return self.driver.quit()