from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


# Your client ID from the registered application
client_id = 'f3Gvne679NhcK7ts'

# The URL of your ArcGIS Online organization
org_url = 'https://martaonline.maps.arcgis.com'

# Get the OAuth token
print("Opening browser to obtain an OAuth token...")
gis = GIS(org_url, client_id=client_id, redirect_uri='urn:ietf:wg:oauth:2.0:oob')

print("Sign in completed.")


# Assuming gis has been authenticated
item_id = 'a0dc62673ce74a62b574444d4b6ee785'
item = gis.content.get(item_id)
feature_layer = item.layers[0]  # Assuming it's the first layer

# Query the feature layer for records
features = feature_layer.query(where="1=1", out_fields="*", return_attachments=False).features

# Define base path for saving photos
base_path = 'photos'

# for feature in features:

#     attrs = feature.attributes
#     # Format the CreationDate for naming
#     creation_date = pd.to_datetime(attrs['CreationDate'], unit='ms')
#     date_str = creation_date.strftime('%m%d%y_%H%M')
    
#     # Construct folder path based on Bus Route and Stop Abbr
#     bus_route = str(attrs['bus_route'])
#     stop_abbr = str(attrs['Abbr'])
#     folder_path = os.path.join(base_path, bus_route, stop_abbr)
#     os.makedirs(folder_path, exist_ok=True)

#     # Get attachments for the current feature
#     object_id = attrs['objectid']
#     attachments = feature_layer.attachments.get_list(oid=object_id)
    
#     for i, attachment in enumerate(attachments, start=1):
#         attachment_id = attachment['id']
#         attachment_name = attachment['name']
#         _, attachment_type = os.path.splitext(attachment_name)
#         file_name = f"{date_str}_{i}{attachment_type}"

#         if not os.path.exists(os.path.join(folder_path,file_name)):
#             # Download the attachment
#             feature_layer.attachments.download(oid=object_id, attachment_id=attachment_id, save_path=folder_path)
#             os.rename(
#                 os.path.join(folder_path,attachment_name),
#                 os.path.join(folder_path,file_name)
#             )
        
def download_and_rename_attachment(feature, attachment, base_path):
    object_id = feature.attributes['objectid']
    creation_date = pd.to_datetime(feature.attributes['CreationDate'], unit='ms')
    date_str = creation_date.strftime('%m%d%y_%H%M')
    bus_route = str(feature.attributes['bus_route'])
    stop_abbr = str(feature.attributes['Abbr'])
    folder_path = os.path.join(base_path, bus_route, stop_abbr)
    os.makedirs(folder_path, exist_ok=True)
    
    attachment_id = attachment['id']
    attachment_name = attachment['name']
    _, attachment_type = os.path.splitext(attachment_name)
    file_name = f"{date_str}_{attachment_id}{attachment_type}"
    file_path = os.path.join(folder_path, file_name)
    
    if not os.path.exists(file_path):
        # Download the attachment
        feature_layer.attachments.download(oid=object_id, attachment_id=attachment_id, save_path=folder_path)
        os.rename(os.path.join(folder_path, attachment_name), file_path)

# Assuming the rest of your setup is as before...

# Use ThreadPoolExecutor to download attachments in parallel
with ThreadPoolExecutor(max_workers=5) as executor:
    # Store future tasks
    future_to_attachment = {executor.submit(
        download_and_rename_attachment, feature, attachment, 
        base_path): (feature, attachment)
                            for feature in features for attachment in feature_layer.attachments.get_list(
                                oid=feature.attributes['objectid'])}
    
    # Process completed futures
    for future in as_completed(future_to_attachment):
        future.result()  # You can handle exceptions here or get the result
