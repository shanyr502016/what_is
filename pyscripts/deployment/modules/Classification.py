"""
Classification deployment activities
"""
import os
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants
from deployment.lib.UtilityExecutionSet import UtilityExecutionSet

class Classification(Loggable):
    
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
                
        self.log.info("Classification Import All")
        return self._executeTargets()           
   
        
    def Import(self):

        """
        Action: Import
        Command:  Classification_import -u= -g= -pf= import_mode= -transfermode= -xml_file=
        """
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        for index, server_info in enumerate(_execute_servers):
            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):
                try:
                    __commands = []
                    _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                    self.log.info(f"{__class__.__name__}")
                    if os.path.exists(_location_in_package):
                        for file in os.listdir(_location_in_package):
                            if file.endswith('.plmxml'):
                                command = self.__build_arguments(server_info, os.path.join(_location_in_package,file))
                                self.log.info(f"Classification Command: {command}")
                                __commands.append(command)
                            else:
                                self.log.warning(f"Required File not Present from this location {tc_package_id}. {__class__.__name__} Import Skipped")
                        if __commands:
                            utilityExecution = UtilityExecutionSet(self.__environment_provider, __commands, 'Classification_' + tc_package_id, self._parallel)
                            result = utilityExecution.execute()
                            self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Classification Import"})            
                            if not self._parallel:
                                self.__console_msg(result, f"[{tc_package_id}] - Classification Import")
                        else:
                            self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. {__class__.__name__} Import Skipped")
                    else:
                        self.log.warning(f"Required Package Folder not Present from this location {tc_package_id}. {__class__.__name__} Import Skipped")
                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1, 'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Classification Import"})            
        return self._processes



    def __build_arguments(self, server_info, file):
        
        __ssh_command = self.__environment_provider.get_ssh_command(server_info)
    
        if __ssh_command == '':  
            args = []
        else:
            args = [__ssh_command]
            
        if self.__environment_provider.get_property_validation('command', self.__properties[self.__target]):
            args.append(self.__properties[self.__target]['command'])

        # Get Infodba Credentials
        args.extend(self.__environment_provider.get_infodba_credentials(server_info))

        # Get Group Name
        args.extend(self.__environment_provider.get_group(server_info))    

        if self.__environment_provider.get_property_validation('import_mode', self.__properties[self.__target]):
            args.append('-import_mode='+ self.__properties[self.__target]['import_mode'])
        if self.__environment_provider.get_property_validation('import_mode', self.__properties[self.__target]):
            args.append('-transfermode='+ self.__properties[self.__target]['transfermode'])

        args.append('-xml_file='+ file)

            
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
                        _processesResult = getattr(Classification, dynamicExecutor.get_sub_module_name())(self)   
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
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')