"""
clearlocks deployment activities
"""
from corelib.Loggable import Loggable
import os
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants
from corelib.SCP import SCP
import tempfile


class Clearlogs(Loggable):
    
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

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel

        """
        Remote Execution.
        """
        self.__remote_execution = False 
        """
        Scope and target setup based on configuration
        """   
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
        
        
    def default(self):
                
        self.log.info("Clearlogs")
        return self._executeTargets() 
    

    def webserver(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        for index, server_info in enumerate(_execute_servers):

            is_linux = self.__environment_provider.is_linux(server_info['OS_TYPE'])
            is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])

            if is_linux: 

                _ssh_with_scp = SCP(self.__environment_provider.get_ssh_command(server_info))

                _logs_paths = self.__properties[self.__target]['logs_path']

                for i in range(len(_logs_paths)):
                    for key, value in server_info.items():
                        _logs_paths[i] = _logs_paths[i].replace(f"${key}", str(value))

                for log_path in _logs_paths:
                    _check_path = log_path
                    _is_path = True
                    if '*' in log_path:
                        _is_path = False
                        _check_path = os.path.dirname(log_path)                        
                    _check_dir_result = _ssh_with_scp.check_dir_to_remote(is_windows,_check_path)
                    if _check_dir_result: 
                        _result =  _ssh_with_scp.remove_file_to_remote(is_windows,log_path,is_path = _is_path)
                        self.__console_msg(_result,f'Clearlogs Webserver [{log_path}]')
                        self._processes.append({'NODE':server_info['NODE'],'process': _result, 'module': self.__module_label, 'package_id': '', 'label': f"Temp dir delete"})
                    else:
                        self.log.warning(f'[{log_path}] No logs files are avaliable')
                        self._processes.append({'NODE':server_info['NODE'],'process': _check_dir_result, 'module': self.__module_label, 'package_id': '', 'label': f"Temp dir delete"})
                
        return self._processes       

        
    def delete(self):
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        

        for index, server_info in enumerate(_execute_servers):
        
            is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            
            if is_windows:
        
                if "LOGS_LOCATION_WIN" in self.__environment:
                    _logs_paths=self.__environment["LOGS_LOCATION_WIN"]
                else:
                    _logs_paths=[]
            else:
                if "LOGS_LOCATION" in self.__environment:
                    _logs_paths=self.__environment["LOGS_LOCATION"]
                else:
                    _logs_paths=[]       
            
            
            _ssh_with_scp = SCP(self.__environment_provider.get_ssh_command(server_info))           
            
            
            for i in range(len(_logs_paths)):
                for key, value in server_info.items():
                    _logs_paths[i] = _logs_paths[i].replace(f"${key}", str(value))

            if is_windows:
                _temp_dir= server_info['DEPLOYMENT_CENTER_TEMP_DIR']
            else:
                _temp_dir ='/tmp'

            for log_path in _logs_paths:
                if '*' in log_path and 'delete_threshold' in self.__properties[self.__target]:

                    _no_of_days = self.__properties[self.__target]['delete_threshold']
                    _collect_list_of_files = _ssh_with_scp.get_files_from_remote(log_path,is_windows,threshhold = _no_of_days) 
                    
                    if len(_collect_list_of_files):
                        _result = _ssh_with_scp.remove_multiple_files_to_remote(is_windows,_collect_list_of_files,_temp_dir)
                        self.__console_msg(_result,f'Clearlogs delete [{log_path}]')
                        self._processes.append({'NODE':server_info['NODE'],'process': _result, 'module': self.__module_label, 'package_id': '', 'label': f"Temp dir delete"})                    
                    else:
                        self.log.warning(f'[{log_path}] No logs files are avaliable')
                        self._processes.append({'NODE':server_info['NODE'],'process': 0, 'module': self.__module_label, 'package_id': '', 'label': f"Temp dir delete"})

                else:
                    _check_path = log_path
                    _is_path = True
                    if '*' in log_path:
                        _is_path = False
                        _check_path = os.path.dirname(log_path)
                        
                    _check_dir_result = _ssh_with_scp.check_dir_to_remote(is_windows,_check_path)
                    if _check_dir_result:  
                        _result =  _ssh_with_scp.remove_file_to_remote(is_windows,log_path,is_path = _is_path)
                        self.__console_msg(_result,f'Clearlogs delete [{log_path}]')
                        self._processes.append({'NODE':server_info['NODE'],'process': _result, 'module': self.__module_label, 'package_id': '', 'label': f"Temp dir delete"})
                    else:
                        self.log.warning(f'[{log_path}] No logs files are avaliable')
                        self._processes.append({'NODE':server_info['NODE'],'process': _check_dir_result, 'module': self.__module_label, 'package_id': '', 'label': f"Temp dir delete"})
                
        return self._processes
                      
    def win(self):
        return self._executeCombineTargets()

    def lnx(self):
        return self._executeCombineTargets()
    
    def _executeCombineTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__target).split(',')):
                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name
                if dynamicExecutor.get_sub_module_name():    
                    _processesResult = getattr(Clearlogs, dynamicExecutor.get_sub_module_name())(self)
                else:
                    _processesResult = dynamicExecutor.run_module()
                self._processesResult = self._processesResult + _processesResult  
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
                        _processesResult = getattr(Clearlogs, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult                     
        except Exception as exp:
            self.log.error(exp)

    def _execute(self, command):

        """ Used to process services/command
        """
        process = Process(command)
        process.set_parallel_execution(self._parallel)
        return process.execute()


    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg}  Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg.capitalize()} Execution Failed.")
        self.log.info('..............................................................')