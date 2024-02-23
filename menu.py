import tkinter as tk
from tkinter import ttk
import json
import subprocess
import reserve_tfl

# Function to save data to JSON and call another script
def save_data_and_call_script(data):
    with open("reservation_details.json", "w") as json_file:
        json.dump(data, json_file, indent=4)
    subprocess.run(['python', 'path_to_second_script.py'])  # Adjust script name/path as needed

# Function to show confirmation modal
def show_confirmation_modal(data):
    modal = tk.Toplevel(root)
    modal.title("Confirm Details")
    modal.geometry("400x400")  

    # Display the data for confirmation
    for i, (key, value) in enumerate(data.items()):
        ttk.Label(modal, text=f"{key.replace('-', ' ').title()}: {value}").grid(column=0, row=i, sticky=tk.W, padx=5, pady=2)

    def on_confirm():
        modal.destroy()
        reserve_tfl.continuous_reservations() 

    def on_cancel():
        modal.destroy()  

    # Confirm and Cancel buttons
    ttk.Button(modal, text="Confirm", command=on_confirm).grid(column=0, row=len(data)+1, padx=5, pady=10, sticky=tk.W)
    ttk.Button(modal, text="Cancel", command=on_cancel).grid(column=1, row=len(data)+1, padx=5, pady=10, sticky=tk.E)

# Function to collect data from entries and show the confirmation modal
def write_to_json():
    data = {key: entry_widgets[key].get() for key in entry_widgets}
    show_confirmation_modal(data)

# Create the main window
root = tk.Tk()
root.title("Data Entry to JSON")

json_data = {
    "reservation-month": "02",
    "reservation-days": "25,26,27",
    "reservation-year": "2024",
    "date-today": "18",
    "earliest-time": "8:00 PM",
    "latest-time": "10:00 PM",
    "reservation-size": "2",
    "experience": "dining-room-reservations",
    "restaurant": "hong-shing-toronto"
}

entry_widgets = {}

# Dynamically create labels and entry widgets based on JSON keys
for i, key in enumerate(json_data):
    ttk.Label(root, text=f"{key.replace('-', ' ').title()}:").grid(column=0, row=i, sticky=tk.W, padx=5, pady=5)
    entry = ttk.Entry(root)
    entry.grid(column=1, row=i, sticky=tk.EW, padx=5, pady=5)
    entry.insert(0, json_data[key])  # Pre-fill with JSON data
    entry_widgets[key] = entry

submit_button = ttk.Button(root, text="Submit", command=write_to_json)
submit_button.grid(column=0, row=len(json_data), columnspan=2, sticky=tk.EW, padx=5, pady=10)

# Configure the grid layout column weights
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=3)

root.mainloop()
