import os

from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants
from deployment.lib.DitaReplacements import DitaReplacements


class CopyTcData(Loggable):
    
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

        self._ditaReplacements = DitaReplacements(self.__environment_provider) 
        
        """
        Scope and target setup based on configuration
        """ 
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
            self.log.info(self.__target)
        
        
    def default(self):
                
        self.log.info("CopyTcData All File")        
        return self._executeTargets()           


    def copyfiles(self):
        """ 
        Action: Copy TcData Server Files
        Command:  scp -pr sourcelocation destinationlocation
        """  
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])        

        self.log.info(f"{__class__.__name__}")

        for index, server_info in enumerate(_execute_servers):
            

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):
                try:
                    if 'TC_DATA' in server_info:
                        _targetpath = server_info['TC_DATA']
                        _replacement_foldername = 'deploy_'+self.__environment_provider.get_environment_name().lower()
                        _replacement_path = self.__environment_provider.get_location_in_package(tc_package_id, _replacement_foldername)
                        _excludes_replacements = self.__properties[self.__target]['excludes_replacements']

                        _replacement_status = self._ditaReplacements._getDitaProperties(tc_package_id, server_info, self.__properties[self.__target]['location_in_package'],_excludes_replacements, self._parallel)

                        if _replacement_status == 0:
                        
                            _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, os.path.join(_replacement_path,self.__properties[self.__target]['location_in_package']))

                            if os.path.exists(os.path.join(_replacement_path,self.__properties[self.__target]['location_in_package'])): # check package path

                                command = self.__build_arguments(server_info, _location_in_package, _targetpath)  
                                result = self._execute(command, _targetpath)
                                self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - CopyTcData to {server_info['HOSTNAME']}"})
                                if not self._parallel:
                                    self.__console_msg(result, f"[{tc_package_id}] - CopyTcData to {server_info['HOSTNAME']}")
                            else:
                                self.log.warning(f"Required File or Folder not Present from this location {tc_package_id} {__class__.__name__} Skipped")
                                self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - CopyTcData to {server_info['HOSTNAME']}"})
                        else:
                            self.log.warning(f'Replacement not updated {tc_package_id}')
                    else:
                        self.log.error(f'TC_DATA is not configured. Skipped CopyTCData') 
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - CopyTcData to {server_info['HOSTNAME']}"}) 
                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - CopyTcData to {server_info['HOSTNAME']}"})
            
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
                        _processesResult = getattr(CopyTcData, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()   
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult               
        except Exception as exp:
            self.log.error(exp)


    def __build_arguments(self, _server_info, _location_in_package, _targetpath):
        
        """
        Return command with source and destination path

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
    
    def _execute(self, command, path):
        
        """ Used to process services/command
        """
        process = Process(command, path)
        process.set_parallel_execution(self._parallel)
        return process.execute()  
     
   
    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Copied Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Copied Failed.")
        self.log.info('..............................................................')

            