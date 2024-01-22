from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.File import Directory
from corelib.File import File
from corelib.Constants import Constants


from corelib.SCP import SCP
import os
import re

class CopySoDLL(Loggable):
    
    def __init__(self, args):   

        super().__init__(__name__)

        self.__arguments = args # Set arguments from DynamicImporter
                
        self.__environment = args._environment # Get the Environment Specific Values from config json
    
        self.__properties = args._properties # Get the Module Specific Values from config json

        self.__environment_provider = args._environment_provider # Get the Environment Provider method. Reusable method derived

        self.__module_name = args._module_name # Module name from user command line (Only Module (classname))
        
        self.__module = args._arguments.module # Sub Module name from user command line (Only Sub Module (classname))
        self.__module_label = self.__module

        self.__sub_module_name = args._sub_module_name 

        self._tcpackage_id = args._tcpackage_id # Target Teamcenter Package ID get from user command line
        
        self.__target = None # Target Instances setup

        self.__remote_execution = False # Remote Execution.

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel

        if self.__sub_module_name: # Scope and target setup based on configuration
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
            
    def default(self):
                
        self.log.info("CopySoDLL All File")        
        return self._executeTargets()         


    def SO(self):
        """ 
        Action: Copy SO Files
        Command:  scp -pr source location destination location
        """  
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        
    
        for index, server_info in enumerate(_execute_servers):
            self.log.info("SO File Copying Started..") 

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                try:
                    if os.path.exists(_location_in_package): 
                        
                        if os.path.exists(_location_in_package):

                            so_target_path = server_info['SO_PATH'] 
                            if self.mkdir_remote(so_target_path, self.__environment_provider, server_info) == 0:
                                result = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(_location_in_package + '/*', so_target_path, self._parallel)
                                self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - Copy SO files to {so_target_path}"})
                                if not self._parallel:
                                    self.__console_msg(result, f"[{tc_package_id}] - Copy SO files to {so_target_path}")
                            
                            else:
                                self.log.warning(f"Directory not exists. Please check permission. [{tc_package_id}] - {self.__target} Skipped")
                        else:
                            self.log.warning(f"Required Package Folder not Present from this location [{tc_package_id}]. {self.__target} Skipped")           
                    else:
                        self.log.warning(f"Required Package Folder not Present from this location [{tc_package_id}]. {self.__target} Skipped")

                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - Copy SO files"})
        return self._processes
                    
               
                      
    def DLL(self):
        """ 
        Action: Copy DLLFiles
        Command:  scp -pr sourcelocation destinationlocation
        """ 
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])  
      
        self.log.info(f'{self.__target}')  
        for index, server_info in enumerate(_execute_servers):

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                try:
                    if os.path.exists(_location_in_package):
                        
                        if os.path.exists(_location_in_package):
                        
                            self.log.info("DLL File Copying Started..")
                            
                            dll_target_path = server_info['DLL_PATH']
                            
                            if self.mkdir_remote(dll_target_path, self.__environment_provider, server_info) == 0:                            
                                result = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(_location_in_package + '/*', dll_target_path, self._parallel)
                                self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - Copy {self.__target} files to {dll_target_path}"})
                                if not self._parallel:
                                    self.__console_msg(result, f"[{tc_package_id}] - Copy {self.__target} files to {dll_target_path}")
                            else:
                                self.log.warning(f"Directory not exists. Please check permission. [{tc_package_id}] - {self.__target} Skipped")
                        else:
                            self.log.warning(f"Required Package Folder not Present from this location [{tc_package_id}]. {self.__target} Skipped")
                    else:
                        self.log.warning(f"Required Package Folder not Present from this location [{tc_package_id}]. {self.__target} Skipped")

                except Exception as exp:                    
                    self.log.error(f'{exp}')
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - Copy {self.__target} files "})
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
                        _processesResult = getattr(CopySoDLL, dynamicExecutor.get_sub_module_name())(self)
                    else:
                        _processesResult = dynamicExecutor.run_module()   
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult             
        except Exception as exp:
            self.log.error(exp)
            
   
    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Copied Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Copied Failed.")
        self.log.info('..............................................................')
        
        

    
    def mkdir_remote(self, targetpath, environment_provider, server_info):       
        
        __ssh_command = environment_provider.get_ssh_command(server_info)

        try:
            args = [__ssh_command]            
            if environment_provider.is_windows(server_info['OS_TYPE']):
                targetpath = targetpath.replace("/","\\")                 
                targetpath = '"' + targetpath + '"'                
                args.append('if not exist ' + targetpath  + ' mkdir ' + targetpath)
            else:
                args.append(f'mkdir -p {targetpath}')                         
            args = ' '.join([str(elem) for elem in args])
            process = Process(args)
            process.hide_output()
            process.collect_output()
            process.ignore_errors()
            return process.execute()
                
        except (Exception) as err:
            self.log.error(err)
            return 1
