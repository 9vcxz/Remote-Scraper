# scraper-bound constants
MAIN_URL = 'https://www.olx.pl/'
CSS_OFFER_CLASS = 'css-1tqlkj0'
CSS_PICTURE_CLASS = 'css-1bmvjcs'
CSS_DESC_CLASS = 'css-19duwlz'
CSS_LOCATION_CLASS = 'css-13l8eec'
CSS_NOT_AVAILABLE_LOADER_CLASS = 'css-1c13tbt'
PRICE_FROM = 'search[filter_float_price:from]='
PRICE_TO = 'search[filter_float_price:to]='
COND_USED = 'search[filter_enum_state][0]=used'
COND_NEW = 'search[filter_enum_state][0]=new'
COND_DAMAGED = 'search[filter_enum_state][0]=damaged'
SHIPPING = 'courier=1'


# user input validation
USER_INPUT_KEYS= {
    'itemName': (str, None),
    'shipping': bool,
    'priceRangeFrom': (int, float),
    'priceRangeTo': (int, float),
    'condition': (str, None),
    'category': (str, None)
}
USER_INPUT_CONDITIONS = {
    'used',
    'new',
    'damaged',
    None
}
CONFIG_SCHEMA = {
    'SERVER_URL': str,
    'DISCORD_UID': int,
    'NOTIF_FREQ_SECS': int,
    'NOTIF_NEW_ITEMS': bool,
    'NOTIF_PRICE_DROP': bool,
    'NOTIF_REMOVED_ITEMS': bool,
}


# requests
REQUEST_TIMEOUT = 10
ATTEMPTS = 5
SLEEP_BETWEEN_ATTEMPTS = 5
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# scraper
SCRAPING_ATTEMPTS = 3






# discord bot 
DISCORD_BOT_TOKEN = ""
