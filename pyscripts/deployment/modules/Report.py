"""
Report deployment activities
"""
import os

from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants


class Report(Loggable):
    
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
        self._parallel = self.__arguments.parallel    
        """
        Scope and target setup based on configuration
        """   
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel
        
    def default(self):
                
        self.log.info("Report Import All")
        return self._executeTargets()             
   
        
    def Import(self):

        """
        Action: Import
        Command:  Report_import -import -stageDir= -u= -g= -pf=  -reportId=
        """
         
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
         
        for index, server_info in enumerate(_execute_servers):            
            
            self.log.info(f"Report Import")

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
            
                try:
                    if os.path.exists(_location_in_package):
                        
                        for reportId in os.listdir(_location_in_package):
                            
                            if os.path.isdir(os.path.join(_location_in_package,reportId)):

                                self.log.info(f"Report Import Started..")
                                
                                command  = self.__build_arguments(server_info, _location_in_package, reportId)
                                                    
                                self.log.info(f"Report Import Command: {command}")
                                result = self._execute(command)
                                self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - {__class__.__name__}"})
                                if not self._parallel:
                                    self.__console_msg(result, f"[{tc_package_id}] - {__class__.__name__}")
                            else:
                                self.log.warning(f"Required Package Folder not Present from this location {tc_package_id}. Report Import Skipped")       
                                                
                    else:
                        self.log.error(f"Required Package Folder not Present from this location {tc_package_id}. Report Import Skipped")
                        
                except Exception as exp:                    
                    self.log.error(f'{exp}')
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - {__class__.__name__}"})
        return self._processes
               
               
               
    def __build_arguments(self, server_info, _location_in_package,reportId):
        
        __ssh_command = self.__environment_provider.get_ssh_command(server_info)
    
        if __ssh_command == '':  
            args = []
        else:
            args = [__ssh_command]
            
        if self.__environment_provider.get_property_validation('command', self.__properties[self.__target]):
            args.append(self.__properties[self.__target]['command'])
             
        args.append('-import')
        args.append('-overwrite')
            
        args.append('-stageDir='+_location_in_package)
        args.append('-reportId='+reportId)

            
        # Get Infodba Credentials
        args.extend(self.__environment_provider.get_infodba_credentials(server_info))

        # Get Group Name
        args.extend(self.__environment_provider.get_group(server_info))
        
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
                        _processesResult = getattr(Report, dynamicExecutor.get_sub_module_name())(self)   
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
            self.log.info(Constants.colorize(f"{action_msg} Imported Successfully.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Import Failed.")

        self.log.info('..............................................................')
