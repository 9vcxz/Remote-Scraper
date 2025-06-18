'''
Fuctions providing various utility
'''
from utils import constants, exceptions
from utils.logging_config import get_logger
import time, os

logger = get_logger(os.path.basename(__file__))

# misc
def normalize_date(date_string):
    from dateparser import parse
    date_obj = parse(date_string, languages=['pl'])
    iso_date = date_obj.date().isoformat()
    return iso_date

def sanitize(input_string):
    from unidecode import unidecode
    input_string = input_string.replace(' ', '-').replace(',', '').lower() 
    input_string = unidecode(input_string)
    return input_string

def validate_user_input(user_input: dict):
    for key, expected_type in constants.USER_INPUT_KEYS.items():
        if key not in user_input:
            raise exceptions.UserInputMissingKeyError(f'Missing required key: \'{key}\' in user input')
        if not isinstance(user_input[key], expected_type):
            raise exceptions.UserInputInvalidValueError(f'Key \'{key}\' has invalid type. Expected: {expected_type}, got: {type(user_input[key])}. ')

    if user_input['condition'] is not None and user_input['condition'] not in constants.USER_INPUT_CONDITIONS:
        raise exceptions.UserInputInvalidValueError(f"Invalid condition value: {user_input['condition']}. Allowed values: {constants.USER_INPUT_CONDITIONS}.")

# connection
def get_html_text(url):
    import requests

    for attempt in range(1, constants.ATTEMPTS + 1):
        try:
            response = requests.get(url, timeout=constants.REQUEST_TIMEOUT, headers=constants.HEADERS)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            logger.error(f"Encountered a timeout for {url}, attempt: {attempt}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for: {url}, attempt: {attempt}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [429, 410, 503]:
                retry_after = int(e.response.headers.get("Retry-After", 5))
                logger.error(f"Received response code: {e.response.status_code}, waiting {retry_after} seconds...")
                time.sleep(retry_after)
            else:
                raise exceptions.ScraperHTTPError(f"Connection error for {url}, status: {e.response.status_code}")

        time.sleep(constants.SLEEP_BETWEEN_ATTEMPTS)
    raise exceptions.ScraperConnectionError(f"Failed to fetch {url}, after {constants.ATTEMPTS} attempts.")

# db
def get_offer_price_from_db():
    pass

    # try: 
    #     response = requests.get(url, timeout=constants.REQUEST_TIMEOUT, headers=constants.HEADERS)
    #     response.raise_for_status()
    #     return response.text
    # except requests.exceptions.Timeout as e:
    #     raise exceptions.ScraperTimeoutError(f"Timeout Error for url: {url}")
    # except requests.exceptions.HTTPError as e:
    #     raise exceptions.ScraperHTTPError(response.status_code, url) from e
    # except requests.exceptions.RequestException as e:
    #     raise exceptions.ScraperConnectionError(f'Unknown requests error for URL: {url}.') from e