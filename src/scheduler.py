'''
    TODO:
        > later - turn the scheduler into a daemon (w/ python lib)
'''
from main.notification_manager import DiscordNotificationBot
import schedule, time, json, os, sys, signal
from utils import constants, exceptions
from datetime import datetime
from threading import Lock

from main.scraper import scrape
from main.db_relay import db_relay_run
from utils import logging_config


logger = logging_config.get_logger()


job_lock = Lock()
running = True

def load_config():
    with open('config/user_config.json', 'r') as f:
        config_dict = json.load(f)
    return config_dict

# TEMP
def load_offer_filenames():
    offer_filenames = os.listdir('offers')
    for i, offer in enumerate(offer_filenames):
        offer_filenames[i] = offer.split('.')[0]
    return offer_filenames

def load_offer_dict(filename):
    with open(f'offers/{filename}.json', 'r') as f:
        offer_json=json.load(f)
    return offer_json

def main_job(message=True):
    config = load_config()
    discord_uid = config['DISCORD_UID']

    offers = load_offer_filenames()
    for offer in offers:
        offer_dict  = load_offer_dict(offer)
        true_offer_name = offer_dict['itemName']

        attempt = 0
        while attempt < constants.SCRAPING_ATTEMPTS:
            attempt += 1
            logger.info(f"Attempting scraping: {attempt}/{constants.SCRAPING_ATTEMPTS}")
            try: 
                scraped_offers = scrape(offer_dict)
                # with open('test/query_output.json', 'w') as f:
                #     json.dump(query_output, f, indent=4)
                logger.info(f"Success. Finished scraping at attempt: {attempt} of {constants.SCRAPING_ATTEMPTS} .")
                break
            except exceptions.ScraperAttributeError as e:
                logger.exception(e) 
                with open('logs/malformed.html', 'w') as f:
                    f.write(e.soup.prettify())
                logger.error(f"Saved malformed html to: logs/malformed.html")
            except exceptions.ScraperConnectionError as e:
                logger.exception(e)
            
            if attempt == constants.SCRAPING_ATTEMPTS:
                logger.fatal(f"Failed to scrape 'user_query' after {constants.SCRAPING_ATTEMPTS} attempts.")


        offer_changes = db_relay_run(scraped_offers)
        logger.info(offer_changes)

        if message:
            send_notification_on_trigger(offer_changes, config, true_offer_name)
        
            
def send_notification_on_trigger(offer_changes, config, offer_name):
    if offer_changes['newOffers'] or offer_changes['unavailableOffers'] or offer_changes['priceChanges']:
        message = f'Offer \'{offer_name}\' update {datetime.now().isoformat(sep=" ", timespec="seconds")}\n'
        if offer_changes['newOffers'] and config['NOTIF_NEW_ITEMS']:
            message += f'\nNew offers:'
            for key in offer_changes['newOffers']:
                message += f'\n{key}'
            message += '\n' 
        if offer_changes['unavailableOffers'] and config['NOTIF_REMOVED_ITEMS']:
            message += f'\nUnavailable offers:'
            for key in offer_changes['unavailableOffers']:
                message += f'\n{key}'
            message += '\n'
        if offer_changes['priceChanges'] and config['NOTIF_PRICE_DROP']:
            message += f'\nPrice changes:'
            for key in offer_changes['priceChanges']:
                message += f'\n{key}'
                old_price = offer_changes['priceChanges'][key][0]
                new_price = offer_changes['priceChanges'][key][1]
                message += f'\nFrom {old_price} to {new_price}'
            message += '\n'    
        # print(message)
        discord_uid = config['DISCORD_UID']
        dnb.send_dm(discord_uid, message)


# TESTING DISCORD DM NOTIFICATIONS...
def _dm_test():
    config = load_config()
    discord_uid = config['DISCORD_UID']

    timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")
    message = f'Scheduler test {timestamp}'
    dnb.send_dm(discord_uid, message)
    print(timestamp)

def refresh_scheduler():
    global refresh_frequency

    with job_lock:
        print("Scanning for config changes...")
        schedule.clear('main_job')
        config_dict = load_config()
        
        updated_refresh_frequency = config_dict['NOTIF_FREQ_SECS'] 
        if refresh_frequency != updated_refresh_frequency:
            schedule.clear('config_reload')
            schedule.every(updated_refresh_frequency).seconds.do(refresh_scheduler).tag('config_reload')
        # print(f'global = {refresh_frequency}, new = {updated_refresh_frequency}')
        refresh_frequency = updated_refresh_frequency

        schedule.every(refresh_frequency).seconds.do(main_job).tag('main_job')

def signal_handler(sig, frame):
    global running
    print("\nShutdown signal received, stopping scheduler...")
    running = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Starting scheduler")
    config_dict = load_config()
    refresh_frequency = config_dict['NOTIF_FREQ_SECS']
    dnb = DiscordNotificationBot(constants.DISCORD_BOT_TOKEN)
    dnb.start()

    main_job(message=False)
    refresh_scheduler()
    schedule.every(refresh_frequency).seconds.do(refresh_scheduler).tag('config_reload')

    try:
        while running:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        print(f'Exception occured: {e}')
    finally:
        dnb.close()
        print('Scheduler has been shut down.')
        sys.exit(0)