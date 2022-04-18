import requests

api = 'e6cb73a915b74726b9081227221804'

def get_weatherapi_data(city): # api_key['darksky']
    try:
        url = f'http://api.weatherapi.com/v1/current.json?key=' + api + '&q=' + city + '&aqi=no'
        print(url)
        r = requests.get(url, timeout=5).json()
        return r
    except requests.exceptions.Timeout as e: 
        print(e)

print(get_weatherapi_data('Galanta'))