from datetime import datetime
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

class Reservation:
    def __init__(self):
        self.reservation_days = None
        self.reservation_month = None
        self.reservation_year = None
        self.reservation_size = None
        self.today_date = None
        self.experience = None
        self.earliest_time = None
        self.latest_time = None
        self.reservation_time_format = "%I:%M %p"
        self.reservation_time_min = None
        self.reservation_time_max = None
        self.restaurant = None
        self.num_threads = 1
        self.thread_delay_sec = 1
        self.reservation_found = False
        self.enable_proxy = False
        self.user_data_dir = '~/Library/Application Support/Google/Chrome'
        self.profile_dir = 'Default'
        self.extension_path = self.user_data_dir + '/' + self.profile_dir + \
            '/Extensions/efohiadmkaogdhibjbmeppjpebenaool/1.149.316_0'
        self.browser_close_delay_sec = 600
        self.webdriver_timeout_delay_ms = 120000
        self.refresh_delay_msec = 500
        options = Options()
        self.driver = webdriver.Chrome(options=options)

    def load_json(self):
        file_path = './reservation_details.json'
        # Load data from JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Extract variables
        self.reservation_days = data['reservation-days']
        self.reservation_month = data['reservation-month']
        self.reservation_year = data['reservation-year']
        self.reservation_size = data['reservation-size']
        self.today_date = data['date-today']
        self.experience = data['experience']
        self.earliest_time = data['earliest-time']
        self.latest_time = data['latest-time']
        self.reservation_time_format = "%I:%M %p"
        self.reservation_time_min = datetime.strptime(
            self.earliest_time, self.reservation_time_format)
        self.reservation_time_max = datetime.strptime(
            self.latest_time, self.reservation_time_format)
        self.restaurant = data['restaurant']

    def teardown(self):
        self.driver.quit()

    def reserve(self):
        print("Looking for availability on month: %s, days: %s, between times: %s and %s" % (
            self.reservation_month, self.reservation_days, self.earliest_time, self.latest_time))

        while not self.reservation_found:
            time.sleep(self.refresh_delay_msec / 1000)
            url = f"https://www.exploretock.com/{self.restaurant}/experience/402750/{self.experience}?date=2024-{self.reservation_month}-{self.today_date}&size={self.reservation_size}&time=12%3A00"
            self.driver.get(url)
            WebDriverWait(self.driver, self.webdriver_timeout_delay_ms).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div.ConsumerCalendar-month")))

            if not self.search_month():
                print("No available days found. Continuing next search iteration")
                continue

            WebDriverWait(self.driver, self.webdriver_timeout_delay_ms).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='booking-card-collapse-header']")))

            print(
                "Found availability. Sleeping for 10 minutes to complete reservation...")
            self.reservation_found = True
            time.sleep(self.browser_close_delay_sec)

    def search_time(self):
        for item in self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='booking-card-collapse-header']"):
            span = item.find_element(
                By.CSS_SELECTOR, "span.Consumer-resultsListItemTime")
            span2 = span.find_element(By.CSS_SELECTOR, "span")
            print("Encountered time", span2.text)

            available_time = datetime.strptime(
                span2.text, self.reservation_time_format)
            if self.reservation_time_min <= available_time <= self.reservation_time_max:
                print("Time %s found. Clicking button" % span2.text)
                item.click()
                return True

        return False

    def search_month(self):
            month_object = None

            for month in self.driver.find_elements(By.CSS_SELECTOR, "div.ConsumerCalendar-month"):
                header = month.find_element(By.CSS_SELECTOR, "div.ConsumerCalendar-monthHeading")
                span = header.find_element(By.CSS_SELECTOR, "span")
                print("Encountered month", span.text)

                if self.reservation_month in span.text:
                    month_object = month
                    print("Month", self.reservation_month, "found")
                    break

            if month_object is None:
                print("Month", self.reservation_month, "not found. Ending search")
                return False

            for day in month_object.find_elements(By.CSS_SELECTOR, "button.ConsumerCalendar-day.is-in-month.is-available"):
                span = day.find_element(By.CSS_SELECTOR, "span")
                print("Encountered day: " + span.text)
                if span.text in self.reservation_days:
                    print("Day %s found. Clicking button" % span.text)
                    day.click()

                    if self.search_time():
                        print("Time found")
                        return True

            return False