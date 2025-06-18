'''
    NOTE:
        selenium appears to be mandatory for extracting offer's view count and location...
        offer attributes:
            > offer_url
            > pics_url
            > offer_title
            > price
            > date_added
            > description
            > view_count   (not doable w/o selenium)
            > localization (not doable w/o selenium)
'''
import os, sys, time
from utils.logging_config import get_logger
from utils import constants, exceptions
from utils.helpers import sanitize, get_html_text
from utils.soup_extractors import get_total_predicted_offers_num, get_total_page_number, get_offers_url
from utils.soup_extractors import get_offer_title, get_offer_price, get_offer_pics_urls, get_offer_date_added, get_offer_desc
from utils.soup_extractors import is_offer_not_available_loader
from bs4 import BeautifulSoup


logger = get_logger(os.path.basename(__file__))


def create_url(json_input):
    item_name = json_input["itemName"]
    category = json_input["category"]
    price_from = json_input["priceRangeFrom"]
    price_to = json_input["priceRangeTo"]
    condition = json_input["condition"]
    shipping = json_input["shipping"]
    global query_started
    query_started = False

    logger.debug(f'from user input; item_name:{item_name}; category:{category}; priceRange: {price_from}-{price_to}; condition: {condition}; shipping: {shipping}')

    if category is None:
        url = f'{constants.MAIN_URL}oferty/q-{sanitize(item_name)}/'
    else:
        url = f'{constants.MAIN_URL}{category}q-{sanitize(item_name)}/'
    
    if price_from:
        if not query_started:
            url = f'{url}?'
            query_started = True
        else:
            url = f'{url}&'
        url = f'{url}{constants.PRICE_FROM}{price_from}'
    if price_to:
        if not query_started:
            url = f'{url}?'
            query_started = True
        else:
            url = f'{url}&'
        url = f'{url}{constants.PRICE_TO}{price_to}'
    if condition:
        if not query_started:
            url = f'{url}?'
            query_started = True
        else:
            url = f'{url}&'
        if condition == "used":
            url = f'{url}{constants.COND_USED}'
        elif condition == "new":
            url = f'{url}{constants.COND_NEW}'
        elif condition == "damaged":
            url = f'{url}{constants.COND_DAMAGED}'
    if shipping:
        if not query_started:
            url = f'{url}?'
            query_started = True
        else:
            url = f'{url}&'
        url = f'{url}{constants.SHIPPING}'
        
    logger.debug(f'Created URL: {url}')
    return url

def initial_parse(soup_obj):
    total_predicted_offers_num = get_total_predicted_offers_num(soup_obj)
    total_page_number = get_total_page_number(soup_obj)

    return total_page_number, total_predicted_offers_num

def create_additional_urls(url, total_page_number):
    logger.debug('Generating additional urls')
    aux_urls = []
    if total_page_number == 2:
        if query_started:
            temp_url = f'{url}&page=2' 
        else:
            temp_url = f'{url}?page=2' 

        aux_urls.append(temp_url)
        return aux_urls
    else:
        for i in range(2, total_page_number + 1):
            if query_started:
                temp_url = f'{url}&page={i}' 
            else:
                temp_url = f'{url}?page={i}'
            aux_urls.append(temp_url)
        return aux_urls

def merge_urls(url, aux_urls):
    merged_urls = aux_urls
    merged_urls.insert(0, url)
    return merged_urls

def offer_parser(soup, offer_url):
    offer_title = get_offer_title(soup)
    offer_price = get_offer_price(soup)
    offer_date_added = get_offer_date_added(soup)
    try:
        offer_pics_urls = get_offer_pics_urls(soup)
    except exceptions.ScraperOfferAttributeErrorOmmitable as e:
        logger.warning(e)
        offer_pics_urls = None
    try: 
        offer_desc = get_offer_desc(soup)
    except exceptions.ScraperOfferAttributeErrorOmmitable as e:
        logger.warning(e)
        offer_desc = None

    offer_dict = {
        "offerURL": offer_url,
        "offerTitle": offer_title,
        "offerPrice": offer_price,
        "offerPics": offer_pics_urls,
        "offerDateAdded": offer_date_added,
        "offerDesc": offer_desc
    }
    logger.debug(f'Extracted offer dict: {offer_dict}')
    return offer_dict

