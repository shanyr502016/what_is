import os
import shutil
import re

from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.SCP import SCP
from corelib.File import Directory
from corelib.Constants import Constants

class WebDV(Loggable):
    
    def __init__(self, args):   

        super().__init__(__name__)
        
        """
        Set arguments from DynamicImporter
        """         
        self.__arguments = args
        
        """
        Get the Environment Specific Values from config json
        """        
        self.__environment = args._environment
        """
        Get the Module Specific Values from config json
        """        
        self.__properties = args._properties
        """
        Get the Environment Provider method
        Reusable method derived
        """        
        self.__environment_provider = args._environment_provider
        """
        Module name from user commandline (Only Module (classname))
        """       
        self.__module_name = args._module_name

        self.__module = args._arguments.module
        self.__module_label = self.__module
        """
        Sub Module name from user commandline (Only Sub Module (classname))
        """
        self.__sub_module_name = args._sub_module_name

        """
        Target Teamcenter Package ID get from user commandline
        """        
        self._tcpackage_id = args._tcpackage_id

        """
        Target Instances setup
        """        
        self.__target = None
        """
        Remote Execution.
        """
        self.__remote_execution = False 

        self._directory = Directory()

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel
        
        """
        Scope and target setup based on configuration
        """ 
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
        
        
    def default(self):
                
        self.log.info("WEBDV Deploy")        
        return self._executeTargets()  
    
    def deploy(self):
        
        if 'executeTargets' in self.__properties[self.__target]:

            return self._executeCombineTargets()

        else:

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
            _target_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['targetServer'])

            for index, server_info in enumerate(_execute_servers):   

                for index, target_server_info in enumerate(_target_servers):

                    try:                    
                        is_linux = self.__environment_provider.is_linux(server_info['OS_TYPE'])
                        is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
                        _ssh_with_scp_source_server = SCP(self.__environment_provider.get_ssh_command(server_info))
                        _ssh_with_scp_target_server = SCP(self.__environment_provider.get_ssh_command(target_server_info))
                        _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(target_server_info, True))

                        _warFile = server_info['WEBDV_WAR_FILE']
                        
                        _check_warsource_result = _ssh_with_scp_source_server.check_dir_to_remote(is_windows,_warFile)
                        
                        if _check_warsource_result:             
                                                    
                            _extract_webdv_dir = os.path.join(os.path.dirname(_warFile), f'{os.path.splitext(os.path.basename(_warFile))[0]}_extract')
                            
                            if _ssh_with_scp_source_server.check_dir_to_remote(is_windows,_extract_webdv_dir):
                            
                                _ssh_with_scp_source_server.remove_file_to_remote(is_windows,_extract_webdv_dir,True)                           
                        
                            _unzip_status = _ssh_with_scp_source_server.unzip(_warFile, _extract_webdv_dir)                           
                            
                            if _unzip_status == 0:
                            
                                _update_default_config = os.path.join(_extract_webdv_dir, 'configuration', 'default.xml')
                                
                                if _ssh_with_scp_source_server.check_dir_to_remote(is_windows,_update_default_config):
                                    try:
                                        _filecontent = None
                                        with open(_update_default_config, 'r') as fin:
                                            _filecontent = fin.read()
                                            fin.close()
                                        with open(_update_default_config, 'w') as fout:
                                            _filecontent = _filecontent.replace('${appData.servicePathPrefix}', target_server_info['WEBDV_IF_ICTMETHOD_URL']+'/')
                                            fout.write(_filecontent)
                                            fout.close()
                                    except Exception as e:
                                        self.log.error(e)
                                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '', 'label': "WebDV Failed"})
                                        return 1
                                        
                                    _zip_status = _ssh_with_scp_source_server.zip(_extract_webdv_dir+'.war', _extract_webdv_dir) 
                                    
                                    if _zip_status == 0:                                   
                                    
                                        _copyResult =  _scp_without_ssh.copy_remote_to_remote(_extract_webdv_dir+'.war',target_server_info['WEBDV_TARGET_WAR_FILE'], self.__environment_provider.get_ssh_command(server_info))
                                        self._processes.append({'NODE':server_info['NODE'],'process': _copyResult,'module': self.__module_label, 'package_id': '', 'label': f"WebDV Deployed"})
                                        self.__console_msg(_copyResult, f"{target_server_info['WEBDV_TARGET_WAR_FILE']} War Deployed")
                                        
                                    else:                                    
                                        self.__console_msg(_zip_status, "ZIP Failed")
                                else:                                    
                                    self.__console_msg(0, "Configuration No Present")
                            else:                                    
                                self.__console_msg(_zip_status, "UnZIP Failed")
                                    
                                        
                                                                       
                    except Exception as exp:
                        self.log.error(f'{exp}')
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '', 'label': f"War Deployment"})
            return self._processes

    def _executeCombineTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__target).split(',')):
                self.__target = targets
                
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name               
                
                if dynamicExecutor.get_sub_module_name():  
                    _processesResult = getattr(War, dynamicExecutor.get_sub_module_name())(self)
                else:
                    _processesResult = dynamicExecutor.run_module()
                self._processesResult = self._processesResult + _processesResult               
            dynamicExecutor.set_process_results(self._processesResult)
            return self._processesResult
        except Exception as exp:
            self.log.error(exp)


    def _executeTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__module_name).split(',')): 
                    # Execute with multiple targets
                if not self.__sub_module_name:   
                    self.__target = targets  
                    dynamicExecutor = DynamicExecutor(self.__arguments)   
                    dynamicExecutor.set_module_instance(targets) # module instance name
                    # calling the targets one by one
                    if dynamicExecutor.get_sub_module_name():
                        _processesResult = getattr(War, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult             
        except Exception as exp:
            self.log.error(exp)              
            
    def _execute(self, command, path):
        
        """ Used to process services/command
        """
        process = Process(command, path)
        process.set_parallel_execution(self._parallel)
        return process.execute() 
     
    def __console_msg(self, result, action_msg):
        
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Copied Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Copied Failed.")
        self.log.info('..............................................................')