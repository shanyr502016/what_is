"""
AwcUiConfig deployment activities
"""
import os
import re
 
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants


class AwcUiConfig(Loggable):
    
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

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel
        
        """
        Scope and target setup based on configuration
        """ 
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
        
        
    def default(self): 
        self.log.info(__class__.__name__+' '+'Whole Import Staring')
        return self._executeTargets()         
    
    def tilesDelete(self):

        """
        Action: tilesDelete
        Command:  aws2_install_tilecollections -u= -g= -pf=  -mode= -file
        """ 
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
       
        for index, server_info in enumerate(_execute_servers):

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
              
                self.log.info(f'Tiles Remove')   
                try:
                    if self.__environment_provider.get_property_validation('mode', self.__properties[self.__target]):
                        if os.path.exists(_location_in_package) and self.__properties[self.__target]['mode']:   
                            extra_args = []                         
                            extra_args.append('-mode='+ self.__properties[self.__target]['mode'])
                            extra_args.append('-file='+ _location_in_package)
                            command  = self.__build_arguments(server_info, extra_args)            
                            self.log.info(f"tilesDelete Command: {command}")
                            result = self._execute(command)
                            self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - Awctiles Remove"})
                            if not self._parallel:
                                self.__console_msg(result, f"[{tc_package_id}] - Awctiles Remove")
                        else:
                            self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. TilesDelete Skipped")
                    else:
                        self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. TilesDelete Skipped")
                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - Awctiles Remove"})
        return self._processes

    
    
    def tilesAdd(self):
        """
        Action: tilesAdd
        Command:  aws2_install_tilecollections -u= -g= -pf=  -mode= -file
        """  
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
              
        for index, server_info in enumerate(_execute_servers):

            self.log.info(f'Tiles Add')

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                try:
                    if self.__environment_provider.get_property_validation('mode', self.__properties[self.__target]):
                        #Split mode and command run as per mode set                
                        for mode in self.__properties[self.__target]['mode'].split(','):
                            extra_args = []                        
                            if os.path.exists(_location_in_package):                                                        
                                self.log.info(f'Tiles {mode} Started..')
                                extra_args.append('-mode='+mode)
                                extra_args.append('-file='+_location_in_package)
                                command  = self.__build_arguments(server_info, extra_args)                                
                                self.log.info(f"Tiles {mode} Command: {command}") 
                                result = self._execute(command)
                                self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC Tiles {mode.capitalize()}"})
                                if not self._parallel:
                                    self.__console_msg(result, f"[{tc_package_id}] - AWC Tiles {mode.capitalize()}")                           
                            else:
                                self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. TilesAdd Skipped")
                    else:
                        self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. TilesAdd Skipped")
                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC Tiles"})
        return self._processes
            
            
    
    
    def tilesUpdate(self):
        """
        Action: tilesUpdate
        Command:  aws2_install_tilecollections -u= -g= -pf=  -mode= -file
        """  
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
             
        for index, server_info in enumerate(_execute_servers):

            self.log.info("Tiles Update")

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                
                
                
                try:
                    if os.path.exists(_location_in_package) and self.__properties[self.__target]['mode']:
                        extra_args = []                 
                        extra_args.append('-mode='+self.__properties[self.__target]['mode'])
                        extra_args.append('-file='+_location_in_package)
                        command  = self.__build_arguments(server_info, extra_args)                            
                        self.log.info(f"Tiles Update Command: {command}")
                        result = self._execute(command)
                        self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC Tiles Update "})
                        if not self._parallel:
                            self.__console_msg(result, f"[{tc_package_id}] - AWC Tiles Update ") 
                    else:
                        self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. tilesUpdate Skipped")
                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC Tiles Update "})
        return self._processes
            
    
    

    def columnImport(self):  

        """
        Action: columnImport
        Command:  aws2_install_tilecollections -u= -g= -pf=  -mode= -file
        """                 
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        for index, server_info in enumerate(_execute_servers):

            self.log.info("Column Import")

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                                

                try:
                    if os.path.exists(_location_in_package):                        
                        for file in os.listdir(_location_in_package):
                            extra_args = []                          
                            if file.endswith('.xml'):     
                                extra_args.append('-file='+os.path.join(_location_in_package, file))                                
                                command  = self.__build_arguments(server_info, extra_args)                                
                                self.log.info(f"ColumnImport Command: {command}")                                
                                result = self._execute(command)
                                self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC ColumnImport "})
                                if not self._parallel:
                                    self.__console_msg(result, f"[{tc_package_id}] - AWC ColumnImport ")
                            else:
                                self.log.warning(f"Required File not Present from this location {tc_package_id}. ColumnImport Skipped")                                
                    else:
                        self.log.warning(f"Required Package Folder not Present from this location {tc_package_id}. ColumnImport Skipped")                                   
                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC ColumnImport "})
        return self._processes
                    
    def RelationBrowserDSImport(self): 

        """
        Action: RelationBrowserDSImport
        Command:  aws2_install_tilecollections -u= -g= -pf=  -mode= -file
        """          
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        for index, server_info in enumerate(_execute_servers):

            self.log.info("RelationBrowserDS Import")

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                

                try:
                    if os.path.exists(_location_in_package) and self.__properties[self.__target]['inputFile']:  
                        extra_args = []                          

                        extra_args.append('-type='+self.__properties[self.__target]['type'])
                        extra_args.append('-input='+os.path.join(_location_in_package, self.__properties[self.__target]['inputFile']))
                        extra_args.append('-filepath='+_location_in_package)
                        extra_args.append('-replace')

                        command = self.__build_arguments(server_info, extra_args)
                        self.log.info(f"RelationBrowserDSImport Command: {command}")
                        result = self._execute(command)
                        self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC RelationBrowserDSImport"})
                        if not self._parallel:
                            self.__console_msg(result, f"[{tc_package_id}] - AWC RelationBrowserDSImport")
                    else:
                        self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. RelationBrowserDSImport Skipped")
                        
                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC RelationBrowserDSImport"})
        return self._processes
                
                 
    def WorkspaceImport(self):
        
        """
        Action: WorkspaceImport
        Command: aws2_install_tilecollections -u= -g= -pf= file=
        """ 
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        for index, server_info in enumerate(_execute_servers):

            self.log.info(f'WorkspaceImport Started')

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                

                try: 
                    if os.path.exists(_location_in_package):
                        
                        for file in os.listdir(_location_in_package):
                            extra_args = []

                            if file.endswith('.xml'):                              
                                extra_args.append('-file='+os.path.join(_location_in_package, file))                                
                                command  = self.__build_arguments(server_info, extra_args)                                
                                self.log.info(f"WorkspaceImport Command: {command}")      
                                result = self._execute(command)
                                self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC WorkspaceImport"})
                                if not self._parallel:
                                    self.__console_msg(result, f"[{tc_package_id}] - AWC WorkspaceImport")                          
                            else:
                                self.log.warning(f"Required File not Present from this location {tc_package_id}. WorkspaceImport Skipped")
                    else:
                        self.log.warning(f"Required Package Folder not Present from this location {tc_package_id}. WorkspaceImport Skipped")

                except Exception as exp:                
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC WorkspaceImport"})
        return self._processes
        
    
        
    def __build_arguments(self, server_info, extra_args):
        
        __ssh_command = self.__environment_provider.get_ssh_command(server_info)
        
        if __ssh_command == '':
            args = []
        else:
            args = [__ssh_command]
            
        args.append(self.__properties[self.__target]['command'])
            
        # Get Infodba Credentials
        args.extend(self.__environment_provider.get_infodba_credentials(server_info))

        # Get Group Name
        args.extend(self.__environment_provider.get_group(server_info))

        if extra_args:
            args.extend(extra_args)
                  
        return ' '.join([str(elem) for elem in args])    
            
        
    def _executeTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__module_name).split(',')): 
                # Execute with multiple targets
                if not self.__sub_module_name:   
                    self.__target = targets   
                    dynamicExecutor = DynamicExecutor(self.__arguments)   
                    dynamicExecutor.set_module_instance(targets) # module instance name
                    dynamicExecutor.set_parallel(self._parallel)
                    # calling the targets one by one
                    if dynamicExecutor.get_sub_module_name():
                        _processesResult = dynamicExecutor.run_class()     
                    else:
                        _processesResult = dynamicExecutor.run_module()   
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult               
        except Exception as exp:
            self.log.error(exp)


    def _execute(self, command):
        """ 
        Used to process services/command
        """
        process = Process(command)
        process.set_parallel_execution(self._parallel)
        return process.execute()
    
    
    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Failed. Please check log file. Skipped Deployment")
        self.log.info('..............................................................')
