# Notification
from corelib.Loggable import Loggable
from corelib.Process import Process
import json

class Notification(Loggable):

    def __init__(self, ssh_hostname = ''):

        super().__init__(__name__)
        
        self.__ssh_hostname = ssh_hostname
        
    def send_notification(self, content, url):
        args = []
        if self.__ssh_hostname:
            args.append(self.__ssh_hostname)   
        original_string = f'{content}'
        args.append("'curl -v -X POST ")
        args.append('-H "Content-Type: application/json"')
        args.append('-d')
        # Convert the original string into properly escaped JSON format
        escaped_string = json.dumps(original_string)
        # Append the properly escaped JSON string to args
        args.append(escaped_string)
        args.append(f"{url}'")
        args = ' '.join([str(elem) for elem in args])
        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        result = process.execute() 
        return result
        