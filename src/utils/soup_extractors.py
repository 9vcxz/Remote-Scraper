'''
A layer lower than scraper - functions in this module are designed to deal only 
with extracting desired data from the soup object.
'''
from utils import exceptions, constants
from utils.helpers import normalize_date
import re, os.path


def get_total_predicted_offers_num(soup):
    import re

    try:
        total_predicted_offers_num = soup.find('span', {'data-testid': 'total-count'})
        if not total_predicted_offers_num:
            raise exceptions.ScraperAttributeError('Total predicted offers num. attribute not found', soup=soup)

        match = re.search(r"[0-9]+", total_predicted_offers_num.text)
        if match:
            return int(match.group().replace(',', '.'))
        else:
            raise exceptions.ScraperAttributeError('No numeric value found in str(total_predicted_offers_num)', soup=soup)
    except Exception as e: 
        raise exceptions.ScraperAttributeError(f'Failed to extract total_predicted_offers_num {e}', soup=soup)
    
def get_total_page_number(soup):

    if len(soup.find('div', {'data-testid': 'pagination-wrapper'}).find_all()) != 0:
        total_page_number = int(soup.find('div', {'data-testid': 'pagination-wrapper'}).find_all('li')[-1].text)
    else:
        total_page_number = 1

    return total_page_number

def get_offers_url(soup):
    try: 
        a_elements = soup.find_all('a', class_="css-1tqlkj0")
        if not a_elements: 
            raise exceptions.ScraperAttributeError('Anchors with offer urls were not found', soup=soup)
        offer_urls = set()
        for a in a_elements:
            url_section = a['href']
            offer_url = f'https://www.olx.pl{url_section}'
            extended_search_offer_url = re.search("reason=extended_search_extended", offer_url)
            if extended_search_offer_url:
                continue
            else:
                offer_urls.add(offer_url)
        return list(offer_urls)
    except Exception as e:
        raise exceptions.ScraperAttributeError(f'Failed to extract offer_urls.', soup=soup)


# single offer helper funcs
def get_offer_title(soup):
    try: 
        offer_title = soup.find('div', {'data-testid': 'offer_title'}).text
        return offer_title
    except AttributeError:
        raise exceptions.ScraperOfferAttributeError(f"Failed to fetch offer's title.", soup=soup) 

def get_offer_price(soup):
    try:
        offer_price = soup.find('div', {'data-testid': 'ad-price-container'}).text
        offer_price = re.search(r"[0-9 ]+", offer_price).group()
        if offer_price:
            return offer_price.replace(" ", "")
        else:
            raise exceptions.ScraperOfferAttributeError(f"Failed to fetch offer's price.", soup=soup)
    except AttributeError:
        raise exceptions.ScraperOfferAttributeError("Failed to fetch offer's price.", soup=soup)

def get_offer_date_added(soup):
    try:
        offer_date_added = soup.find('span', {'data-testid': 'ad-posted-at'}).text
        offer_date_added = normalize_date(offer_date_added)
        return offer_date_added
    except AttributeError:
        raise exceptions.ScraperOfferAttributeError(f"Failed to fetch offer's 'date added' attribute.", soup=soup)

def get_offer_pics_urls(soup): 
    try:
        offer_pic_urls = soup.find('img', class_=constants.CSS_PICTURE_CLASS).attrs["srcset"]
        split_res = offer_pic_urls.split(" ")
        offer_pic_urls = []
        for res in split_res:
            if re.search(r"^http", res):
                offer_pic_urls.append(res)
        return offer_pic_urls
    except AttributeError:
        raise exceptions.ScraperOfferAttributeErrorOmmitable("No pictures found.", "pics")
        # logger.warning(f"No pictures found. Ommiting.")
        # return None

def get_offer_desc(soup):
    try:
        offer_desc = soup.find('div', class_=constants.CSS_DESC_CLASS).text
        return offer_desc
    except AttributeError:
        raise exceptions.ScraperOfferAttributeErrorOmmitable("No description found.", "desc")
        # logger.warning(f"No description found. Ommiting.")
        # return None

def is_offer_not_available_loader(soup):
    offer_na_loader = soup.find('div', class_=constants.CSS_NOT_AVAILABLE_LOADER_CLASS)
    return bool(offer_na_loader)
         
