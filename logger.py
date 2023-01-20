
import logging

__all__ = ['LOGGER_CF']

class LoggerConsFile():
    '''Singleton class implementing logging.Logger() instance.'''

    def __init__(self) -> None:
        self.logger = None
        self.ready = False
    
    def init_2CH(self, file_name='default_log.txt', logger_id='LogDcd'):
        ''' Create Logger() instance and setup logging parameters'''
        
        assert (not self.ready), f'Logger already exists. Deinit first, then setup anew.'
        
        # Instantiate new logger
        self.logger = logging.getLogger(logger_id)
        # Create new severity level 'PROGRESS' for information messages
        # which are not critical but required for transmission al. 
        self.PROGRESS = logging.CRITICAL
        logging.addLevelName(self.PROGRESS, 'PROGRESS')

        # Create handlers for two data flows:
        # _c - console
        # _f - file
        _c_handler = logging.StreamHandler()
        _c_handler.setLevel(logging.WARNING)
        _c_format = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
        _c_handler.setFormatter(_c_format)
        
        _f_handler = logging.FileHandler(file_name, mode='a')
        _f_handler.setLevel(logging.INFO)
        _f_format = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
        _f_handler.setFormatter(_f_format)

        # Add handlers to the logger
        self.logger.addHandler(_c_handler)
        self.logger.addHandler(_f_handler)

        # Global severity level affects _c and _f handlers.
        # Allow minimum severity.
        self.logger.setLevel(logging.DEBUG)
        
        self.ready = True

    def deinit(self):
        '''Delete Logger() instance'''
        if not self.ready:
            return
        
        logging.shutdown()
        self.logger.handlers.clear()
        self.ready = False

    def debug(self, msg):
        if self.ready:
            self.logger.debug(msg)

    def info(self, msg):
        if self.ready:
            self.logger.info(msg)

    def warning(self, msg):
        if self.ready:
            self.logger.warning(msg)
            
    def error(self, msg):
        if self.ready:
            self.logger.error(msg)
    
    def critical(self, msg):
        if self.ready:
            self.logger.critical(msg)
        
    def progress(self, msg):
        if self.ready:
            self.logger.log(self.PROGRESS, msg)
    

LOGGER_CF = LoggerConsFile()