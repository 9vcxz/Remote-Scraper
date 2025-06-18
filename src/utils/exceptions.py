# SCRAPING RELATED ERRORS
class ScraperError(Exception):
    pass

# user input validation 
class UserInputMissingKeyError(ScraperError):
    pass
class UserInputInvalidValueError(ScraperError):
    pass

# requests
class ScraperConnectionError(ScraperError):
    '''
    Exception thrown during fatal scraper issues - lack of connection or error 502.
    '''
class ScraperHTTPError(ScraperError):
    '''
    unused, for now...
    '''
    pass


# soup
class ScraperAttributeError(ScraperError):
    def __init__(self, message, soup=None):
        super().__init__(message)
        self.soup = soup
class ScraperOfferAttributeError(ScraperAttributeError):
    '''
    Exception thrown when an essential attribute of an individual offer (e.g. title, price) cannot be found.
    Later to be caught for either omitting the entire offer or retrying.
    It carries message concerning which attribute is missing and soup object, later to be saved for debugging purposes. 
    '''
class ScraperOfferAttributeErrorOmmitable(ScraperAttributeError):
    '''
    Exception thrown when non essential attribute of an individual offer cannot be found.
    '''
    def __init__(self, message, attr=None):
        super().__init__(message)
        self.attr = attr