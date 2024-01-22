""" Properties """

import os
from corelib.Loggable import Loggable
from corelib.Constants import Constants

class Properties(Loggable):
    
    def __init__(self, args):   

        super().__init__(__name__)
        
        self.__arguments = args # get arguments from DynamicImporter

        self.__environment_provider = args._environment_provider # Get the Environment Provider method. Reusable method derived





    def get_properties_from_files(self, package_location, properties_name, excludes_extension, excludes_replacements):       

        properties_package_location = os.path.join(package_location, '/'.join(properties_name))

        #set to check if any properties not present in the properties file 
        
        properties_present_data = []

        for dirpath, dirnames, filenames in os.walk(properties_package_location):

            dirnames[:] = [d for d in dirnames if d not in excludes_replacements]

            for fname in filenames:

                if not fname.endswith(tuple(excludes_extension)):

                    fullname = os.path.join(dirpath, fname)

                    if os.path.exists(fullname):
                        
                        try:
                            properties_present_in_files = set()
                            with open(fullname, 'r', encoding='utf-8', errors='ignore') as fin:
                                filedata = fin.read()

                                lines = filedata.split('\n')
                                for line in lines:
                                    if '<<<DITA' in line:
                                        prop_name = line.split('<<<')[1].split('>>>')[0].strip()
                                        properties_present_in_files.add(prop_name)
                            properties_present_data.append({'property_filename': fullname, 'property_keys': properties_present_in_files})    
                        except FileNotFoundError:
                            self.log.error(f"File '{fullname}' not found.")
                            return 1
                        except IOError as e:
                            self.log.error(f"Error reading file '{fullname}': {e}")
                            return 1
                        except Exception as e:
                            self.log.error(f"An unexpected error occurred: {e}")
                            return 1
        return properties_present_data