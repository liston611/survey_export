from arcgis.gis import GIS
from functions_export_multithread import execute_download, execute_upload, execute_delete, execute_delete_all
import os


# client ID from the registered application
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')
client_id = config['DEFAULT']['CLIENT_ID']

# The URL of your ArcGIS Online organization
org_url = 'https://martaonline.maps.arcgis.com'

# Get the OAuth token
print("Opening browser to obtain an OAuth token...")
gis = GIS(org_url, client_id=client_id, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
print("Sign in completed.")

max_work = 15 #default value to populate


import tkinter as tk
from tkinter import ttk, filedialog

def ini_download():
    item_id = item_id_entry.get()
    item = gis.content.get(item_id)
    base_path = path_entry.get()
    comp_path = f'{base_path}\\working'
    max_work = int(workers_entry.get())
    execute_download(item, base_path, comp_path, max_work)


def ini_upload():
    item_id = item_id_entry.get()
    item = gis.content.get(item_id)
    base_path = path_entry.get()
    comp_path = f'{base_path}\\working'
    max_work = int(workers_entry.get())
    execute_upload(item, comp_path, max_work)


def ini_delete():
    item_id = item_id_entry.get()
    item = gis.content.get(item_id)
    base_path = path_entry.get()
    max_work = int(workers_entry.get())
    execute_delete(item, base_path, max_work)


def ini_delete_all():
    item_id = item_id_entry.get()
    item = gis.content.get(item_id)
    base_path = path_entry.get()
    max_work = int(workers_entry.get())
    execute_delete_all(item, base_path, max_work)


def on_entry_click(event): #Function to be called when the entry is clicked
    if item_id_entry.get() == placeholder_text:
        item_id_entry.delete(0, "end")  # Delete all the text in the entry
        item_id_entry.insert(0, '')  # Insert blank for user input
        item_id_entry.config(foreground='black')


def on_focusout(event): # Function to be called when the entry loses focus
    if item_id_entry.get() == '':
        item_id_entry.insert(0, placeholder_text)
        item_id_entry.config(foreground='grey')


def browse_directory():
    initial_dir = os.path.dirname(os.path.realpath(__file__))  # Get the script's directory
    directory = filedialog.askdirectory(initialdir=initial_dir)  # Set the initial directory
    if directory:  # If the user didn't cancel the dialog
        directory = directory.replace('/', '\\')
        path_entry.delete(0, tk.END)
        path_entry.insert(0, directory)



# Initialize the main window
root = tk.Tk()
root.title("ArcGIS Backup Tool")

# Set the window size
root.geometry('350x250')

placeholder_text = 'Enter layer ID:'

# Create an Entry widget for item_id, initialized with item_id
item_id_entry = ttk.Entry(root, width=40)
item_id_entry.insert(0, placeholder_text)
item_id_entry.config(foreground='grey')
item_id_entry.bind("<FocusIn>", on_entry_click)
item_id_entry.bind("<FocusOut>", on_focusout)
item_id_entry.grid(row=0,column=0, columnspan=3, pady=10, padx=10)

path_label = ttk.Label(root, text="Enter Folder:")
path_label.grid(row=1, column=0, pady=(10,0))  # Adjust padding as needed

# Create an Entry widget for folder directory
path_entry = ttk.Entry(root)
path_entry.grid(row=1, column=1,pady=5)

# Browse Button
browse_button = ttk.Button(root, text="Browse...", command=browse_directory)
browse_button.grid(row=1, column=2,pady=5)

workers_label = ttk.Label(root, text="Max Workers:")
workers_label.grid(row=2, column=0, pady=(10,0))  # Adjust padding as needed

# Create an Entry widget for max_work, initialized with max_work
workers_entry = ttk.Entry(root)
workers_entry.insert(0, max_work)  # Pre-fill the Entry with max_work
workers_entry.grid(row=2, column=1,pady=5)

# Create and place the "Download" button
download_button = ttk.Button(root, text="Download/Compress Pics", command=ini_download)
download_button.grid(row=3, column=0, columnspan= 2, pady=(10,0))  # Add some vertical padding

# Create and place the "Upload" button
upload_button = ttk.Button(root, text="Upload Compressed Pics", command=ini_upload)
upload_button.grid(row=4, column=0, columnspan= 2, pady=(10,0))  # Add some vertical padding

# Create and place the "Delete" button
delete_button = ttk.Button(root, text="Safe Delete Full-Res (leave compressed)", command=ini_delete)
delete_button.grid(row=5, column=0, columnspan= 2, pady=(10,0))  # Add some vertical padding

# Create and place the "Delete All" button
delete_all_button = ttk.Button(root, text="Safe Delete All Hosted (including compressed)", command=ini_delete_all)
delete_all_button.grid(row=6, column=0, columnspan= 2, pady=(10,0))  # Add some vertical padding

# Start the GUI event loop
root.mainloop()