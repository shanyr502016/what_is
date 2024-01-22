"""
Dispatcher deployment activities

"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Encryption import Encryption
from corelib.SCP import SCP
from corelib.File import Directory
from corelib.Constants import Constants
import glob
import os
from deployment.lib.DitaReplacements import DitaReplacements


class Dispatcher(Loggable):
    
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
        Get the Security Values
        """
        self.__security = args._security
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

        self.__action = None
        
        """
        Scope and target setup based on configuration
        """ 
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
        """
        Remote Execution.
        """
        self.__remote_execution = False        
        """
        Target Environment Type if linux
        """
        self.__is_linux = False
        
        """
        Target Environment Type if windows
        """        
        self.__is_windows = False

        self._ditaReplacements = DitaReplacements(self.__environment_provider)

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel 

        self.__share_do_not_modify_dir = os.path.join(self.__environment_provider.get_share_root_path(), 'dita_share_do_not_modify')

        self._directory = Directory()

    def default(self):        
        return self._executeTargets() 
    

    def Client(self):
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 
        
        for index, server_info in enumerate(_execute_servers):
            self.log.info(f"Dispatcher Deploy")  

            service_stop_result = self.servicestop('DISPATCHER_ALL')

            if service_stop_result == 0:

                for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                    try:

                        _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                        _replacement_foldername = 'deploy_'+self.__environment_provider.get_environment_name().lower()

                        _replacement_path = self.__environment_provider.get_location_in_package(tc_package_id, _replacement_foldername)

                        _excludes_replacements = self.__properties[self.__target]['excludes_replacements']

                        _replacement_status = self._ditaReplacements._getDitaProperties(tc_package_id, server_info, self.__properties[self.__target]['location_in_package'], _excludes_replacements, self._parallel)

                        if _replacement_status == 0:

                            if os.path.exists(os.path.join(_replacement_path, self.__properties[self.__target]['location_in_package'])):


                                _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))
                                _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

                                dispatcher_path = server_info['DISPATCHER_PATH']

                                # DispatcherClient
                                _dispatcher_client_path = os.path.join(dispatcher_path, 'DispatcherClient')
                                _check_dispatcher_client = _scp_with_ssh.check_dir_to_remote(self.__environment_provider.is_windows(server_info['OS_TYPE']), _dispatcher_client_path)
                                if _check_dispatcher_client:
                                    _copyDispatcherClientResult = 0
                                    _copyDispatcherClientResult =  _scp_without_ssh.copy_to_remote(os.path.join(_replacement_path,self.__properties[self.__target]['location_in_package'],'DispatcherClient','*'), _dispatcher_client_path, self._parallel)
                                    self._processes.append({'NODE':server_info['NODE'],'process': _copyDispatcherClientResult,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - DispatcherClient"})
                                    if not self._parallel:
                                        self.__console_msg(_copyDispatcherClientResult, f'[{tc_package_id}] - DispatcherClient')
                                else:
                                    self.log.info('DispatcherClient Folder does not exists')
                                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - DispatcherClient"})
                            
                            else:
                                self.log.warning(f'Replacement Environment is not avaliable in {tc_package_id}')
                                self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - DispatcherClient"})

                        else:
                            self.log.warning(f'Replacement not updated {tc_package_id}')
                            self._processes.append({'NODE':server_info['NODE'],'process': _replacement_status,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - DispatcherClient"})

                    except Exception as exp:                
                        self.log.error(f'{exp}')
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - DispatcherClient"})

            else:
                self.log.warning(f'DISPATCHER_CLIENT - Service Stop Failed - Execution Skipped...')
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '', 'label': f"[''] - DispatcherClient"})


        return self._processes

    def Module(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 
        
        for index, server_info in enumerate(_execute_servers):

            self.log.info(f"Dispatcher Deploys")

            service_stop_result = self.servicestop('DISPATCHER_ALL')

            if service_stop_result == 0:
            
                for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                    try:

                        _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                        _replacement_foldername = 'deploy_'+self.__environment_provider.get_environment_name().lower()

                        _replacement_path = self.__environment_provider.get_location_in_package(tc_package_id, _replacement_foldername)

                        _excludes_replacements = self.__properties[self.__target]['excludes_replacements']

                        _replacement_status = self._ditaReplacements._getDitaProperties(tc_package_id, server_info, self.__properties[self.__target]['location_in_package'], _excludes_replacements, self._parallel)

                        if _replacement_status == 0:

                            if os.path.exists(os.path.join(_replacement_path, self.__properties[self.__target]['location_in_package'])):

                                _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))
                                _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

                                dispatcher_path = server_info['DISPATCHER_PATH']

                                # Module
                                _dispatcher_module_path = os.path.join(dispatcher_path, 'Module')
                                _check_dispatcher_module = _scp_with_ssh.check_dir_to_remote(self.__environment_provider.is_windows(server_info['OS_TYPE']), _dispatcher_module_path)
                                if _check_dispatcher_module:
                                    _copyDispatcherModuleResult =  _scp_without_ssh.copy_to_remote(os.path.join(_replacement_path,self.__properties[self.__target]['location_in_package'],'Module','*'), _dispatcher_module_path, self._parallel)
                                    self._processes.append({'NODE':server_info['NODE'],'process': _copyDispatcherModuleResult,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Dispatcher Module"})
                                    if not self._parallel:
                                        self.__console_msg(_copyDispatcherModuleResult, f'[{tc_package_id}] - Dispatcher Module')
                                else:
                                    self.log.warning(f'Module Folder does not exists from [{server_info["HOSTNAME"]}]')  
                                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Dispatcher Module"})                      
                            else:
                                self.log.warning(f'Replacement Environment is not avaliable in {tc_package_id}')
                                self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Dispatcher Module"})

                        else:
                            self.log.warning(f'Replacement not updated {tc_package_id}')
                            self._processes.append({'NODE':server_info['NODE'],'process': _replacement_status,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - DispatcherClient"})

                    except Exception as exp:                
                        self.log.error(f'{exp}')
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Dispatcher Module"})

            else:
                self.log.warning(f'DISPATCHER_MODULE - Service Stop Failed - Execution Skipped...')
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '', 'label': f"[''] - DispatcherClient"})

        
        return self._processes


    def servicestop(self, service_name):
        dynamicExecutor = DynamicExecutor(self.__arguments)
        self.log.info(f"Requesting to Stop the {service_name} Service")
        for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Stop', service_name):
            if not serviceData['pid']:
                self.log.info(f"{serviceData['module']} - Stopped")
            else:
                self.log.error(f"{serviceData['module']} not Stopped. Please Check the {service_name} Service")
                return 1
        return 0
    

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
                        _processesResult = getattr(Dispatcher, dynamicExecutor.get_sub_module_name())(self)   
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
            self.log.info(Constants.colorize(f"{action_msg} Copied Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Copied Failed.")
        self.log.info('..............................................................')