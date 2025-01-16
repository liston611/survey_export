# client ID from the registered application
from configparser import ConfigParser
from arcgis.gis import GIS
import requests

# The URL of your ArcGIS Online organization
org_url = 'https://martagis.itsmarta.com/arcgisprod/'

def get_token():
    config = ConfigParser()
    config.read('config.ini')
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