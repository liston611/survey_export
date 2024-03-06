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

def gen_name(feature, attachment = None):
    try: object_id = feature.attributes['objectid']
    except: object_id = feature.attributes['OBJECTID']
    
    # try: creation_date = pd.to_datetime(feature.attributes['EditDate_1'], unit='ms')
    # except: creation_date = pd.to_datetime(feature.attributes['inProgressDate'], unit='ms')
    
    # try: date_str = creation_date.strftime('%m%d%y-%H%M')
    # except:
    #     creation_date = pd.to_datetime(feature.attributes['CreationDate'], unit='ms')
    #     date_str = creation_date.strftime('%m%d%y-%H%M')
    date_str = '000000-0000'
    
    try: wrkordr = str(feature.attributes['HEAT'])
    except: #wrkordr = str(feature.attributes['workOrderId'])
        wrkordr = "RooseveltHwy"
    
    if wrkordr == '':
        wrkordr = 'BLANK'
    
    try:
        stop_abbr = str(feature.attributes['StopAbbr_1'])[:6]
        if len(str(int(stop_abbr))) != 6:
            raise ValueError("Condition not met")
    except:
        try:
            stop_abbr = str(re.search(r'[^0-9](\d{6})[^0-9]',feature.attributes['description'])[1])
        except: stop_abbr = 'OTHER_'

    if attachment == None:
        attachment_id = ''
        attachment_type = ''
    else:
        attachment_id, attachment_name = attachment['id'], attachment['name']
        _, attachment_type = os.path.splitext(attachment_name)
    
    file_base = f"{stop_abbr}_{date_str}_{wrkordr}_OID{object_id}_{attachment_id}"
    
    file_name = f"{file_base}{attachment_type}"
    file_name_comp = f"{file_base}_comp{attachment_type}"

    return [file_name, file_name_comp, stop_abbr]


# for feature in features:
def download_and_rename_attachment(feature_layer, feature, attachment, base_path, comp_path):
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
        if not os.path.exists(file_path_comp) and attachment_type in ['.jpg', '.jpeg', '.png', '.gif']:
            os.makedirs(folder_path_comp, exist_ok=True)
            compress_img(file_path, file_path_comp)


def upload_compressed(feature_layer, feature, comp_path):
    # iterate features
    ## find feature OBJECTID
    try: object_id = feature.attributes['objectid']
    except: object_id = feature.attributes['OBJECTID']

    file_name, _, stop_abbr = gen_name(feature)

    try:
        attachments = feature_layer.attachments.get_list(oid=object_id)
        attachments_names = [attachment['name'] for attachment in attachments]
    except:
        attachments_names = ''

    file_path_comp = os.path.join(comp_path, stop_abbr)

    for _, _, filenames in os.walk(file_path_comp, topdown=False):
         for filename in filenames:
             if (not filename in attachments_names) and file_name in filename:
                 feature_layer.attachments.add(oid=object_id, file_path = os.path.join(file_path_comp,filename))
                 print(f"Photo {filename} uploaded from {file_path_comp}")


def delete_fullres(feature_layer, feature, attachment, base_path, mode = True):
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
    

# Use ThreadPoolExecutor to download attachments in parallel
def execute_download(item, base_path, comp_path, max_work):
    feature_layer = item.layers[0]  # Assuming it's the first layer
    # Query the feature layer for records
    features = feature_layer.query(where="1=1", out_fields="*", return_attachments=False).features
    
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


def execute_upload(item, comp_path, max_work):
    feature_layer = item.layers[0]  # Assuming it's the first layer
    # Query the feature layer for records
    features = feature_layer.query(where="1=1", out_fields="*", return_attachments=False).features

    with ThreadPoolExecutor(max_workers=max_work) as executor:
        # Store future tasks
        future_to_attachment = {executor.submit(
            upload_compressed, feature_layer, feature, 
            comp_path): (feature)
                                for feature in features
                                }
        # Process completed futures
        for future in as_completed(future_to_attachment):
            future.result()  # You can handle exceptions here or get the result
    print('Upload Complete')


def execute_delete(item, base_path, max_work, mode = True):
    feature_layer = item.layers[0]  # Assuming it's the first layer
    # Query the feature layer for records
    features = feature_layer.query(where="1=1", out_fields="*", return_attachments=False).features

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

def execute_delete_all(item, base_path, max_work):
    execute_delete(item, base_path, max_work, mode=False)