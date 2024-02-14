from arcgis.gis import GIS
import re
import os
import pandas as pd
from PIL import Image, ExifTags
from concurrent.futures import ThreadPoolExecutor, as_completed


# Compress image
def compress_img(file_path, file_path_comp, quality = 65):
    image = Image.open(file_path)

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # Attempt to get the image's orientation from its EXIF data
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break
        exif = dict(image._getexif().items())
        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # Cases: image doesn't have getexif
        pass

    width, height = image.size
    new_size = (width//2, height//2)
    resized_image = image.resize(new_size)
    
    resized_image.save(file_path_comp, quality = quality, optimize=True)
    print(f"Compressed photo saved at {file_path_comp}")

def gen_name(feature, attachment):
    object_id = feature.attributes['OBJECTID']
    try:
        creation_date = pd.to_datetime(feature.attributes['inprogressdate'], unit='ms')
    except:
        creation_date = pd.to_datetime(feature.attributes['inProgressDate'], unit='ms')
    
    try:
        date_str = creation_date.strftime('%m%d%y-%H%M')
    except:
        creation_date = pd.to_datetime(feature.attributes['CreationDate'], unit='ms')
        date_str = creation_date.strftime('%m%d%y-%H%M')
    try:
        wrkordr = str(feature.attributes['workorderid'])
    except:
        wrkordr = str(feature.attributes['workOrderId'])
    if wrkordr == '':
        wrkordr = 'BLANK'
    stop_abbr = str(feature.attributes['location'][:6])
    if len(stop_abbr) == 6:
        try:
            if len(str(int(stop_abbr))) != 6: stop_abbr = 'OTHER_'
        except:
            stop_abbr = 'OTHER_'
    else:
        stop_abbr = 'OTHER_'

    attachment_id = attachment['id']
    attachment_name = attachment['name']
    _, attachment_type = os.path.splitext(attachment_name)
    file_name = f"{stop_abbr}_{date_str}_{wrkordr}_OID{object_id}_{attachment_id}{attachment_type}"
    file_name_comp = f"{stop_abbr}_{date_str}_{wrkordr}_OID{object_id}_{attachment_id}_comp{attachment_type}"

    return [file_name, file_name_comp, stop_abbr]

# for feature in features:
def download_and_rename_attachment(feature_layer, feature, attachment, base_path, comp_path):
    object_id = feature.attributes['OBJECTID']
    
    file_name, file_name_comp, stop_abbr = gen_name(feature, attachment)

    folder_path = os.path.join(base_path, stop_abbr)
    folder_path_comp = os.path.join(comp_path, stop_abbr)
    os.makedirs(folder_path, exist_ok=True)

    attachment_id = attachment['id']
    attachment_name = attachment['name']
    file_str, attachment_type = os.path.splitext(attachment_name)
    file_path = os.path.join(folder_path, file_name)
    file_path_comp = os.path.join(folder_path_comp, file_name_comp)
    
    # Download the attachment
    if not file_str[len(file_str)-5:] == '_comp':
        if not os.path.exists(file_path):
            feature_layer.attachments.download(oid=object_id, attachment_id=attachment_id, save_path=folder_path)
            os.rename(os.path.join(folder_path, attachment_name), file_path)
            print(f"Photo {file_name} saved at {folder_path}")

        # Save compressed
        if not os.path.exists(file_path_comp) and attachment_type in ['.jpg', '.jpeg', '.png', '.gif']:
            os.makedirs(folder_path_comp, exist_ok=True)
            compress_img(file_path, file_path_comp)


def upload_compressed(feature_layer, feature, attachment, comp_path):
    # iterate features
    ## find feature OBJECTID
    object_id = feature.attributes['OBJECTID']

    _, file_name_comp, stop_abbr = gen_name(feature, attachment)

    attachments = feature_layer.attachments.get_list(oid=object_id)
    attachments_names = [attachment['name'] for attachment in attachments]

    file_path_comp = os.path.join(comp_path, stop_abbr)

    for _, _, filenames in os.walk(file_path_comp, topdown=False):
         for filename in filenames:
             if (not filename in attachments_names) and filename == file_name_comp:
                 feature_layer.attachments.add(oid=object_id, file_path = os.path.join(file_path_comp,filename))
                 print(f"Photo {filename} uploaded at {file_path_comp}")


def delete_fullres(feature_layer, feature, attachment, base_path, mode = True):
    object_id = feature.attributes['OBJECTID']
    
    file_name, _, stop_abbr = gen_name(feature, attachment)

    folder_path = os.path.join(base_path, stop_abbr)
    os.makedirs(folder_path, exist_ok=True)

    attachment_id = attachment['id']
    attachment_name = attachment['name']
    file_str, _ = os.path.splitext(attachment_name)
    file_path = os.path.join(folder_path, file_name)
    
    # Delete the attachment
    if not file_str[len(file_str)-5:] == '_comp' and mode:
        if os.path.exists(file_path):
            if attachment['size'] == os.path.getsize(file_path):
                feature_layer.attachments.delete(oid=object_id, attachment_id=attachment_id)
                print(f"Photo {attachment_name} deleted")
            else:
                print(f"Bus Stop {file_str} is a different file size. Attachment size: {attachment['size']} Downloaded: {os.path.getsize(file_path)}")
        else:
            print(f"Bus Stop {file_str} photo does not exist on drive: {file_path}")
    elif not mode:
        if os.path.exists(file_path):
            if attachment['size'] == os.path.getsize(file_path):
                feature_layer.attachments.delete(oid=object_id, attachment_id=attachment_id)
                print(f"Photo {attachment_name} deleted")
            else:
                print(f"Bus Stop {file_str} is a different file size. Attachment size: {attachment['size']} Downloaded: {os.path.getsize(file_path)}")
        elif file_str[len(file_str)-5:] == '_comp':
            feature_layer.attachments.delete(oid=object_id, attachment_id=attachment_id)
            print(f"Photo {attachment_name} deleted")
        else:
            print(f"Bus Stop {file_str} photo does not exist on drive: {file_path}")
    

# Use ThreadPoolExecutor to download attachments in parallel
def execute_download():
    item_id = item_id_entry.get()
    item = gis.content.get(item_id)
    feature_layer = item.layers[0]  # Assuming it's the first layer
    # Query the feature layer for records
    features = feature_layer.query(where="1=1", out_fields="*", return_attachments=False).features
    
    max_work = int(workers_entry.get())
    with ThreadPoolExecutor(max_workers=max_work) as executor:
        # Store future tasks
        future_to_attachment = {executor.submit(
            download_and_rename_attachment, feature_layer, feature, attachment, 
            base_path, comp_path): (feature, attachment)
                                for feature in features for attachment in feature_layer.attachments.get_list(
                                    oid=feature.attributes['OBJECTID'])}
        # Process completed futures
        for future in as_completed(future_to_attachment):
            future.result()  # You can handle exceptions here or get the result
    print('Download/Compress Complete')


def execute_upload():
    item_id = item_id_entry.get()
    item = gis.content.get(item_id)
    feature_layer = item.layers[0]  # Assuming it's the first layer
    # Query the feature layer for records
    features = feature_layer.query(where="1=1", out_fields="*", return_attachments=False).features

    max_work = int(workers_entry.get())
    with ThreadPoolExecutor(max_workers=max_work) as executor:
        # Store future tasks
        future_to_attachment = {executor.submit(
            upload_compressed, feature_layer, feature, attachment, 
            comp_path): (feature, attachment)
                                for feature in features for attachment in feature_layer.attachments.get_list(
                                    oid=feature.attributes['OBJECTID'])}
        # Process completed futures
        for future in as_completed(future_to_attachment):
            future.result()  # You can handle exceptions here or get the result
    print('Upload Complete')


def execute_delete(mode = True):
    item_id = item_id_entry.get()
    item = gis.content.get(item_id)
    feature_layer = item.layers[0]  # Assuming it's the first layer
    # Query the feature layer for records
    features = feature_layer.query(where="1=1", out_fields="*", return_attachments=False).features

    max_work = int(workers_entry.get())
    with ThreadPoolExecutor(max_workers=max_work) as executor:
        # Store future tasks
        future_to_attachment = {executor.submit(
            delete_fullres, feature_layer, feature, attachment, 
            base_path, mode): (feature, attachment)
                                for feature in features for attachment in feature_layer.attachments.get_list(
                                    oid=feature.attributes['OBJECTID'])}
        # Process completed futures
        for future in as_completed(future_to_attachment):
            future.result()  # You can handle exceptions here or get the result
    print('Deletion Complete')

def execute_delete_all():
    execute_delete(mode=False)
    return

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

item_id = ''
max_work = 10

# Define base path for saving photos
base_path = 'HEAT'
comp_path = 'HEAT\\working'

import tkinter as tk
from tkinter import ttk

# Initialize the main window
root = tk.Tk()
root.title("ArcGIS Operations")

# Set the window size
root.geometry('300x325')

item_id_label = ttk.Label(root, text="Item ID:")
item_id_label.pack(pady=(10,0))  # Adjust padding as needed

# Create an Entry widget for item_id, initialized with item_id
item_id_entry = ttk.Entry(root)
item_id_entry.insert(0, item_id)  # Pre-fill the Entry with item_id
item_id_entry.pack(fill = 'x', pady=5)

workers_label = ttk.Label(root, text="Max Workers:")
workers_label.pack(pady=(10,0))  # Adjust padding as needed

# Create an Entry widget for max_work, initialized with max_work
workers_entry = ttk.Entry(root)
workers_entry.insert(0, max_work)  # Pre-fill the Entry with max_work
workers_entry.pack(pady=5)

# Create and place the "Download" button
download_button = ttk.Button(root, text="Download/Compress Pics", command=execute_download)
download_button.pack(pady=10)  # Add some vertical padding

# Create and place the "Upload" button
upload_button = ttk.Button(root, text="Upload Compressed Pics", command=execute_upload)
upload_button.pack(pady=10)  # Add some vertical padding

# Create and place the "Delete" button
delete_button = ttk.Button(root, text="Safe Delete Full-Res (leave compressed)", command=execute_delete)
delete_button.pack(pady=10)  # Add some vertical padding

# Create and place the "Delete All" button
delete_all_button = ttk.Button(root, text="Safe Delete All Hosted (including compressed)", command=execute_delete_all)
delete_all_button.pack(pady=10)  # Add some vertical padding

# Start the GUI event loop
root.mainloop()