# retry after ScraperOfferAttributeError - it should've been a decorator..
def create_offers_dict(offers_urls):
    logger.info('Parsing data from individual offers.')

    main_offer_dict = {}
    for i, offer_url in enumerate(offers_urls):
        logger.info(f'Parsing offer {i+1}/{len(offers_urls)}')
        logger.debug(f'Extracting from: {offer_url}')

        offer_dict = None
        attempts = 0
        last_excepton = None

        while attempts < constants.ATTEMPTS and offer_dict is None:
            attempts += 1
            try:
                html_text = get_html_text(offer_url)
                logger.debug(f"Got html doc for URL: {offer_url}")
                soup = BeautifulSoup(html_text, 'html.parser')

                try: 
                    offer_dict = offer_parser(soup, offer_url)
                except exceptions.ScraperOfferAttributeError as e:
                    last_exception = e
                    logger.error(f"Offer parsing failed on attempt {attempts} for url: {offer_url}")
                    
                    if is_offer_not_available_loader(last_exception.soup):
                        logger.warning(f"The offer has been found, but is no longer available, skipping.")
                        break
                    if attempts <= constants.ATTEMPTS:
                        logger.error(f"Retrying, attempt: {attempts}/{constants.ATTEMPTS} for url: {offer_url}")
                        time.sleep(constants.SLEEP_BETWEEN_ATTEMPTS)

            except exceptions.ScraperHTTPError as e:   
                logger.error(e)
                if attempts <= constants.ATTEMPTS:
                    logger.error(f"Retrying, attempt: {attempts}/{constants.ATTEMPTS} for url: {offer_url}")
                
        if offer_dict is None:
            # offer still not extracted after X attempts 
            raise exceptions.ScraperAttributeError(f"Failed to extract essential attributes from offer, url: {offer_url}", soup=last_exception.soup)
        else:
            main_offer_dict[f"offer{i+1}"] = offer_dict

    return main_offer_dict

def scrape(user_input_dict):
    logger.info(f"Starting scraper for user offer query: {user_input_dict['itemName']}")

    main_page_url = create_url(user_input_dict)
    main_page_html_text = get_html_text(main_page_url)
    main_page_soup = BeautifulSoup(main_page_html_text, 'html.parser')
    logger.debug(f'Got html doc for URL: {main_page_url}')

    total_page_number, total_predicted_offers_num = initial_parse(main_page_soup)
    if total_predicted_offers_num != 1000:
        logger.info(f"Found {total_predicted_offers_num} predicted total offers.")
    else:
        logger.info(f"Found over {total_predicted_offers_num} predicted total offers.")
    logger.debug(f"Found {total_page_number} offer pages, and {total_predicted_offers_num} predicted total offers for entry: {user_input_dict['itemName']}")

    main_url_list = []
    if total_page_number > 1: 
        aux_urls = create_additional_urls(main_page_url, total_page_number)
        main_url_list = merge_urls(main_page_url, aux_urls)
    else:
        main_url_list.append(main_page_url)

    logger.debug(f'Created main pages URL list ({len(main_url_list)}): {main_url_list}')

    offer_url_list = []
    for index, main_page_url in enumerate(main_url_list):
        main_page_html_text = get_html_text(main_page_url)
            # logger.fatal(e)
            # sys.exit()

        logger.info(f"Acquiring offer URLs from page: {index+1}/{len(main_url_list)}")
        logger.debug(f'Got html doc for URL: {main_page_url}')
        main_page_soup = BeautifulSoup(main_page_html_text, 'html.parser')
        current_page_offer_urls = get_offers_url(main_page_soup)
        for offer_url in current_page_offer_urls:
            if offer_url not in offer_url_list:
                offer_url_list.append(offer_url)
        
    logger.debug(f'Created total offers URL list ({len(offer_url_list)}): {offer_url_list}')        

    logger.info(f"Parsing individual offers.")
    output_dict = create_offers_dict(offer_url_list)
    output_dict = {user_input_dict['itemName']: output_dict}

    logger.info(f'Returning output dictionary.')

    return output_dict
