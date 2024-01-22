
from corelib.Loggable import Loggable
from argparse import Namespace
from pykeepass import PyKeePass
from corelib.Encryption import Encryption
import json

class KeePass(Loggable):
    """
    KeePass File Read Classes and Functions
    """
    def __init__(self):
         
        super().__init__(__name__)
        
        self._encryption = Encryption()      
        
                
    def get_keepass(self, keepass_file, keepass_password, environment_name):
    
        #_encrpyt_pass = self._encryption.encrypt(keepass_password)       
        
        _decrpyt_pass = self._encryption.decrypt(keepass_password)
                
        kp = PyKeePass(keepass_file, password=_decrpyt_pass) 
        
        root_group = kp.root_group
        
        keepass_data = self.convert_to_json(root_group)['groups']
        
        # Convert Python dictionary to JSON string
        #json_string = json.dumps(json_data, indent=4)
        
        # Search for a dictionary with a specific key-value pair
        filtered_data = {
            'Jenkins': [item for item in keepass_data if item.get('name') == 'Jenkins'],
            environment_name: [item for item in keepass_data if item.get('name') == environment_name]
        }
        #found_items = [item for item in keepass_data if item.get('name') == environment_name]
               
        return filtered_data

        
    def convert_to_json(self, group):
        result = {'name': group.name, 'groups': [], 'entries': []}
    
        # Convert subgroups
        for subgroup in group.subgroups:
            result['groups'].append(self.convert_to_json(subgroup))
        
        # Convert entries
        for entry in group.entries:
            entry_dict = {
                'title': entry.title,
                'username': entry.username,
                'password': entry.password,
                'url': entry.url,
                'note': entry.notes,
                'expires': entry.expires
                # Add more properties here if needed
            }
            result['entries'].append(entry_dict)
        
        return result
 
        