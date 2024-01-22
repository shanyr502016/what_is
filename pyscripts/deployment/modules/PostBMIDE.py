
"""
PostBMIDE deployment activities
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants

class PostBMIDE(Loggable):
    
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
            # self.__scope = self.__sub_module_name[1:][0]
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)

        self._processesResult = []
        self._parallel = self.__arguments.parallel

        """
        Resume State Skip
        """
        self._resumestate = args._arguments.resumestate

        """
        Get the Delta targets
        """
        self._delta = None
        if args._arguments.delta:
            self._delta = self.__environment_provider.read_delta_targets(args._arguments.delta)

    def default(self):
        self.log.info("PostBMIDE")
        if self.__environment_provider.get_property_validation('parallel', self.__properties[self.__module_name]):
            self._parallel = self.__environment_provider.get_parallel_status(self.__module_name)  
        if self._delta :
            self.__properties[self.__module_name]['executeTargets'] = self._delta
            self._resumestate = True
        self.servicestart('FSC')        
        return self._executeTargets()
    
    def servicestart(self, servicename):
        dynamicExecutor = DynamicExecutor(self.__arguments)
        self.log.info('Requesting to start the FSC Service')
        for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Start', servicename):
            if serviceData['pid']:
                self.log.info(f"{serviceData['module']} - Started")
            else:
                self.log.error(f"{serviceData['module']} not Started. Please Check the FSC Service")
                exit()

    def conf(self):
        self.log.info("PostBMIDE Conf")
        self.servicestart('FSC')
        return self._executeCombineTargets()
    
    def Online(self):
        self.log.info("PostBMIDE Online")
        self.servicestart('FSC')
        return self._executeCombineTargets()

    def _executeCombineTargets(self):
        try:
            # Resume State Execution Read File
            _targetList = self.__environment_provider.resume_state_execution_read(self._tcpackage_id,self.__module_name,self._resumestate)       
            for threadcount, targets in enumerate(_targetList):  

                server_info = self.__environment_provider.update_serverinfo_data(_targetList[targets],self.__arguments)
                if 'executionServer' in self.__arguments._properties[targets]:
                    self.__arguments._environment[self.__arguments._properties[targets]['executionServer']] = server_info

                dynamicExecutor = DynamicExecutor(self.__arguments)
                self.__target = targets
                dynamicExecutor.set_module_instance(targets) # module instance name
                dynamicExecutor.set_parallel(self._parallel) 
                dynamicExecutor.set_environment(self.__arguments._environment)
                self.__scope = dynamicExecutor.get_action()                    
                if dynamicExecutor.get_sub_module_name():
                    _processesResult = dynamicExecutor.run_class()                        
                else:
                    _processesResult = dynamicExecutor.run_module()
                self._processesResult = self._processesResult + _processesResult
                dynamicExecutor.set_process_results(self._processesResult)
                # Resume State Calculation     
                self.__environment_provider.resume_state_execution_write(self._tcpackage_id,self.__module_name,targets,_processesResult,self._parallel) # Resume State Execution Write File
            if self._parallel:
                _parallelResult = []
                for process in self._processesResult:
                    if len(Loggable.log_subprocess_output(self, process['process'].stdout)) > 0:
                        self.log.error('Error Found')
                        self.__console_msg(1, process['label'])
                        _parallelResult.append({'process': 1 ,'module': process['module'],  'label': process['label']})
                    else:
                        self.__console_msg(process['process'].wait(), process['label'])
                        _parallelResult.append({'process': process['process'].wait() ,'module': process['module'],  'label': process['label']})
                self._processesResult = _parallelResult
            return self._processesResult
        except Exception as exp:
            self.log.error(exp)

    
    def _executeTargets(self):
        
        try:       
            # Resume State Execution Read File
            _targetList = self.__environment_provider.resume_state_execution_read(self._tcpackage_id,self.__module_name,self._resumestate)       
            for threadcount, targets in enumerate(_targetList):

                server_info = self.__environment_provider.update_serverinfo_data(_targetList[targets],self.__arguments)
                if 'executionServer' in self.__arguments._properties[targets]:
                    self.__arguments._environment[self.__arguments._properties[targets]['executionServer']] = server_info
                                                                                                 
                if not self.__sub_module_name:               
                    dynamicExecutor = DynamicExecutor(self.__arguments)
                    self.__target = targets
                    dynamicExecutor.set_module_instance(targets) # module instance name
                    dynamicExecutor.set_parallel(self._parallel) 
                    dynamicExecutor.set_environment(self.__arguments._environment)
                    self.__scope = dynamicExecutor.get_action()                    
                    if dynamicExecutor.get_sub_module_name():
                        _processesResult = dynamicExecutor.run_class()                        
                    else:
                        _processesResult = dynamicExecutor.run_module()
                    self._processesResult = self._processesResult + _processesResult
                    dynamicExecutor.set_process_results(self._processesResult)
                    # Resume State Calculation     
                    self.__environment_provider.resume_state_execution_write(self._tcpackage_id,self.__module_name,targets,_processesResult,self._parallel) # Resume State Execution Write File
            if self._parallel:
                _parallelResult = []
                for process in self._processesResult:
                    if len(Loggable.log_subprocess_output(self, process['process'].stdout)) > 0:
                        self.log.error('Error Found')
                        self.__console_msg(1, process['label'])
                        _parallelResult.append({'process': 1 ,'module': process['module'],  'label': process['label']})
                    else:
                        self.__console_msg(process['process'].wait(), process['label'])
                        _parallelResult.append({'process': process['process'].wait() ,'module': process['module'],  'label': process['label']})
                self._processesResult = _parallelResult
            return self._processesResult
        except Exception as exp:
            self.log.error(exp)


    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg}  Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')