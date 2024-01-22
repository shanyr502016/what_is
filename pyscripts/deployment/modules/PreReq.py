import os
import shutil
import re

from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.SCP import SCP
from corelib.File import Directory
from corelib.Constants import Constants

class PreReq(Loggable):
    
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
                
        self.log.info("PreReq Copy All")        
        return self._executeTargets()  
    

    def Check(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        for index, server_info in enumerate(_execute_servers):
            
            _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))
            _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))
            _is_linux = self.__environment_provider.is_linux(server_info['OS_TYPE'])
            _is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            
            __ssh_command = self.__environment_provider.get_ssh_command(server_info)
            
            _check_system_variables = True           

            if _is_windows:
            
                if _check_system_variables:

                    _SYSTEM_VARIABLES_WIN = self.__properties[self.__target]['SYSTEM_VARIABLES_WIN']
                    
                    for sindex, system_variables in enumerate(_SYSTEM_VARIABLES_WIN):
                                    
                        command = f'echo %{system_variables}%'
                        
                        if __ssh_command == '':
                            args = []
                        else:
                            args = [__ssh_command]                    
                        args.append(f'"{command}"')                
                        args = ' '.join([str(elem) for elem in args])                
                        result = self._execute(args)            
                        _check_path = _scp_with_ssh.check_dir_to_remote(self.__environment_provider.is_windows(server_info['OS_TYPE']), result[0].replace("\\","\\\\"))
                        
                        if _check_path: 
                            self.__console_msg(0, f'{system_variables} Environment variable is available on {server_info["HOSTNAME"]}')
                        else:
                            self.__console_msg(1, f'{system_variables} Environment variable is not available on {server_info["HOSTNAME"]}')
                            
            


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
                        _processesResult = getattr(PreReq, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult             
        except Exception as exp:
            self.log.error(exp)              
            
    def _execute(self, command, path=''):
        
        """ Used to process services/command
        """
        process = Process(command, path)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        process.execute()
        return process.get_out_lines() 
     
    def __console_msg(self, result, action_msg):
        
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg}.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg}")
        self.log.info('..............................................................')