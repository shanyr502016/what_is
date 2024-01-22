import os
import shutil
import re

from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.SCP import SCP
from corelib.File import Directory
from corelib.Constants import Constants

class TCVis(Loggable):
    
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
                
        self.log.info("TCVis Copy All")        
        return self._executeTargets()  
    
    def deploy(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        for index, server_info in enumerate(_execute_servers):
                for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                    try:

                        _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                        if os.path.exists(_location_in_package) and len(os.listdir(_location_in_package)) > 0: # check package path                            

                            if 'TCVIS_VVCP_PATH' in server_info:

                                tcvis_vvcp_path = server_info['TCVIS_VVCP_PATH']

                                _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))
                                _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

                                _check_vvcp_path = _scp_with_ssh.check_dir_to_remote(self.__environment_provider.is_windows(server_info['OS_TYPE']), tcvis_vvcp_path)

                                if _check_vvcp_path:
                                    _copyResult =  _scp_without_ssh.copy_to_remote(os.path.join(_location_in_package, '*'),tcvis_vvcp_path, self._parallel)
                                    self._processes.append({'NODE':server_info['NODE'],'process': _copyResult,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - TCVis"})
                                    if not self._parallel:
                                        self.__console_msg(_copyResult, f'[{tc_package_id}] - TCVis')
                            else:
                                self.log.warning(f"TCVIS_VVCP_PATH not Present  {tc_package_id}. TCVis Skipped")
                        else:
                            self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. TCVis Skipped")

                    except Exception as exp:
                        self.log.error(f'{exp}')
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - TCVis"})
        return self._processes

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
                        _processesResult = getattr(TCVis, dynamicExecutor.get_sub_module_name())(self)   
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