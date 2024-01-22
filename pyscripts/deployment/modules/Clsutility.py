"""
Clsutility deployment activities
"""
import os
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants

class Clsutility(Loggable):
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
                
        self.log.info("Clsutility Import")
        return self._executeTargets()  

    def Import(self):

        """
        Action: Import
        Command:  Clsutility_import -u=username -pf=file -g=dba -import -hierarchy -cid=ICM -include_instances -output=%Temp%\Clsutility.log -show_all_errors
        """
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        for index, server_info in enumerate(_execute_servers):
            try:
                        
                #for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):
                self.log.info(f"{__class__.__name__}")                    
                command = self.__build_arguments(server_info)
                self.log.info(f"Clsutility Command: {command}")
                result = self._execute(command)
                self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': self._tcpackage_id,'label': f"[{self._tcpackage_id}] - ClsUtility"})
                if not self._parallel:
                    self.__console_msg(result, f"[{self._tcpackage_id}] - ClsUtility")            
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': self._tcpackage_id,'label': f"[{self._tcpackage_id}] - ClsUtility"})
        return self._processes


    def __build_arguments(self,_server_info):
        
        __ssh_command = self.__environment_provider.get_ssh_command(_server_info)

        if __ssh_command == '':  
            args = [] 
        else:
            args = [__ssh_command]

        if self.__environment_provider.get_property_validation('command', self.__properties[self.__target]):
            args.append(self.__properties[self.__target]['command']) 

        args.extend(self.__environment_provider.get_infodba_credentials(_server_info))

        args.extend(self.__environment_provider.get_group(_server_info))

        args.append('-import')
        args.append('-hierarchy')

        if self.__environment_provider.get_property_validation('cid', self.__properties[self.__target]):
            args.append('-cid='+ self.__properties[self.__target]['cid']) 

        args.append('-include_instances')

        if self.__environment_provider.get_property_validation('output_path', self.__properties[self.__target]):
            args.append('-output='+ self.__properties[self.__target]['output_path']) 

        args.append('-show_all_errors')
    
        return ' '.join([str(elem) for elem in args]) 
    
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
                        _processesResult = getattr(Clsutility, dynamicExecutor.get_sub_module_name())(self)   
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
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')
