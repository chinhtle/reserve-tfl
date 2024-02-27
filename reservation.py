import datetime
import json


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
        self.extension_path = self.user_data_dir + '/' + self.profile_dir + '/Extensions/efohiadmkaogdhibjbmeppjpebenaool/1.149.316_0'
        self.browser_close_delay_sec = 600
        self.webdriver_timeout_delay_ms = 120000
        
        
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
        self.reservation_time_min = datetime.strptime(self.earliest_time, self.reservation_time_format)
        self.reservation_time_max = datetime.strptime(self.latest_time, self.reservation_time_format)
        self.restaurant = data['restaurant']
        