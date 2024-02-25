import os
import threading
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options

# Declare variables with None to indicate that they'll be set later
RESERVATION_DAYS = None
RESERVATION_MONTH = None
RESERVATION_YEAR = None
RESERVATION_SIZE = None
TODAY_DATE = None
EXPERIENCE = None
EARLIEST_TIME = None
LATEST_TIME = None
RESERVATION_TIME_FORMAT = "%I:%M %p"
RESERVATION_TIME_MIN = None
RESERVATION_TIME_MAX = None
RESTAURANT = None

# Multithreading configurations
NUM_THREADS = 1
THREAD_DELAY_SEC = 1
RESERVATION_FOUND = False

# Time between each page refresh in milliseconds. Decrease this time to
# increase the number of reservation attempts
REFRESH_DELAY_MSEC = 500

# Chrome extension configurations that are used with Luminati.io proxy.
# Enable proxy to avoid getting IP potentially banned. This should be enabled only if the REFRESH_DELAY_MSEC
# is extremely low (sub hundred) and NUM_THREADS > 1.
ENABLE_PROXY = False
USER_DATA_DIR = '~/Library/Application Support/Google/Chrome'
PROFILE_DIR = 'Default'
# https://chrome.google.com/webstore/detail/luminati/efohiadmkaogdhibjbmeppjpebenaool
EXTENSION_PATH = USER_DATA_DIR + '/' + PROFILE_DIR + '/Extensions/efohiadmkaogdhibjbmeppjpebenaool/1.149.316_0'

# Delay for how long the browser remains open so that the reservation can be finalized. Tock holds the reservation
# for 10 minutes before releasing.
BROWSER_CLOSE_DELAY_SEC = 600

WEBDRIVER_TIMEOUT_DELAY_MS = 120000

def load_configuration_from_json():
    file_path = './reservation_details.json'
    global RESERVATION_DAYS, RESERVATION_MONTH, RESERVATION_YEAR, RESERVATION_SIZE
    global TODAY_DATE, EXPERIENCE, EARLIEST_TIME, LATEST_TIME, RESERVATION_TIME_MIN, RESERVATION_TIME_MAX, RESTAURANT

    # Load data from JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)
    
        # Extract variables
        RESERVATION_DAYS = data['reservation-days']
        RESERVATION_MONTH = data['reservation-month']
        RESERVATION_YEAR = data['reservation-year']
        RESERVATION_SIZE = data['reservation-size']
        TODAY_DATE = data['date-today']
        EXPERIENCE = data['experience']
        EARLIEST_TIME = data['earliest-time']
        LATEST_TIME = data['latest-time']
        RESERVATION_TIME_FORMAT = "%I:%M %p"
        RESERVATION_TIME_MIN = datetime.strptime(EARLIEST_TIME, RESERVATION_TIME_FORMAT)
        RESERVATION_TIME_MAX = datetime.strptime(LATEST_TIME, RESERVATION_TIME_FORMAT)
        RESTAURANT = data['restaurant']
    

class reserveOnTock():
    def __init__(self):
        options = Options()
        if ENABLE_PROXY:
            options.add_argument('--load-extension={}'.format(EXTENSION_PATH))
            options.add_argument('--user-data-dir={}'.format(USER_DATA_DIR))
            options.add_argument('--profile-directory=Default')

        self.driver = webdriver.Chrome(options=options)

    def teardown(self):
        self.driver.quit()

    def reserve(self):
        global RESERVATION_FOUND
        print("Looking for availability on month: %s, days: %s, between times: %s and %s" % (RESERVATION_MONTH, RESERVATION_DAYS, EARLIEST_TIME, LATEST_TIME))

        while not RESERVATION_FOUND:
            time.sleep(REFRESH_DELAY_MSEC / 1000)
            url = f"https://www.exploretock.com/{RESTAURANT}/experience/450847/{EXPERIENCE}?date=2024-{RESERVATION_MONTH}-{TODAY_DATE}&size={RESERVATION_SIZE}&time=12%3A00"
            self.driver.get(url)
            WebDriverWait(self.driver, WEBDRIVER_TIMEOUT_DELAY_MS).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div.ConsumerCalendar-month")))

            if not self.search_month():
                print("No available days found. Continuing next search iteration")
                continue

            WebDriverWait(self.driver, WEBDRIVER_TIMEOUT_DELAY_MS).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "button.Consumer-resultsListItem.is-available")))

            print("Found availability. Sleeping for 10 minutes to complete reservation...")
            RESERVATION_FOUND = True
            time.sleep(BROWSER_CLOSE_DELAY_SEC)

    def search_month(self):
        month_object = None

        for month in self.driver.find_elements(By.CSS_SELECTOR, "div.ConsumerCalendar-month"):
            header = month.find_element(By.CSS_SELECTOR, "div.ConsumerCalendar-monthHeading")
            span = header.find_element(By.CSS_SELECTOR, "span")
            print("Encountered month", span.text)

            if RESERVATION_MONTH in span.text:
                month_object = month
                print("Month", RESERVATION_MONTH, "found")
                break

        if month_object is None:
            print("Month", RESERVATION_MONTH, "not found. Ending search")
            return False

        for day in month_object.find_elements(By.CSS_SELECTOR, "button.ConsumerCalendar-day.is-in-month.is-available"):
            span = day.find_element(By.CSS_SELECTOR, "span")
            print("Encountered day: " + span.text)
            if span.text in RESERVATION_DAYS:
                print("Day %s found. Clicking button" % span.text)
                day.click()

                if self.search_time():
                    print("Time found")
                    return True

        return False

    def search_time(self):
        for item in self.driver.find_elements(By.CSS_SELECTOR, "button.Consumer-resultsListItem.is-available"):
            span = item.find_element(By.CSS_SELECTOR, "span.Consumer-resultsListItemTime")
            span2 = span.find_element(By.CSS_SELECTOR, "span")
            print("Encountered time", span2.text)

            available_time = datetime.strptime(span2.text, RESERVATION_TIME_FORMAT)
            if RESERVATION_TIME_MIN <= available_time <= RESERVATION_TIME_MAX:
                print("Time %s found. Clicking button" % span2.text)
                item.click()
                return True

        return False


def run_reservation():
    r = reserveOnTock()
    r.reserve()
    r.teardown()


def execute_reservations():
    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=run_reservation)
        threads.append(t)
        t.start()
        time.sleep(THREAD_DELAY_SEC)

    for t in threads:
        t.join()


def continuous_reservations():
    while True:
        execute_reservations()
        

if __name__ == '__main__':
    load_configuration_from_json()
    continuous_reservations()