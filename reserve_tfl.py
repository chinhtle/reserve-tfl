import threading
import time

from reservation import Reservation

def run_reservation(reservation:Reservation):
    reservation.reserve()
    reservation.teardown()

def execute_reservations(reservation:Reservation):
    threads = []
    for _ in range(reservation.num_threads):
        t = threading.Thread(target=run_reservation(reservation))
        threads.append(t)
        t.start()
        time.sleep(reservation.thread_delay_sec)

    for t in threads:
        t.join()

def continuous_reservations(reservation:Reservation):
    while True:
        execute_reservations(reservation)
        
if __name__ == '__main__':
    new_reservation = Reservation()
    new_reservation.load_json()
    continuous_reservations(new_reservation)