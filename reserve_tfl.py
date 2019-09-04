import json
import pytest
import time
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import ProxyType, Proxy
from selenium.webdriver.chrome.options import Options

# Login not required for Tock. Leave it as false to decrease reservation delay
ENABLE_LOGIN = False
TOCK_USERNAME = "SET_YOUR_USER_NAME_HERE"
TOCK_PASSWORD = "SET_YOUR_PASSWORD_HERE"

# Set your specific reservation month and days
RESERVATION_MONTH = 'November'
RESERVATION_DAYS = ['1','2','8','9','15','16','22','23']
RESERVATION_TIME_FORMAT = "%I:%M %p"

# Set the time range for acceptable reservation times. I.e., any available slots between 5:00 PM and 8:30 PM
RESERVATION_TIME_MIN = datetime.strptime("5:00 PM", RESERVATION_TIME_FORMAT)
RESERVATION_TIME_MAX = datetime.strptime("8:30 PM", RESERVATION_TIME_FORMAT)

# Set the party size for the reservation
RESERVATION_SIZE = 2

# Multithreading configurations
NUM_THREADS = 1
THREAD_DELAY_SEC = 1
RESERVATION_FOUND = False

# Time between each page refresh in milliseconds. Decrease this time to increase the number of reservation attempts
REFRESH_DELAY_MSEC = 1000

# Chrome extension configurations that are used with Luminati.io proxy. Enable proxy to avoid getting IP banned.
ENABLE_PROXY = False
USER_DATA_DIR = '~/Library/Application Support/Google/Chrome'
PROFILE_DIR = 'Default'
# https://chrome.google.com/webstore/detail/luminati/efohiadmkaogdhibjbmeppjpebenaool
EXTENSION_PATH = USER_DATA_DIR + '/' + PROFILE_DIR + '/Extensions/efohiadmkaogdhibjbmeppjpebenaool/1.149.316_0'

# Delay for how long the browser remains open so that the reservation can be finalized
BROWSER_CLOSE_DELAY_SEC = 600

MONTH_NUM = {
    'january': 1,
    'february': 2,
    'march': 3,
    'april': 4,
    'may': 5,
    'june': 6,
    'july': 7,
    'august': 8,
    'september': 9,
    'october': 10,
    'november': 11,
    'december': 12
}


class ReserveTFL():
    def setup(self):
        options = Options()
        if ENABLE_PROXY:
            options.add_argument('--load-extension={}'.format(EXTENSION_PATH))
            options.add_argument('--user-data-dir={}'.format(USER_DATA_DIR))
            options.add_argument('--profile-directory=Default')

        self.driver = webdriver.Chrome(options=options)
        self.vars = {}

    def teardown(self):
        self.driver.quit()

    def reserve(self):
        global RESERVATION_FOUND
        print("Looking for availability on month: %s, days: %s, between times: %s and %s" % (RESERVATION_MONTH, RESERVATION_DAYS, RESERVATION_TIME_MIN, RESERVATION_TIME_MAX))

        if ENABLE_LOGIN:
            self.login_tock()

        while True and RESERVATION_FOUND == False:
            time.sleep(REFRESH_DELAY_MSEC / 1000)
            self.driver.get("https://www.exploretock.com/tfl/search?date=2019-%s-02&size=%s&time=%s" % (month_num(RESERVATION_MONTH), RESERVATION_SIZE, "22%3A00"))
            WebDriverWait(self.driver, 3000).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div.ConsumerCalendar-month")))

            monthObject = None

            if not self.search_month():
                print("No available days found. Continuing next search iteration")
                continue

            WebDriverWait(self.driver, 3000).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "button.Consumer-resultsListItem.is-available")))

            if not self.search_time():
                print("Time not found. Continuing next search iteration")
                continue

            print("Found availability. Sleeping for 10 minutes to complete reservation...")
            RESERVATION_FOUND = True
            time.sleep(BROWSER_CLOSE_DELAY_SEC)

    def login_tock(self):
        self.driver.get("https://www.exploretock.com/tfl/login")
        WebDriverWait(self.driver, 10000).until(expected_conditions.presence_of_element_located((By.NAME, "email")))
        self.driver.find_element(By.NAME, "email").send_keys(TOCK_USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(TOCK_PASSWORD)
        self.driver.find_element(By.CSS_SELECTOR, ".Button").click()
        WebDriverWait(self.driver, 3000).until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, ".MainHeader-accountName")))

    def search_month(self):
        for month in self.driver.find_elements(By.CSS_SELECTOR, "div.ConsumerCalendar-month"):
            header = month.find_element(By.CSS_SELECTOR, "div.ConsumerCalendar-monthHeading")
            span = header.find_element(By.CSS_SELECTOR, "span.H1")
            print("Encountered month", span.text)

            if RESERVATION_MONTH in span.text:
                monthObject = month
                print("Month", RESERVATION_MONTH, "found")
                break

        if monthObject == None:
            print("Month", RESERVATION_MONTH, "not found. Ending search")
            return False

        found = False
        for day in monthObject.find_elements(By.CSS_SELECTOR, "button.ConsumerCalendar-day.is-in-month.is-available"):
            span = day.find_element(By.CSS_SELECTOR, "span.B2")
            print("Encountered day: " + span.text)
            if span.text in RESERVATION_DAYS:
                found = True
                print("Day %s found. Clicking button" % span.text)
                day.click()
                return True

        return False

    def search_time(self):
        for item in self.driver.find_elements(By.CSS_SELECTOR, "button.Consumer-resultsListItem.is-available"):
            span = item.find_element(By.CSS_SELECTOR, "span.Consumer-resultsListItemTime")
            span2 = span.find_element(By.CSS_SELECTOR, "span.B2")
            span3 = span2.find_element(By.CSS_SELECTOR, "span")
            print("Encountered time", span3.text)

            availableTime = datetime.strptime(span3.text, RESERVATION_TIME_FORMAT)
            if RESERVATION_TIME_MIN <= availableTime <= RESERVATION_TIME_MAX:
                print("Time %s found. Clicking button" % span3.text)
                item.click()
                return True

        return False


def month_num(month):
    # TODO error handling
    return MONTH_NUM[month.lower()]


def run_reservation():
    t = ReserveTFL()
    t.setup()
    t.reserve()
    t.teardown()


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
