"""
GenerateClientMetaCache deployment activities
"""
import os

from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor


class GenerateClientMetaCache(Loggable):
    
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
        """
        Scope and target setup based on configuration
        """   
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
        
        
    def default(self):
                
        self.log.info("GenerateClientMetaCache Execute ")
        self._executeTargets()           
   
        
    def execute(self):           
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
         
        for index, server_info in enumerate(_execute_servers):
            """
            Action: GenerateClientMetaCache Exicute
            Command:  generate_client_meta_cache -u= -g= -pf= -t genertare all
            """
            command  =' '.join([str(elem) for elem in self.__build_arguments(server_info)])
            self.log.info(f"GenerateClientMetaCache Execution Started")
            self.log.info(f"GenerateClientMetaCache Command: {command}")
            #self.__console_msg(self._execute(command),  __class__.__name__)
            


    def __build_arguments(self, _server_info, ):
        
        __ssh_command = self.__environment_provider.get_ssh_command(_server_info)
        
        if __ssh_command == '':
            self.__remote_execution = False  
        else:
            self.__remote_execution = True
    
        if self.__remote_execution:
            args = [__ssh_command,
                    self.__properties[self.__target]['command'],
                    '-u='+ _server_info['TC_USER'],
                    '-g='+ _server_info['TC_GROUP'],
                    '-pf='+ _server_info['TC_PWF'],
                    '-t ',
                    'generate',
                    'all',
                    '-log='+ os.path.expandvars('$TC_TMP_DIR')

                ]       
        else:
            args = [self.__properties[self.__target]['command'],
                    '-u='+ _server_info['TC_USER'],
                    '-g='+ _server_info['TC_GROUP'],
                    '-pf='+ _server_info['TC_PWF'],
                    '-t ',
                    'generate',
                    'all',
                    '-log='+ os.path.expandvars('$TC_TMP_DIR')
                ]     
            
        return args        
        
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
                        getattr(GenerateClientMetaCache, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        dynamicExecutor.run_module()              
        except Exception as exp:
            self.log.error(exp)
        
           
    def _execute(self, command):

        """ Used to process services/command
        """
        process = Process(command)
        return process.execute()


    def __console_msg(self, result, action_msg):
        if result == 0:
            Loggable.log_success(self, f"{action_msg.capitalize()} Execution Successfully.")
        else:
            self.log.error(f"{action_msg.capitalize()} Execution Failed.")
        self.log.info('..............................................................')