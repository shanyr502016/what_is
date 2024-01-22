"""
TCRelease Management 
"""
import os
from corelib.Loggable import Loggable
from corelib.SSHConnection import SSHConnection
from corelib.File import BaseFile, File, Directory
from corelib.DynamicExecutor import DynamicExecutor
from corelib.RemoteExecutor import RemoteExecutor
from corelib.Constants import Constants
from corelib.ExceptionHandler import BMIDEException, DLLsException
from build.lib.TCBuildConfig import TCBuildConfig
from build.lib.TCLib import TCLib

class TCRelease(Loggable):
    
    def __init__(self, args):   

        super().__init__(__name__)
              
        self.__arguments = args # Set arguments from DynamicImporter
        
        self.__environment = args._environment # Get the Environment Specific Values from config json
        
        self.__environment_provider = args._environment_provider # Get the Environment Provider method. Reusable method derived
    
        self.__module_name = args._module_name # Module name from user command line (Only Module (classname))
        
        self.__module = args._arguments.module # Module name with submodule from user command line (full name)
        
        self.__module_label = self.__module # Module label  
     
        self.__properties = args._properties # Get the Module Specific Values from config json

        self.__security = args._security # Get the Security Values
        
        self.__sub_module_name = args._sub_module_name # Sub Module name from user command line (Only Sub Module (classname))
        
        self.__target = None # Target Instances setup
        
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name) # Scope and target setup based on configuration


        self._processes = []
        self._processesResult = []
        
        self.tc_build_config = TCBuildConfig(self.__arguments)
        self.tc_lib = TCLib(self.__arguments)
        
    def default(self):        
        return self._executeTargets()
        
        
    def updatepreferencesversion(self):
        """ Update the Preferences Version

        Returns:
            _type_: _description_
        """
    
        if 'executeTargets' in self.__properties[self.__target]:

            self._executeCombineTargets()

        else:
    
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
            
            for index, server_info in enumerate(_execute_servers):

                

                if self.tc_build_config.get_workspace() and self.tc_build_config.get_branch() and self.tc_build_config.get_package_name():        
                      
                    __ssh_command = self.__environment_provider.get_ssh_command(server_info)
                    
                    packages_lists = self.__properties[self.__target]['packages']
                    
                    for package_name in packages_lists:
                    
                        package_name = package_name.split(':')
                        
                        preferences_version_file = os.path.join(self.tc_build_config.get_workspace(), package_name[0], self.__properties[self.__target]['location_in_package']) 

                        full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())
                        
                        self.log.info(f"Preferences Version File: {preferences_version_file}")
                        if __ssh_command:
                            ssh_client = None
                            try:
                                ssh_client = SSHConnection(server_info['USERNAME'],server_info['HOSTNAME'])
                                # Read the remote XML file and update package name                                           
                                _updated_preferences_version = File(preferences_version_file).remote_find_replace_content(ssh_client, f"{self.__properties[self.__target]['pattern']}", f">{full_package_name}</")
                                self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': '', 'label': f"Update Preferences Version"})
                                self.__console_msg( _updated_preferences_version, f"{preferences_version_file} - {full_package_name} Updated ")
                            except Exception as e:
                                print(f"Remote connection failed: {e}")
                            finally:
                                ssh_client.close()
                        else:
                            _updated_preferences_version = File(preferences_version_file).find_replace_content(f"{self.__properties[self.__target]['pattern']}", f">{full_package_name}</")
                            self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': '', 'label': f"Update Preferences Version"})
                            self.__console_msg( _updated_preferences_version, f"{preferences_version_file} - {full_package_name} Updated ")
                    
            return self._processes
        
        
    def updatetcversion(self):

        """ Update Teamcenter Version in BMIDE media_teamcenter_{}.xml """
    
        if 'executeTargets' in self.__properties[self.__target]:

            self._executeCombineTargets()

        else:
    
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
            
            for index, server_info in enumerate(_execute_servers):

                        
                if self.tc_build_config.get_workspace() and self.tc_build_config.get_tc_version():    
                    __ssh_command = self.__environment_provider.get_ssh_command(server_info)

                    self.log.info(f"TC Version: {self.tc_build_config.get_workspace()}")             
                    
                        
                    packages_lists = self.__properties[self.__target]['packages']


                    for package_name in packages_lists:
                    
                        package_name = package_name.split(':')            
                        
                        media_teamcenter_file = os.path.join(self.tc_build_config.get_workspace(), package_name[0], '01_bmide', package_name[1], 'install', f'media_teamcenter_{package_name[1]}.xml')
                        self.log.info(f"Media Teamcenter File: {media_teamcenter_file}")
                        if __ssh_command:
                            ssh_client = None
                            try:
                                ssh_client = SSHConnection(server_info['USERNAME'],server_info['HOSTNAME'])
                                # Read the remote XML file                                           
                                _updated_tc_version = File(media_teamcenter_file).remote_find_replace_content(ssh_client, f"<<<{self.__properties[self.__target]['pattern']}>>>", self.tc_build_config.get_tc_version())
                                self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': '', 'label': f"Update TC Version"})
                                self.__console_msg( _updated_tc_version, f"{media_teamcenter_file} - {self.tc_build_config.get_tc_version()} Updated ")
                            except Exception as e:
                                self.log.error(f"Exception: {e}")
                            finally:
                                ssh_client.close()
                        else:
                            _updated_tc_version = File(media_teamcenter_file).find_replace_content(f"<<<{self.__properties[self.__target]['pattern']}>>>", self.tc_build_config.get_tc_version())
                            self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': '', 'label': f"Update TC Version"})
                            self.__console_msg( _updated_tc_version, f"{media_teamcenter_file} - {self.tc_build_config.get_tc_version()} Updated ")
                    
            return self._processes
                    

    
    def _executeCombineTargets(self):
        try:
            for thread_count, targets in enumerate(self.__environment_provider.get_execute_targets(self.__target).split(',')):
                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name

                if dynamicExecutor.get_sub_module_name():  
                    _processesResult = getattr(TCRelease, dynamicExecutor.get_sub_module_name())(self)
                else:
                    _processesResult = dynamicExecutor.run_module()
                self._processesResult = self._processesResult + _processesResult  
            return self._processesResult
        except Exception as exp:
            self.log.error(exp)
            
    def __console_msg(self, result, action_msg):
        
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')