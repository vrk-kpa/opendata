"""
Logging functions that can handle mixed strings/unicode messages
"""
import unicodedata
import logging
logger = None

def set_config(config):
    """
    set the logger used by this module
    """
    logging.config.fileConfig(config)
    global logger
    logger = logging.getLogger('qa')

class Logger(object):
    def info(self, message):
        try:
            # make sure message is unicode and normalise
            norm = unicodedata.normalize('NFKD', unicode(message))
            # log as ascii
            logger.info(norm.encode('ascii', 'replace'))
        except Exception as e:
            print "Logging error:", e.message

    def error(self, message):
        try:
            # make sure message is unicode and normalise
            norm = unicodedata.normalize('NFKD', unicode(message))
            # log as ascii
            logger.error(norm.encode('ascii', 'replace'))
        except Exception as e:
            print "Logging error:", e.message

log = Logger()
