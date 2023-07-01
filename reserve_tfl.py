import threading
import time

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options

# Login not required for Tock. Leave it as false to decrease reservation delay
ENABLE_LOGIN = True
TOCK_USERNAME = "your_email"
TOCK_PASSWORD = "your_password"

# The name of the restaurant as shown in tock urls ex "https://www.exploretock.com/hayato"
RESTAURANT = 'hayato'

# Set your specific reservation month and days
RESERVATION_MONTH = 'August'
RESERVATION_DAYS = ['5', '6', '26' '27']
RESERVATION_YEAR = '2023'
RESERVATION_TIME_FORMAT = "%I:%M %p"

# Set the time range for acceptable reservation times.
# I.e., any available slots between 5:00 PM and 8:30 PM
EARLIEST_TIME = "5:00 PM"
LATEST_TIME = "10:00 PM"
RESERVATION_TIME_MIN = datetime.strptime(EARLIEST_TIME, RESERVATION_TIME_FORMAT)
RESERVATION_TIME_MAX = datetime.strptime(LATEST_TIME, RESERVATION_TIME_FORMAT)

# Set the party size for the reservation
RESERVATION_SIZE = 2

# Multithreading configurations
NUM_THREADS = 1
THREAD_DELAY_SEC = 1
RESERVATION_FOUND = False

# Time between each page refresh in milliseconds. Decrease this time to
# increase the number of reservation attempts
REFRESH_DELAY_MSEC = 200

# Chrome extension configurations that are used with Luminati.io proxy (now called Bright Data).
# Enable proxy to avoid getting IP potentially banned. This should be enabled only if the REFRESH_DELAY_MSEC
# is extremely low (sub hundred) and NUM_THREADS > 1.
ENABLE_PROXY = False
# This is formatted for windows -> either way this should be the path to your google chrome profile directory
USER_DATA_DIR = 'C:/Users/your_username/AppData/Local/Google/Chrome/User Data/'
PROFILE_DIR = 'Default'
# https://chrome.google.com/webstore/detail/luminati/efohiadmkaogdhibjbmeppjpebenaool
# Chrome extension for Luminati/Bright Data
EXTENSION_PATH = USER_DATA_DIR + '/' + PROFILE_DIR + '/Extensions/efohiadmkaogdhibjbmeppjpebenaool/1.370.148_0'

# Delay for how long the browser remains open so that the reservation can be finalized. Tock holds the reservation
# for 10 minutes before releasing.
BROWSER_CLOSE_DELAY_SEC = 600

WEBDRIVER_TIMEOUT_DELAY_MS = 3000

MONTH_NUM = {
    'january':   '01',
    'february':  '02',
    'march':     '03',
    'april':     '04',
    'may':       '05',
    'june':      '06',
    'july':      '07',
    'august':    '08',
    'september': '09',
    'october':   '10',
    'november':  '11',
    'december':  '12'
}



class ReserveTFL():
    def __init__(self):
        options = webdriver.ChromeOptions()
        if ENABLE_PROXY:
            options.add_argument('--load-extension=' + EXTENSION_PATH)
            options.add_argument('--user-data-dir=' + USER_DATA_DIR)
            options.add_argument('--profile-directory=Default')

        self.driver = webdriver.Chrome(options=options)

    def teardown(self):
        self.driver.quit()

    def reserve(self):
        global RESERVATION_FOUND
        print("Looking for availability on month: %s, days: %s, between times: %s and %s" % (RESERVATION_MONTH, RESERVATION_DAYS, EARLIEST_TIME, LATEST_TIME))

        if ENABLE_LOGIN:
            self.login_tock()

        while not RESERVATION_FOUND:
            time.sleep(REFRESH_DELAY_MSEC / 1000)
            self.driver.get("https://www.exploretock.com/" + RESTAURANT + "/search?date=%s-%s-02&size=%s&time=%s" % (RESERVATION_YEAR, month_num(RESERVATION_MONTH), RESERVATION_SIZE, "22%3A00"))
            WebDriverWait(self.driver, WEBDRIVER_TIMEOUT_DELAY_MS).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div.ConsumerCalendar-month")))

            if not self.search_month():
                print("No available days found. Continuing next search iteration")
                continue

            WebDriverWait(self.driver, WEBDRIVER_TIMEOUT_DELAY_MS).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "button.Consumer-resultsListItem.is-available")))

            print("Found availability. Sleeping for 10 minutes to complete reservation...")
            RESERVATION_FOUND = True
            time.sleep(BROWSER_CLOSE_DELAY_SEC)

    def login_tock(self):
        self.driver.get("https://www.exploretock.com/" + RESTAURANT + "/login")
        WebDriverWait(self.driver, WEBDRIVER_TIMEOUT_DELAY_MS).until(expected_conditions.presence_of_element_located((By.NAME, "email")))
        self.driver.find_element(By.NAME, "email").send_keys(TOCK_USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(TOCK_PASSWORD)
        # Old css selector no longer working
        self.driver.find_element(By.CSS_SELECTOR, ".MuiButton-fullWidth").click()
        # Checks for profile image css selector -> maybe not the best check but it works
        WebDriverWait(self.driver, WEBDRIVER_TIMEOUT_DELAY_MS).until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, ".css-118lam2")))

    def search_month(self):
        month_object = None

        for month in self.driver.find_elements(By.CSS_SELECTOR, "div.ConsumerCalendar-month"):
            header = month.find_element(By.CSS_SELECTOR, "div.ConsumerCalendar-monthHeading")
            span = header.find_element(By.CSS_SELECTOR, "span.H1")
            print("Encountered month", span.text)

            if RESERVATION_MONTH in span.text:
                month_object = month
                print("Month", RESERVATION_MONTH, "found")
                break

        if month_object is None:
            print("Month", RESERVATION_MONTH, "not found. Ending search")
            return False

        for day in month_object.find_elements(By.CSS_SELECTOR, "button.ConsumerCalendar-day.is-in-month.is-available"):
            span = day.find_element(By.CSS_SELECTOR, "span.B2")
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


def month_num(month):
    # TODO error handling
    return MONTH_NUM[month.lower()]


def run_reservation():
    r = ReserveTFL()
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


continuous_reservations()
