
import os
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.SCP import SCP
from corelib.File import Directory



class DitaReplacements(Loggable):
    
    def __init__(self, environment_provider): 
        
        super().__init__(__name__)

        self._environment_provider = environment_provider

        self._directory = Directory()

        self._parallel = False


    def _getDitaProperties(self, tc_package_id, server_info, location_in_package, excludes_replacements, parallel):

        _properties_config_in_package = self._environment_provider.get_location_in_package(tc_package_id, '05_dita')

        _copytoreplacementdir = 0

        properties_file = location_in_package.replace("/","__") + '.properties'

        if os.path.exists(os.path.join(_properties_config_in_package, self._environment_provider.get_environment_name())):

            self._parallel = parallel

            _scp_without_ssh = SCP(self._environment_provider.get_ssh_command(server_info, True))

            _scp_with_ssh = SCP(self._environment_provider.get_ssh_command(server_info))

            replacement_foldername = 'deploy_'+self._environment_provider.get_environment_name().lower()

            _replacement_path = self._environment_provider.get_location_in_package(tc_package_id, replacement_foldername)

            _excludes_extension = [".exe", ".jar", ".lib", ".so", ".bin",".50", '.crt', '.cer', '.sha256', '.lst', '.mf']

            if os.path.exists(os.path.join(_replacement_path, location_in_package)):
                self._directory.removedirs(os.path.join(_replacement_path, location_in_package))

            if not os.path.exists(os.path.join(_replacement_path, location_in_package)):
                os.makedirs(os.path.join(_replacement_path, location_in_package))

            _replacement_properties_path = os.path.join(_properties_config_in_package,self._environment_provider.get_environment_name())

            _package_location = self._environment_provider.get_location_in_package(tc_package_id)            
            
            properties_name = ''.join(properties_file.split('.')[:-1]).split('__')

            if len(properties_name) == 1:
                if not os.path.exists(os.path.join(_replacement_path,(''.join(properties_name)))):
                    os.makedirs(os.path.join(_replacement_path,(''.join(properties_name))))
                if len(os.listdir(os.path.join(_package_location,'/'.join(properties_name)))) > 0:
                    _copytoreplacementdir = SCP('').copy_to_local(os.path.join(_package_location,''.join(properties_name),'*'),os.path.join(_replacement_path,''.join(properties_name)))
                    self._environment_provider.change_execmod(_replacement_path)
                    if _copytoreplacementdir == 0:
                        if os.path.exists(os.path.join(_replacement_properties_path, properties_file)):
                            return self._updateProperties(os.path.join(_replacement_properties_path,properties_file), _replacement_path, _excludes_extension, excludes_replacements, ''.join(properties_name), server_info)
                        else:
                            return self._updateProperties(os.path.join(_replacement_properties_path,properties_file), _replacement_path, _excludes_extension, excludes_replacements, '/'.join(properties_name), server_info, property_file_exist = False)
                    else:
                        return _copytoreplacementdir
                else:
                    return _copytoreplacementdir
            else:
                if not os.path.exists(os.path.join(_replacement_path,('/'.join(properties_name)))):
                    os.makedirs(os.path.join(_replacement_path,('/'.join(properties_name))))
                if len(os.listdir(os.path.join(_package_location,'/'.join(properties_name)))) > 0:
                    _copytoreplacementdir = SCP('').copy_to_local(os.path.join(_package_location,'/'.join(properties_name), '*'),os.path.join(_replacement_path,'/'.join(properties_name)))
                    self._environment_provider.change_execmod(_replacement_path)
                    if _copytoreplacementdir == 0:
                        if os.path.exists(os.path.join(_replacement_properties_path, properties_file)):
                            return self._updateProperties(os.path.join(_replacement_properties_path,properties_file), _replacement_path, _excludes_extension, excludes_replacements, '/'.join(properties_name),server_info)
                        else:
                            return self._updateProperties(os.path.join(_replacement_properties_path,properties_file), _replacement_path, _excludes_extension, excludes_replacements, '/'.join(properties_name), server_info, property_file_exist = False)
                    else:
                        return _copytoreplacementdir
                else:
                    return _copytoreplacementdir

        else:
            self.log.warning(f'Dita Properties not avaliable {_properties_config_in_package}')
            return _copytoreplacementdir


    def _updateProperties(self, properties_file_path, replacement_path, _excludes_extension, _excludes_replacements, replacement_location, server_info, property_file_exist = True):
        try:
            property_update_status = 1
            properties = {}
            if property_file_exist:
                properties = self._environment_provider.read_properties_file(properties_file_path)
            for dirpath, dirnames, filenames in os.walk(os.path.join(replacement_path, replacement_location)):                    
                dirnames[:] = [d for d in dirnames if d not in _excludes_replacements]
                for fname in filenames:                    
                    if not fname.endswith(tuple(_excludes_extension)):
                        fullname = os.path.join(dirpath, fname)
                        if os.path.exists(fullname):  
                            if property_file_exist:
                                try:
                                    with open(fullname, 'r', encoding='utf-8', errors='ignore') as fin:
                                        filedata = fin.read()
                                        for patternkey in properties.keys():                                            
                                            if properties[patternkey].__eq__('DITA_EMPTY_STRING'):
                                                filedata = filedata.replace(f'<<<{patternkey}>>>','')
                                            elif patternkey.endswith(f'.{server_info["NODE"]}'):
                                                pattern_key = patternkey.replace(f'.{server_info["NODE"]}', '')
                                                filedata = filedata.replace(f'<<<{pattern_key}>>>',properties[patternkey])
                                            else:
                                                filedata = filedata.replace(f'<<<{patternkey}>>>',properties[patternkey])
                                    with open(fullname, 'w') as fout:
                                        fout.write(filedata)
                                except FileNotFoundError:
                                    self.log.error(f"File '{fullname}' not found.")
                                except IOError as e:
                                    self.log.error(f"Error reading file '{fullname}': {e}")
                                except Exception as e: # Exception Handling
                                    self.log.error(f"An unexpected error occurred: {e}")
                            try:
                                with open(fullname, 'r', encoding='utf-8', errors='ignore') as fin: 
                                    filedata = fin.read()
                                    lines = filedata.split('\n')
                                    for line in lines:
                                        if '<<<DITA' in line:
                                            self.log.error(f"Replacement Line: {line}")
                                            self.log.error(f"Failed to replace properties: Missing properties or potential spelling mistakes detected.")
                                            self.log.error(f"{fullname}")                                            
                                            self.log.debug(f"Properties: {properties_file_path}")
                                            property_update_status = 1
                                            return property_update_status
                            except FileNotFoundError:
                                self.log.error(f"File '{fullname}' not found.")
                                return 1
                            except IOError as e:
                                self.log.error(f"Error reading file '{fullname}': {e}")
                                return 1
                            except Exception as e:
                                self.log.error(f"An unexpected error occurred: {e}")
                                return 1

                property_update_status = 0  
            self.log.info(f'Updated the Dita Properties [{properties_file_path}]')
            return property_update_status
        except Exception as exp:
            self.log.error(f'Update Properties are failed. {exp}')
            return 1
