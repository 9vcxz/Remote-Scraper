'''
    offer_relay module for dealing with databases and detecting changes in offers
    input: output.json file from scraper.py
    output: json report file regarding changes
    NOTE:
        current db schema won't be good at tracking changes for stats
        in future - 2 tables w/ established relationship, 
        one for holding offers with unchangeable attributes (id, url, name, date_added)
        the other for tracking a certain offer through time until that offer becomes unavailable, 
        so (id (from the 1st table), price, is_available, timestamp) 

        current db structure unfortunately requires deletion of unavail. offers
    TODO:
        !! add exception handling
        clean up structure, clear up function flow etc.
        set up logging
        add db entry for offer pictures (not important now)
'''
import sqlite3, os
from datetime import datetime
import json
from utils.logging_config import get_logger


logger = get_logger(os.path.basename(__file__))


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # cursor.execute("DROP TABLE IF EXISTS offers")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            price REAL,
            date_added TEXT,
            description TEXT,
            is_available TRUE,
            last_seen TEXT,
            checked TRUE,
            timestamp TEXT
        )
    """)
    conn.commit()
    return conn

def insert_offer(conn, offer):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO offers (title, url, price, date_added, description, is_available, last_seen, checked, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        offer['offerTitle'],
        offer['offerURL'],
        offer['offerPrice'],
        offer['offerDateAdded'],
        offer['offerDesc'],
        True,
        datetime.utcnow(),
        True,
        datetime.utcnow()
    ))
    conn.commit()

def set_offer_unavailable():
    pass

def detect_offer_changes():
    '''
        detects changes in db and packs them into a JSON file, to be intercepted by notification manager
        it now detects in availability and price of previously registered offer
    '''
    pass

def db_relay_run(scraper_output):
    item_name = next(iter(scraper_output))
    sanitized_item_name = item_name.replace(' ', '_').lower()
    db_path = f'databases/{sanitized_item_name}.db'

    offer_changes_dict = {'newOffers': {}, 'unavailableOffers': {}, 'priceChanges': {}}

    if not os.path.exists(db_path):
        # create db file for a new user query
        conn = init_db(db_path)
        offer_dict = scraper_output[item_name]
        for offer_number, offer in offer_dict.items():
            insert_offer(conn, offer)
        conn.close()
    else:
        conn = init_db(db_path)
        cursor = conn.cursor()
        offer_dict = scraper_output[item_name]

        # adding new offers to db
        # set values of rows to unchecked
        cursor.execute("""
            UPDATE offers
            SET checked = 0
        """)
        conn.commit()
        for offer_number, offer in offer_dict.items():
            cursor.execute("SELECT id FROM offers WHERE url = ?", 
                           (offer['offerURL'],))
            row = cursor.fetchone()
            if row:
                cursor.execute(f"""
                    UPDATE offers
                    SET checked = 1, last_seen = ?
                    WHERE url = ?
                """, (datetime.utcnow(), offer['offerURL'],))
                conn.commit()
                # detect_offer_changes: COMPARE PRICES
                cursor.execute("SELECT price FROM offers WHERE url = ?", (offer['offerURL'],))
                offer_price_from_db = cursor.fetchone()[0]
                if int(offer['offerPrice']) != int(offer_price_from_db):
                    offer_changes_dict['priceChanges'].update({offer['offerURL']: [int(offer_price_from_db), int(offer['offerPrice'])]})
                cursor.execute("UPDATE offers SET price = ? WHERE url = ?",
                                (offer['offerPrice'], offer['offerURL'],))
            else:
                # detect_offer_changes: NEW OFFER ADDED
                insert_offer(conn, offer)
                offer_changes_dict['newOffers'].update({offer['offerURL']: {}})

        # expired offers
        cursor.execute("SELECT MAX(id) from offers")
        db_max_id = cursor.fetchone()
        db_max_id = db_max_id[0]

        if db_max_id > len(offer_dict):
            # need to isolate those expired offers for logging purposes
            cursor.execute("""
                UPDATE offers
                SET is_available = 0, checked = 1
                WHERE checked = 0
            """)
            conn.commit()

            # detect_offer_changes: OFFER NO LONGER AVAILABLE
            cursor.execute("SELECT * FROM offers WHERE is_available = 0")
            unavailable_offers = cursor.fetchall()
            for unavailable_offer in unavailable_offers:
                temp = {unavailable_offer[2]: {}}
                offer_changes_dict['unavailableOffers'].update(temp)

            # temp. solution, to be changed later
            cursor.execute("DELETE FROM offers WHERE is_available = 0")
            conn.commit()

        conn.close()

    return offer_changes_dict

if __name__ == '__main__':
    db_relay_run()