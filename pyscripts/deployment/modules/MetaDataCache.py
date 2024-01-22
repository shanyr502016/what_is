"""
MetaDataCache deployment activities
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants


class MetaDataCache(Loggable):
    
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
        self._parallel = False
        """
        Scope and target setup based on configuration
        """   
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
        
        
    def default(self):
                
        self.log.info("MetaDataCache Execute ")
        return self._executeTargets()           
   
    def generateMetaDataCacheDelete(self):           
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
         
        for index, server_info in enumerate(_execute_servers):
            """
            Action: GenerateClientMetaCache Exicute
            Command:  generate_client_meta_cache -u= -g= -pf= -t genertare all
            """
            try:
                args= []
                    
                args.append('-delete')
                
                self.log.info(f"{self.__target}")
                    
                command = self.__build_arguments(server_info,args)
                
                self.log.info(f"Execution Command: {command}")
                result = self._execute(command)
                self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': '', 'label': "Delete All ClientMetaCache"})
                if not self._parallel:
                    self.__console_msg(result, 'Delete MetaCache')
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1, 'module': self.__module_label, 'package_id': '', 'label': "Delete All ClientMetaCache"})

        return self._processes
                   
    def clientMetaCacheDelete(self):           
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
         
        for index, server_info in enumerate(_execute_servers):
            """
            Action: GenerateClientMetaCache Exicute
            Command:  generate_client_meta_cache -u= -g= -pf= -t genertare all
            """
            try:
                args=[]
                args.append('-t')
                args.append('delete')
                args.append('all')
                
                
                self.log.info(f"{self.__target}")
                    
                command = self.__build_arguments(server_info,args)
                
                self.log.info("Execution Started....")
                
                self.log.info(f"Execution Command: {command}")
                result = self._execute(command)
                self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': '', 'label': "Delete All ClientMetaCache"})
                if not self._parallel:
                    self.__console_msg(result, 'Delete All ClientMetaCache')
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1, 'module': self.__module_label, 'package_id': '', 'label': "Delete All ClientMetaCache"})

        return self._processes                   
                         
                
    def clientMetaCacheGenerate(self):           
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
         
        for index, server_info in enumerate(_execute_servers):
            """
            Action: GenerateClientMetaCache Execute
            Command:  generate_client_meta_cache -u= -g= -pf= -t genertare all
            """
            try:
                args= []
                
                args.append('-t')
                args.append('generate')
                args.append('all')
                
                self.log.info(f"{self.__target}")
                    
                command = self.__build_arguments(server_info,args)
                
                self.log.info(f"Execution Command: {command}")
                result = self._execute(command)
                self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': '', 'label': "Generate Client MetaCache"})
                if not self._parallel:
                    self.__console_msg(result, 'Generate Client MetaCache') 
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1, 'module': self.__module_label, 'package_id': '', 'label': "Generate Client MetaCache"})

        return self._processes            
            

            
    def generateMetaDataCache(self):           
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
         
        for index, server_info in enumerate(_execute_servers):
            """
            Action: GenerateClientMetaCache Exicute
            Command:  generate_client_meta_cache -u= -g= -pf= -t genertare all
            """
            try:
                args= []
            
                args.append('-force')
                    
                self.log.info(f"{self.__target}")
                    
                command = self.__build_arguments(server_info,args)
                
                self.log.info(f"Execution Command: {command}")
                result = self._execute(command)
                self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': '', 'label': "Force Generate MetaCache"})
                if not self._parallel:
                    self.__console_msg(result, 'Force Generate MetaCache')
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1, 'module': self.__module_label, 'package_id': '', 'label': "Force Generate MetaCache"})
        return self._processes    
            
            


    def __build_arguments(self, _server_info, args):
        
        args_list = []
        
        __ssh_command = self.__environment_provider.get_ssh_command(_server_info)
        
        if __ssh_command == '':
            self.__remote_execution = False  
        else:
            self.__remote_execution = True
            
        if self.__remote_execution:
            args_list.append(__ssh_command)
            args_list.append(self.__properties[self.__target]['command'])
        else:
            args_list.append(self.__properties[self.__target]['command'])
            
        args_list.extend(args)
        
        args_list.append('-u='+ _server_info['TC_USER'])
        args_list.append('-pf='+ _server_info['TC_PWF'])  
        args_list.append('-g='+ _server_info['TC_GROUP'])
        #args_list.append('-log='+ os.path.expandvars('$TC_TMP_DIR'))
        
        return ' '.join([str(elem) for elem in args_list])
        
              
        
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
                        _processesResult = getattr(MetaDataCache, dynamicExecutor.get_sub_module_name())(self)   
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
        return process.execute()


    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Execution Successfully.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg.capitalize()} Execution Failed.")
        self.log.info('..............................................................')

