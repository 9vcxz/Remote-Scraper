import logging, os

LOG_DIR_PATH = 'logs'


def get_logger(console_log=True):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt='[%(levelname)s] %(asctime)s %(filename)s:%(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    os.makedirs(LOG_DIR_PATH, exist_ok=True)

    last_global_log_file_path = os.path.join(LOG_DIR_PATH, 'last.log')    
    last_global_log_handler = logging.FileHandler(last_global_log_file_path, mode='w')
    last_global_log_handler.setLevel(logging.DEBUG)
    last_global_log_handler.setFormatter(formatter)

    alltime_global_log_file_path = os.path.join(LOG_DIR_PATH, 'alltime.log')    
    alltime_global_log_handler = logging.FileHandler(alltime_global_log_file_path, mode='a')
    alltime_global_log_handler.setLevel(logging.DEBUG)
    alltime_global_log_handler.setFormatter(formatter)

    if console_log:
        console_global_handler = logging.StreamHandler()
        console_global_handler.setLevel(logging.INFO)
        console_global_handler.setFormatter(formatter)
    
    logger.addHandler(last_global_log_handler)
    logger.addHandler(alltime_global_log_handler)
    if console_log:
        logger.addHandler(console_global_handler)


    return logger