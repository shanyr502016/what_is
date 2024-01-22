import logging
from threading import Lock
import builtins
import time
import sys
import re
from logging import StreamHandler
from corelib.DateTime import DateTime
from corelib.Constants import Constants
import os


class CustomConsoleFormatter(logging.Formatter):
    
    def __init__(self, fmt):
           
        super().__init__()
        
        self._fmt = fmt
   
    def format(self, record):
        format_text = None
        if record.levelno == logging.WARNING:
            format_text = Constants.colorize(self._fmt, Constants.TEXT_YELLOW)

        if record.levelno == logging.DEBUG:
            format_text = Constants.colorize(self._fmt, Constants.TEXT_LIGHT_BLUE)
            
        if record.levelno == logging.CRITICAL:
            format_text = Constants.colorize(self._fmt, Constants.TEXT_LIGHT_RED)
            
        if record.levelno == logging.ERROR:
            format_text = Constants.colorize(self._fmt, Constants.TEXT_RED)
            
        if record.levelno == logging.INFO:
            format_text = Constants.colorize(self._fmt, Constants.TEXT_WHITE)
              
        formatter = logging.Formatter(format_text)
        return formatter.format(record)
            

class LogConfigProvider:

    def __init__(self):       
       
        self._console_log_level = logging.DEBUG

        self._log_file_name = None

    def set_console_log_level(self, log_level):
        self._console_log_level = log_level

    def set_log_file(self, log_file):
        self._log_file_name = log_file

    def get_log_file(self): 
        
        return self._log_file_name  

    def get_console_log_level(self): 
        
        return self._console_log_level  

    def _get_log_format_console(self):
        
        format_text = "[%(levelname)s]: %(message)s"
        return format_text
    
    def get_dita_log_path(self):

        return os.getenv('DITA_LOG_LOCATION')

    def _get_log_format_file(self):
        return '%(levelname)-.1s %(asctime)-.19s %(threadName)s [%(name)s] %(message)s' 

    @classmethod
    def generate_logfilename(cls, module_name, package_info = '', tc_package_id = ''):

        timestamp = DateTime.get_filename_timestamp()

        if package_info.__ne__('deployment'):
            path = os.path.join(cls.get_dita_log_path(cls),os.pardir,'startstop_logs')
        else:
            path = os.path.join(cls.get_dita_log_path(cls), tc_package_id, 'logs')
        if not os.path.exists(path):
            os.makedirs(path)

        _log_file_name = path + '/'+ str(timestamp) + '_' + module_name  + '.log'    

        return _log_file_name      
        
           
    def get_handlers(self):
        handlers = []
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.get_console_log_level())  
        console_handler.setFormatter(CustomConsoleFormatter(self._get_log_format_console()))
        handlers.append(console_handler)
        if self.get_log_file():
            fileHandler = logging.FileHandler(str(self.get_log_file()))     
            fileHandler.setLevel(level=logging.DEBUG)
            fileHandler.setFormatter(logging.Formatter(self._get_log_format_file()))
            handlers.append(fileHandler)

        return handlers
    
    
class Loggable:

    __lock = Lock()
    

    def __init__(self, name: str):

        super().__init__()

        self._name = name

        self.log = Loggable.create_logger(name)

    def create_logger(name: str):
        config_provider = Loggable.get_config_provider()
        Loggable.__lock.acquire()
        try:
            logger = logging.getLogger(name)
            logger.handlers = []
            logger.setLevel(logging.DEBUG)        
            
            for handler in config_provider.get_handlers():
                logger.addHandler(handler)
        finally:
            Loggable.__lock.release()
        return logger

    @staticmethod
    def get_config_provider():

        if 'LOG_CONFIG_FACILITY' in __builtins__:
            config_provider = __builtins__['LOG_CONFIG_FACILITY']
        else:
            # no custom config provider set - create new
            config_provider = LogConfigProvider()
            Loggable.set_config_provider(config_provider)
        return config_provider


    @staticmethod
    def set_config_provider(config_provider: LogConfigProvider):

        builtins.LOG_CONFIG_FACILITY = config_provider

        logger_dict = logging.Logger.manager.loggerDict

        try:
            Loggable.__lock.acquire()
            for logger_instance in logger_dict.values():
                if not isinstance(logger_instance, logging.Logger):
                    continue
                # Close all old handlers
                for handler in logger_instance.handlers:
                    handler.close()
                logger_instance.handlers = []

                # Add new handlers
                for handler in config_provider.get_handlers():
                    logger_instance.addHandler(handler)
        finally:
            Loggable.__lock.release()

    @staticmethod
    def shutdown():
        logging.shutdown()
            
    def print_raw(message):        
        print(message)
    
    @staticmethod    
    def log_success(self, cmsg):
        
        return self.log.info('\033[92m' + cmsg + '\033[0m')
    

    def log_subprocess_output(self, pipe):
        """
        Find the error message from std out from process execution 
        """  
        errorLine = []
        for std_out_line in iter(pipe.readline, b''):
            if std_out_line.decode('utf-8').rstrip().__ne__(''):

                if re.search(r"error",std_out_line.decode('utf-8').rstrip().lower()):
                    self.log.error(std_out_line.decode('utf-8').rstrip())
                    errorLine.append(std_out_line.decode('utf-8').rstrip())
                elif re.search(r"fail",std_out_line.decode('utf-8').rstrip().lower()):
                    self.log.error(std_out_line.decode('utf-8').rstrip())
                    errorLine.append(std_out_line.decode('utf-8').rstrip())
                else:
                    self.log.debug(std_out_line.decode('utf-8').rstrip())
        return errorLine
