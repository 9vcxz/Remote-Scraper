'''
    simple flask server app used for client - server communication
    TODO:
        /remove -> remove db files 
'''
from flask import Flask, request, jsonify
from datetime import datetime
# from utils.helpers import sanitize
import json, os, logging

logger = logging.get_logger(os.path.basename(__file__))



app = Flask(__name__)

@app.route('/test', methods=['POST'])
def test():
    data = request.json
    logger.info(f'Received request.')
    logger.debug(f'Received request: {data}')
    return 'OK', 200

@app.route('/config', methods=['POST'])
def config():
    received_config = request.json
    logger.info(f'Received config.')
    logger.debug(f'Received config: {received_config}')
    
    # check whether config is being created or updated (or neither)
    if os.path.exists('config/user_config.json'):
        with open('config/user_config.json', 'r') as f:
            existing_config = json.load(f)

        if existing_config == received_config:
            return f'Received config file, no changes in config detected, {datetime.now().isoformat(sep=" ", timespec="seconds")}\n', 200
        else:
            with open('config/user_config.json', 'w') as f:
                json.dump(received_config, f, indent=4)
            return f'Received config file, settings have been updated, {datetime.now().isoformat(sep=" ", timespec="seconds")}\n', 200    
    else:
        with open('config/user_config.json', 'w') as f:
                json.dump(received_config, f, indent=4)
        return f'Received config file, new config loaded, {datetime.now().isoformat(sep=" ", timespec="seconds")}\n', 200

@app.route('/offer', methods=['POST'])
def offer():
    offer = request.json
    logger.info(f"Received offer: {offer['itemName']}")
    logger.debug(f'Received offer: {offer}')

    offer_name = offer['itemName']
    offer_name = offer_name.replace(' ', '_').lower()

    # if offer exists under the same name -> compare and send response
    offer_path = f'offers/{offer_name}.json'
    if os.path.exists(offer_path):
        with open(offer_path, 'r') as f:
            old_offer = json.load(f)

        if offer == old_offer:
            return f'Received already existing offer {offer_name}, {datetime.now().isoformat(sep=" ", timespec="seconds")}\n', 200
        else:
            with open(offer_path, 'w') as f:
                json.dump(offer, f, indent=4)
            return f'Existing offer {offer_name} has been updated, {datetime.now().isoformat(sep=" ", timespec="seconds")}\n', 200
    else:
        with open(f'{offer_path}', 'w') as f:
            json.dump(offer, f, indent=4)
        return f'Received new offer: {offer_name}, {datetime.now().isoformat(sep=" ", timespec="seconds")}\n', 200

@app.route('/delete', methods=['POST'])
def delete():
    offer_to_delete = request.data
    offer_to_delete = request.data.decode('UTF-8')
    # offer_to_delete = offer_to_delete['delete']
    logger.info(f"Received delete request for '{offer_to_delete}'")

    offer_to_delete_path = f'offers/{offer_to_delete}.json'
    if not os.path.exists('offers'):
        return f'No stored offers\n', 200
    
    if not os.path.exists(offer_to_delete_path):
        return f'Offer {offer_to_delete} not found\n', 200
        
    os.remove(offer_to_delete_path)
    logger.info(f'Offer {offer_to_delete} has been succesfully deleted.')

    return f'Offer {offer_to_delete} has been deleted\n', 200

@app.route('/get_offers', methods=['GET'])
def get_offers():
    logger.info("Received 'get_offers' request.")
    if not os.path.exists('offers'):
        logger.info("No stored offers found.")
        return f'No stored offers found.', 204
    if len(os.listdir('offers')) == 0:
        logger.info("No stored offers found.")
        return f'No stored offers found.', 204

    offers = os.listdir('offers')
    for i, offer in enumerate(offers):
        offers[i] = offer.split('.')[0]

    logger.info(f"Found {len(offers)} offer(s), sending response to client...")
    logger.debug(f"Found offers: {offers}")
    return f'Found offers: {offers}\n', 200
    

if __name__ == '__main__':
    app.run(host='192.168.0.28', port=5000)
