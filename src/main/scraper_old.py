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
            > localization (not doable w/o selenium))
    TODO:
        add date to log format
        differentiate between expired/bought offer and a bad url
        create link should include: shipping bool, priceRange
        !! add exception handling
        system independent file paths

    it should've been a class.. :(
'''
import json, requests, re, os
from bs4 import BeautifulSoup
from utils.logging_config import get_logger
from utils import constants
from utils.helpers import sanitize, normalize_date, get_html_text


logger = get_logger(os.path.basename(__file__))

def create_url(json_input):
    logger.info(f'Creating url from input: {json.dumps(json_input, indent=4)}')
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
    
    # hmmm
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
        
    logger.info(f'Created URL: {url}')
    return url

def main_parser(json_input=None, fed_url=None):
    logger.debug(f'starting main_parser with args: json_input={json_input}, fed_url={fed_url}')

    if fed_url is None:
        url = create_url(json_input)
    else:
        url = fed_url
    logger.debug(f'created url: {url}')

    dom = get_html_text(url)
    soup = BeautifulSoup(dom, 'html.parser')

    res = re.search(r"[0-9]+",soup.find('span', {'data-testid': 'total-count'}).text)
    total_predicted_offers_num = int(res.group())
    logger.debug(f'Number of total predicted offers: {total_predicted_offers_num}')

    # it is how it is
    offer_urls = []
    for a in soup.find_all('a'):
        for attr in a.attrs:
            if str(attr).startswith('href'):
                attr_str = str(a[attr])
                if attr_str.startswith('/d/'):
                    offer_url = f'{constants.MAIN_URL[:-1]}{attr_str}'
                    search_res = re.search("reason=extended_search_extended", offer_url)
                    if search_res:
                        continue
                    if offer_url not in offer_urls:
                        offer_urls.append(offer_url)
                        logger.debug(f'appending offer_urls with {offer_url}')

    
    # issue with not detecting all pages, e.g. logitech g305, w/o null category
    if len(soup.find('div', {'data-testid': 'pagination-wrapper'}).find_all()) != 0:
        total_page_number = int(soup.find('div', {'data-testid': 'pagination-wrapper'}).find_all('li')[-1].text)
    else:
        total_page_number = 1
    logger.debug(f'number of pages found: {total_page_number}')

    logger.debug(f'main_parser returning:\noffer_urls:\n{offer_urls}\ntotal_page_number:{total_page_number}\ntotal_predicted_offers_num:{total_predicted_offers_num}')
    return offer_urls, total_page_number, total_predicted_offers_num

def create_aux_urls(url, total_page_number):
    logger.info('Generating aux urls')
    aux_urls = []
    if total_page_number == 2:
        if query_started:
            temp_url = f'{url}&page=2' 
        else:
            temp_url = f'{url}?page=2' 

        aux_urls.append(temp_url)

        logger.debug(f'Generated aux urls:: {aux_urls}')
        return aux_urls
    else:
        for i in range(2, total_page_number + 1):
            if query_started:
                temp_url = f'{url}&page={i}' 
            else:
                temp_url = f'{url}?page={i}'
            aux_urls.append(temp_url)

        logger.debug(f'Generated aux urls:: {aux_urls}')
        return aux_urls
    
def aux_parser(query_url, total_page_number):
    logger.info('Parsing aux pages')

    aux_urls = create_aux_urls(query_url, total_page_number)
    aux_offer_urls = []
    for aux_url in aux_urls:
        temp_aux_offer_urls, placeholder1, placeholder2 = main_parser(fed_url=aux_url)
        aux_offer_urls.append(temp_aux_offer_urls)
        # for aux_offer in aux_offer_urls:
        #     aux_offer_urls.append(aux_offer)
    logger.debug(f'returning aux_offer_urls: {aux_offer_urls}')
    return aux_offer_urls

def offer_parser(offer_url):
    dom = get_html_text(offer_url)
    soup = BeautifulSoup(dom, 'html.parser')

    logger.debug(f'Extracting from: {offer_url}')

    try:
        offer_title = soup.find('div', {'data-testid': 'offer_title'}).text
    except AttributeError:
        logger.exception('offer_title not found')
    try:
        offer_price = soup.find('div', {'data-testid': 'ad-price-container'}).text
        offer_price = re.search(r"[0-9]+", offer_price).group()
    except AttributeError:
        logger.exception('offer_price not found')
        
    try:
        offer_pic_urls = soup.find('img', class_=constants.CSS_PICTURE_CLASS).attrs["srcset"]
        split_res = offer_pic_urls.split(" ")
        offer_pic_urls = []
        for res in split_res:
            if re.search(r"^http", res):
                offer_pic_urls.append(res)
    except AttributeError:
        logger.exception('offer_pics not found', stack_info=True)
        offer_pic_urls = None

    # maybe some proper date formatting later
    try:
        offer_date_added = soup.find('span', {'data-testid': 'ad-posted-at'}).text
        offer_date_added = normalize_date(offer_date_added)
    except AttributeError:
        logger.exception('offer_date_added not found')
    
    try:
        offer_desc = soup.find('div', class_=constants.CSS_DESC_CLASS).text
    except AttributeError:
        logger.exception('offer_desc not found')
        offer_desc = None

    offer_dict = {
        "offerURL": offer_url,
        "offerTitle": offer_title,
        "offerPrice": offer_price,
        "offerPics": offer_pic_urls,
        "offerDateAdded": offer_date_added,
        "offerDesc": offer_desc
    }
    logger.debug(f'Extracted offer dict: {offer_dict}')
    return offer_dict

def create_offers_dict(offer_urls):
    logger.info('Creating offers dictionary')

    main_offer_dict = {}
    for i, offer_url in enumerate(offer_urls):
        logger.debug(f'Offer {i+1}/{len(offer_urls)}')
        offer_dict = offer_parser(offer_url)
        main_offer_dict[f"offer{i+1}"] = offer_dict

    # logger.debug(f'returning main_offer_dict: {main_offer_dict}')
    return main_offer_dict

def scrape(user_input_dict):
    logger.info("Starting scraper")

    offer_urls, total_page_number, total_predicted_offers_num = main_parser(user_input_dict)

    query_url = create_url(user_input_dict)
    aux_offer_urls = aux_parser(query_url, total_page_number)
    for aux_offer_url_page in aux_offer_urls:
        for aux_offer_url in aux_offer_url_page:
            offer_urls.append(aux_offer_url)

    if len(offer_urls) != total_predicted_offers_num:
        logger.warning(f'the number of predicted offers: {total_predicted_offers_num} does not match the actual: {len(offer_urls)} ')
    else:
        logger.debug(f'number of offer URLs saved: {len(offer_urls)}')

    # testing new functions
    offers_dict = create_offers_dict(offer_urls)
    output_dict = {user_input_dict['itemName']: offers_dict}

    return output_dict

if __name__ == '__main__':
    scrape()
