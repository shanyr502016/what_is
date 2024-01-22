"""
clearlocks deployment activities
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants


class Clearlocks(Loggable):
    
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

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel

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
                
        self.log.info("clearlocks Execute ")
        return self._executeTargets()    

    def truncatepomtimestamp(self):

        try:

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])  

            for index, server_info in enumerate(_execute_servers):

                __ssh_command = self.__environment_provider.get_ssh_command(server_info)

                _LD_LIBRARY_PATH = server_info['LD_LIBRARY_PATH']
                _BASHRC = server_info['BASHRC']
                _ORACLE_HOME = server_info['ORACLE_HOME']
                _DB_USERNAME = server_info['DB_USERNAME']
                _DB_PASSWORD = server_info['DB_PASSWORD']
                _DB_SSID = server_info['DB_SSID']
                _DB_DIRECTORY = server_info['DB_DIRECTORY']

                _SCHEMAS = server_info['SCHEMAS']

                args_expdp = []

                if __ssh_command == '':
                    args_expdp = []
                else:
                    args_expdp = [__ssh_command]
                args_expdp.append('export LD_LIBRARY_PATH='+ _LD_LIBRARY_PATH+':$LD_LIBRARY_PATH') 
                args_expdp.append('&&') 
                args_expdp.append('export PATH=$LD_LIBRARY_PATH:$PATH') 
                args_expdp.append('&&')  
                args_expdp.append(_BASHRC)  
                args_expdp.append('&&')  
                args_expdp.append('export ORACLE_HOME='+ _ORACLE_HOME + '/') 
                args_expdp.append('&&')         
                args_expdp.append('cd '+_ORACLE_HOME+'/bin &&') 
                args_expdp.append('TRUNCATE TABLE infodba.POMTIMESTAMP;')

                args_expdp = ' '.join([str(elem) for elem in args_expdp])

                if self._parallel:
                    self.log.info("Please wait while taking 10 to 15 minutes...")
                    result = self._execute(args_expdp, _ORACLE_HOME+'/bin', False)
                    self._processes.append(result)
                else:
                    self.log.info("Please wait while taking 10 to 15 minutes...")
                    result = self._execute(args_expdp, _ORACLE_HOME+'/bin', False)
                    self.__console_msg(result, 'Backup infodba')
            return self._processes
        except Exception as exp:
            self.log.error(exp)
        

           
   
        
    def verbose(self):           
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
         
        for index, server_info in enumerate(_execute_servers):
            """
            Action: verbose Execute
            Command:  clearlocks -verbose 
            """        
            try:    
                args=[]
                args.append('-verbose')
                    
                command = self.__build_arguments(server_info,args)
                
                self.log.info("Execution Started....")
                
                self.log.info(f"Execution Command: {command}")
                result = self._execute(command)
                self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': '', 'label': f"Clearlocks Verbose"})
                if not self._parallel:
                    self.__console_msg(result, f"Clearlocks Verbose")
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1, 'module': self.__module_label, 'package_id': '', 'label': f"Clearlocks Verbose"})
        return self._processes
                    
                
                         
                
    def assertAllDead(self):           
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
         
        for index, server_info in enumerate(_execute_servers):
            """
            Action: asserAllDead Execute
            Command:  clearlocks -assert_all_dead -u= -g= -pf= 
            """
            try:
                args= []       
                args.append('-assert_all_dead')            
                args.append('-u='+ server_info['TC_USER'])
                args.append('-pf='+ server_info['TC_PWF'])  
                args.append('-g='+ server_info['TC_GROUP'])
                
                self.log.info(f"{self.__target}")
                    
                command = self.__build_arguments(server_info, args)            
                self.log.info(f"Execution Command: {command}")
                result = self._execute(command)
                self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': '', 'label': f"Clearlocks AssertallDead"})
                if not self._parallel:
                    self.__console_msg(result, f"Clearlocks AssertallDead")
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1, 'module': self.__module_label, 'package_id': '', 'label': f"Clearlocks AssertallDead"})
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
                        _processesResult = getattr(Clearlocks, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()  
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult            
        except Exception as exp:
            self.log.error(exp)
        
           
    def _execute(self, command, path='',stderr = True):

        """ Used to process services/command
        """
        process = Process(command)
        process.set_parallel_execution(self._parallel)
        process.set_stderr(stderr)
        return process.execute()


    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Execution Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg.capitalize()} Execution Failed.")
        self.log.info('..............................................................')