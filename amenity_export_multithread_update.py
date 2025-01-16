from arcgis.gis import GIS
import re
import requests
import os
import pandas as pd
from PIL import Image, ExifTags
from concurrent.futures import ThreadPoolExecutor, as_completed
import certifi
import urllib3

http = urllib3.PoolManager(
    cert_reqs="CERT_REQUIRED",
    ca_certs=certifi.where()
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def gen_name(feature, attachment = None):
    try: object_id = feature.attributes['objectid']
    except: object_id = feature.attributes['OBJECTID']

    creation_date = pd.to_datetime(feature.attributes['CreationDate'], unit='ms')
    date_str = creation_date.strftime('%m%d%y-%H%M')
    stop_abbr = str(feature.attributes['bus_stop_number']).strip()
    folder_path = os.path.join(base_path, stop_abbr)
    os.makedirs(folder_path, exist_ok=True)

    if attachment == None:
        attachment_id = ''
        attachment_type = ''
    else:
        attachment_id, attachment_name = attachment['id'], attachment['name']
        _, attachment_type = os.path.splitext(attachment_name)

    file_name = f"{stop_abbr}_{date_str}_OID{object_id}-{attachment_id}{attachment_type}"
    file_name_comp = f"{stop_abbr}_{date_str}_OID{object_id}-{attachment_id}_comp{attachment_type}"

    return [file_name, file_name_comp, stop_abbr]

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


# for feature in features:
def download_and_rename_attachment(feature, feature_layer, attachment, base_path, comp_path):
    try: object_id = feature.attributes['objectid']
    except: object_id = feature.attributes['OBJECTID']

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
        if not os.path.exists(file_path_comp):
            os.makedirs(folder_path_comp, exist_ok=True)
            compress_img(file_path, file_path_comp)


def upload_compressed(feature, feature_layer, comp_path):
    # iterate features
    ## find feature objectID
    try: object_id = feature.attributes['objectid']
    except: object_id = feature.attributes['OBJECTID']

    file_name, _, stop_abbr = gen_name(feature)

    try:
        attachments = feature_layer.attachments.get_list(oid=object_id)
        attachments_names = [attachment['name'] for attachment in attachments]
    except:
        attachments_names = ''

    file_path_comp = os.path.join(comp_path, stop_abbr)

    for dirpath, dirnames, filenames in os.walk(file_path_comp, topdown=False):
         for filename in filenames:
             if (not filename in attachments_names) and file_name in filename:
                try:
                    feature_layer.attachments.add(oid=object_id, file_path = os.path.join(file_path_comp,filename))
                    print(f"Photo {filename} uploaded from {file_path_comp}")
                # try:
                #     feature_layer.attachments.add(oid=object_id, file_path = os.path.join(file_path_comp,filename))
                except Exception as e:
                    print(f"Error uploading OID: {object_id} Filename: {filename} Comp path: {file_path_comp} \n Exception: {e}")
                print(f"Photo {filename} uploaded from {file_path_comp}")


def delete_fullres(feature, feature_layer, attachment, base_path, comp_path, mode=True):

    try: object_id = feature.attributes['objectid']
    except: object_id = feature.attributes['OBJECTID']

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
            else: print(f"Bus Stop {file_str} is a different file size. Attachment size: {attachment['size']} Downloaded: {os.path.getsize(file_path)}")
        else: print(f"Bus Stop {file_str} photo does not exist on drive: {file_path}")
    elif not mode:
        if os.path.exists(file_path):
            if attachment['size'] == os.path.getsize(file_path):
                feature_layer.attachments.delete(oid=object_id, attachment_id=attachment_id)
                print(f"Photo {attachment_name} deleted")
            else: print(f"Bus Stop {file_str} is a different file size. Attachment size: {attachment['size']} Downloaded: {os.path.getsize(file_path)}")
        elif file_str[len(file_str)-5:] == '_comp':
            feature_layer.attachments.delete(oid=object_id, attachment_id=attachment_id)
            print(f"Photo {attachment_name} deleted")
        else: print(f"Bus Stop {file_str} photo does not exist on drive: {file_path}") 
          
def check_comp(filename):
    base, ext = os.path.splitext(filename)
    # Check if the base ends with '_comp'
    return base.endswith('_comp')

# Use ThreadPoolExecutor to download attachments in parallel
def execute_download():
    feature_layer = item.layers[0]  # Assuming it's the first layer
    features = feature_layer.query(where="1=1", out_fields="*", return_attachments=False).features
    unique_parent_ids_list = filter_oid(feature_layer)

    with ThreadPoolExecutor(max_workers=36) as executor:
        future_to_attachment = {
            executor.submit(
                download_and_rename_attachment,
                feat,  # the feature
                feature_layer,
                attachment,  # the attachment
                base_path,
                comp_path
            ): (feat, attachment)
            for feat in features
            if feat.attributes['objectid'] in unique_parent_ids_list
            for attachment in feature_layer.attachments.get_list(
                oid=feat.attributes['objectid']
            )
        }
        # Process completed futures
        for future in as_completed(future_to_attachment):
            future.result()  # You can handle exceptions here or get the result


def execute_upload():
    feature_layer = item.layers[0]  # Assuming it's the first layer
    features = feature_layer.query(where="1=1", out_fields="*", return_attachments=False).features
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Store future tasks
        future_to_attachment = {executor.submit(
            upload_compressed, feature, feature_layer,
            comp_path): (feature)
                                for feature in features
                                }
        # Process completed futures
        for future in as_completed(future_to_attachment):
            try:
                future.result()  # You can handle exceptions here or get the result
            except Exception as e:
                # print(f"error uploading {future_to_attachment[future]}")
                print(f"Error: {e}")

def execute_delete():
    feature_layer = item.layers[0]  # Assuming it's the first layer
    features = feature_layer.query(where="1=1", out_fields="*", return_attachments=False).features
    unique_parent_ids_list = filter_oid(feature_layer)

    with ThreadPoolExecutor(max_workers=36) as executor:
        # Store future tasks
        future_to_attachment = {executor.submit(
            delete_fullres, feat, feature_layer, attachment, 
            base_path, comp_path
            ): (feat, attachment)
            for feat in features
            if feat.attributes['objectid'] in unique_parent_ids_list
            for attachment in feature_layer.attachments.get_list(
                oid=feat.attributes['objectid']
                )
            }
        # Process completed futures
        for future in as_completed(future_to_attachment):
            future.result()  # You can handle exceptions here or get the result


def filter_oid(feature_layer):
    df = feature_layer.attachments.search(as_df=True)
    base_names = df['NAME'].str.rsplit('.', n=1).str[0]
    ends_with_comp = base_names.str.endswith('_comp')
    mask = ~ends_with_comp
    unique_parent_ids = df.loc[mask, 'PARENTOBJECTID'].unique()
    unique_parent_ids_list = set(unique_parent_ids.tolist())
    
    return unique_parent_ids_list

# client ID from the registered application
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')
client_id = config['DEFAULT']['CLIENT_ID']
client_secret = config['DEFAULT']['CLIENT_SECRET']

# The URL of your ArcGIS Online organization
org_url = 'https://martaonline.maps.arcgis.com'

def get_token():
    config = ConfigParser()
    config.read('config_EP.ini')
    client_id = config['DEFAULT']['CLIENT_ID']
    client_secret = config['DEFAULT']['CLIENT_SECRET']
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': "client_credentials"
    }
    request = requests.get('https://www.arcgis.com/sharing/rest/oauth2/token',
                          params=params)
    response = request.json()
    token = response["access_token"]
    return token

token = get_token()

print("ArcGIS Online")
gis = GIS(org_url, token = token)
print("Logged in to " + gis.properties.portalName)

item_id = 'ec03593406114883a7a3f44858854629'
item = gis.content.get(item_id)


# Define base path for saving photos
base_path = 'amenities'
comp_path = 'amenities\\working'

import tkinter as tk
from tkinter import ttk

# Initialize the main window
root = tk.Tk()
root.title("ArcGIS Operations")

# Set the window size
root.geometry('300x150')

# Create and place the "Download" button
download_button = ttk.Button(root, text="Download/Compress Photos", command=execute_download)
download_button.pack(pady=10)  # Add some vertical padding

# Create and place the "Upload" button
upload_button = ttk.Button(root, text="Upload Compressed Photos", command=execute_upload)
upload_button.pack(pady=10)  # Add some vertical padding

# Create and place the "Delete" button
delete_button = ttk.Button(root, text="Delete Hosted Photos", command=execute_delete)
delete_button.pack(pady=10)  # Add some vertical padding

# Start the GUI event loop
root.mainloop()
