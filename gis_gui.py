max_work = 10

# Define base path for saving photos
base_path = 'HEAT'
comp_path = 'HEAT\\working'

import tkinter as tk
from tkinter import ttk

def on_entry_click(event):
    """Function to be called when the entry is clicked."""
    if item_id_entry.get() == placeholder_text:
        item_id_entry.delete(0, "end")  # Delete all the text in the entry
        item_id_entry.insert(0, '')  # Insert blank for user input
        item_id_entry.config(foreground='black')

def on_focusout(event):
    """Function to be called when the entry loses focus."""
    if item_id_entry.get() == '':
        item_id_entry.insert(0, placeholder_text)
        item_id_entry.config(foreground='grey')

# Initialize the main window
root = tk.Tk()
root.title("ArcGIS Operations")

# Set the window size
root.geometry('300x325')

placeholder_text = 'Enter layer ID:'

# Create an Entry widget for item_id, initialized with item_id
item_id_entry = ttk.Entry(root, width=50)
item_id_entry.insert(0, placeholder_text)
item_id_entry.config(foreground='grey')
item_id_entry.bind("<FocusIn>", on_entry_click)
item_id_entry.bind("<FocusOut>", on_focusout)
item_id_entry.grid(row=0,column=0, columnspan=2, pady=10, padx=10)

radio_label = ttk.Label(root, text="Abbr Column:")
radio_label.grid(row=1, column=0, pady=(10,0), rowspan=2)  # Adjust padding as needed

# Create a BooleanVar to store the True/False value
bool_var = tk.BooleanVar()
bool_var.set(True)  # You can set a default value as True or False

# Create Radio buttons for True/False selection
radio_true = ttk.Radiobutton(root, text="Location", variable=bool_var, value=True)
radio_true.grid(row=1, column=1, sticky=tk.W)

radio_false = ttk.Radiobutton(root, text="Description", variable=bool_var, value=False)
radio_false.grid(row=2, column=1, sticky=tk.W)

workers_label = ttk.Label(root, text="Max Workers:")
workers_label.grid(row=3, column=0, pady=(10,0))  # Adjust padding as needed

# Create an Entry widget for max_work, initialized with max_work
workers_entry = ttk.Entry(root)
workers_entry.insert(0, max_work)  # Pre-fill the Entry with max_work
workers_entry.grid(row=3, column=1,pady=5)

# Create and place the "Download" button
download_button = ttk.Button(root, text="Download/Compress Pics", command=execute_download)
download_button.grid(row=4, column=0, columnspan= 2, pady=(10,0))  # Add some vertical padding

# Create and place the "Upload" button
upload_button = ttk.Button(root, text="Upload Compressed Pics", command=execute_upload)
upload_button.grid(row=5, column=0, columnspan= 2, pady=(10,0))  # Add some vertical padding

# Create and place the "Delete" button
delete_button = ttk.Button(root, text="Safe Delete Full-Res (leave compressed)", command=execute_delete)
delete_button.grid(row=6, column=0, columnspan= 2, pady=(10,0))  # Add some vertical padding

# Create and place the "Delete All" button
delete_all_button = ttk.Button(root, text="Safe Delete All Hosted (including compressed)", command=execute_delete_all)
delete_all_button.grid(row=7, column=0, columnspan= 2, pady=(10,0))  # Add some vertical padding

# Start the GUI event loop
root.mainloop()