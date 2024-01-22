""" AWCIndexing deployment activities
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants


class AWSolrIndexing(Loggable):

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
        self._processesResult = []
        self._processes = []
        self._parallel = self.__arguments.parallel
        
        """
        Scope and target setup based on configuration
        """ 
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
        
        
    def default(self): 
        self.log.info(__class__.__name__+' '+'Import All')
        return self._executeTargets()
        
    modules_list_to_stop_start_services = ['SOLR','INDEXINGTASK']


    def execute(self):

        """Command : awindexerutil -u=infodba -pf=infodba_app_pass.pwf -g=dba -delta"""
        
        self.log.info(f"AWSolrIndexing Execute")

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        result = 1
        for index, server_info in enumerate(_execute_servers): 
            self.log.info("Requesting to Stop the Services")
            self.__console_msg(self.service_start_stop('Stop'),'Solr and IndexingTask Stopped')

            command = self.__build_arguments(server_info)

            self.log.info(f"Execution Command: {command}")
            result = self._execute(command)
            self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': '', 'label': "AWSolrIndexing Utility"})
            if not self._parallel:
                self.__console_msg(result, "AWSolrIndexing")
            
            if result==0:
                self.log.info(f"Requesting to Start the Services")
                self.__console_msg(self.service_start_stop('Start'),'Solr and IndexingTask Started')
            else:
                self.log.error(f"{self.__target} Failed to execute. Please check utiity configuration file.")
        return self._processes
            

    def service_start_stop(self, action):
        result = 1
        dynamicExecutor = DynamicExecutor(self.__arguments)
        for module in self.modules_list_to_stop_start_services:
            for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, action , module):
                if not serviceData['pid']:
                    self.log.info(f"{serviceData['module']} - {action} Successfully")
                    result = 0
                else: 
                    self.log.error(f"{serviceData['module']} not Started. Please Check the {module} Service")
                    exit()
        return result


    def __build_arguments(self, server_info):
            
        __ssh_command = self.__environment_provider.get_ssh_command(server_info)
        
        if __ssh_command == '':
            self.__remote_execution = False  
        else:
            self.__remote_execution = True

        if self.__remote_execution:
            args = [__ssh_command]
            args.append('yes |')
            
        else:
            args = []
            args.append('yes |')
        if self.__environment_provider.get_property_validation('command', self.__properties[self.__target]):
            args.append(self.__properties[self.__target]['command'])
            
        # Get Infodba Credentials
        args.extend(self.__environment_provider.get_infodba_credentials(server_info))

        # Get Group Name
        args.extend(self.__environment_provider.get_group(server_info))
          
        args.append('-delta')

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
                        _processesResult = getattr(AWSolrIndexing, dynamicExecutor.get_sub_module_name())(self)
                    else:
                        _processesResult = dynamicExecutor.run_module()
                        
                    self._processesResult = self._processesResult + _processesResult 
            return self._processesResult              
        except (Exception) as excep:
            self.log.error(excep)
            
    def _execute(self, command):

        """ Used to process services/command
        """
        process = Process(command)
        process.set_parallel_execution(self._parallel)
        return process.execute()


    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg.capitalize()} Execution Failed.")
        self.log.info('..............................................................')
