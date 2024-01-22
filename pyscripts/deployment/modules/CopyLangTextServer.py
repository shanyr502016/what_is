from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
import os
from corelib.Constants import Constants

class CopyLangTextServer(Loggable):
    
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
                
        self.log.info("CopyLangTextServer All File")        
        self._executeTargets()           


    def all(self):
        """ 
        Action: Copy LANGText Server Files
        Command:  scp -pr sourcelocation destinationlocation
        """  
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
                
        for index, server_info in enumerate(_execute_servers):

            self.log.info(f"{__class__.__name__}")

            _targetpath = os.path.join(server_info['TC_ROOT'], self.__properties[self.__target]['targetpath'])

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                if os.path.exists(_location_in_package): # check package
                    
                    command = self.__build_arguments(server_info, _location_in_package, _targetpath)
                    result = self._execute(command, _targetpath)
                    self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': tc_package_id, 'label': f'[{tc_package_id}] - {__class__.__name__}'})
                    if not self._parallel:
                        self.__console_msg(result, f'[{server_info["HOSTNAME"]}] - [{tc_package_id}] - {__class__.__name__}')
                else:
                    self.log.warning(f"Required File not Present from this location. {__class__.__name__} {tc_package_id} Skipped")
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
                        _processesResult = getattr(CopyLangTextServer, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()  
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult               
        except Exception as exp:
            self.log.error(exp)


    def __build_arguments(self, _server_info, _location_in_package, _targetpath):
        
        """
        Return command with source and destination path
        
        :param _server_info: Server Info 
        :param _location_in_package: Source Path
        :param _targetpath: Destination Path
        :return: Build command: Command
        """ 
        # ssh command
        __ssh_command = self.__environment_provider.get_ssh_command(_server_info,True)
        
        args = ['scp']
        
        args.append('-pr')
        args.append(_location_in_package + '/*')
        
        if __ssh_command == '':
            self.__remote_execution = False 
            args.append(_targetpath)  
        else:
            self.__remote_execution = True
            args.append(__ssh_command + ':' + _targetpath)           
         
        return ' '.join([str(elem) for elem in args]) 
    
    
    
    
   
    def __console_msg(self, result, action_msg):
        
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Copied Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Copied Failed.")
        self.log.info('..............................................................')

              
            
    def _execute(self, command, path):
        
        """ Used to process services/command
        """
        process = Process(command, path)
        process.set_parallel_execution(self._parallel)
        return process.execute()  
