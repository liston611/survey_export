from arcgis.gis import GIS
#from arcgis.features import FeatureLayer
import re
import os
import pandas as pd
from PIL import Image, ExifTags
from concurrent.futures import ThreadPoolExecutor, as_completed

# Compress image
def compress_img(img_path, img_path_comp, quality = 65):
    image = Image.open(img_path)

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

    resized_image.save(img_path_comp, quality = quality, optimize=True)


# for feature in features:
def download_and_rename_attachment(feature, attachment, base_path, comp_path):
    object_id = feature.attributes['objectid']
    creation_date = pd.to_datetime(feature.attributes['CreationDate'], unit='ms')
    date_str = creation_date.strftime('%m%d%y-%H%M')
    bus_route = str(feature.attributes['bus_route'])
    stop_abbr = str(feature.attributes['Abbr'])
    folder_path = os.path.join(base_path, bus_route, stop_abbr)
    folder_path_comp = os.path.join(comp_path, bus_route, stop_abbr)
    os.makedirs(folder_path, exist_ok=True)
    os.makedirs(folder_path_comp, exist_ok=True)

    attachment_id = attachment['id']
    attachment_name = attachment['name']
    file_str, attachment_type = os.path.splitext(attachment_name)
    file_name = f"{stop_abbr}_{date_str}_OID{object_id}-{attachment_id}{attachment_type}"
    file_name_comp = f"{stop_abbr}_{date_str}_OID{object_id}-{attachment_id}_comp{attachment_type}"
    file_path = os.path.join(folder_path, file_name)
    file_path_comp = os.path.join(folder_path_comp, file_name_comp)
    
    # Download the attachment
    if not file_str[len(file_str)-5:] == '_comp':
        if not os.path.exists(file_path):
            feature_layer.attachments.download(oid=object_id, attachment_id=attachment_id, save_path=folder_path)
            os.rename(os.path.join(folder_path, attachment_name), file_path)

        # Save compressed
        if not os.path.exists(file_path_comp):
            compress_img(file_path, file_path_comp)

        # if os.path.exists(file_path) and os.path.exists(file_path_comp):
        #     feature_layer.attachments.add(oid=object_id, file_path=file_path_comp)
        #     feature_layer.attachments.delete(oid=object_id, attachment_id=attachment_id)

def upload_compressed(feature, base_path, comp_path):
    # iterate features
    ## find feature objectID
    object_id = feature.attributes['objectid']
    attachments = feature_layer.attachments.get_list(oid=object_id)
    attachments_names = [attachment['name'] for attachment in attachments]

    bus_route = str(feature.attributes['bus_route'])
    stop_abbr = str(feature.attributes['Abbr'])
    file_path_comp = os.path.join(comp_path, bus_route, stop_abbr)

    for dirpath, dirnames, filenames in os.walk(file_path_comp, topdown=False):
         for filename in filenames:
             file_oid = int(re.search(r"OID(\d{1,4})-", filename)[1])
             if (not filename in attachments_names) and file_oid == object_id:
                 feature_layer.attachments.add(oid=object_id, file_path = os.path.join(file_path_comp,filename))

    ## find compressed photos for objectID


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
base_path = 'photos2'
comp_path = 'photos2\\working'

# Use ThreadPoolExecutor to download attachments in parallel
with ThreadPoolExecutor(max_workers=6) as executor:
    # Store future tasks
    future_to_attachment = {executor.submit(
        download_and_rename_attachment, feature, attachment, 
        base_path, comp_path): (feature, attachment)
                            for feature in features for attachment in feature_layer.attachments.get_list(
                                oid=feature.attributes['objectid'])}
    
    # Process completed futures
    for future in as_completed(future_to_attachment):
        future.result()  # You can handle exceptions here or get the result

# for feature in features:
#     upload_compressed(feature, base_path, comp_path)