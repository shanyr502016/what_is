

import calendar
import time
from datetime import datetime


class DateTime:


    @staticmethod
    def get_timestamp(timezone=None):
        """
        Returns the current local time as datetime object.
        """
        return datetime.now(tz=timezone)


    @staticmethod
    def get_utc():
        """
        Returns the current time as UTC in milliseconds
        """
        return int(round(time.time() * 1000))   
    
    def get_datetime(format=None):
        """
        Returns the datatime with custom format
        """
        
        if format is None:
            return datetime.now()
        return datetime.now().strftime(format)


    @staticmethod
    def get_filename_timestamp(timestamp=None):
        """
        Converts a timestamp to a string representation that can be used as filename.
        """

        if timestamp is None:
            timestamp = DateTime.get_timestamp()
        return timestamp.strftime("%Y%m%d_%H%M")