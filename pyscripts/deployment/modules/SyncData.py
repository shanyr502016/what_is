from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.File import Directory
from corelib.File import File


from corelib.SCP import SCP
import os
import re

class SyncData(Loggable):
    
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
            
          
    def default(self):
                       
        self._executeTargets()
                                          
    def tc(self):
        """ 
        Action: Copy tcdataFiles
        Command:  scp -pr sourcelocation destinationlocation
        """ 
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 
        
        for index, server_info in enumerate(_execute_servers):
            
            try:

                if self.__environment_provider.get_property_validation('TC_DATA', server_info) and self.__environment_provider.get_property_validation('SYNCTCDATA_PATH', server_info):

                    tc_data = server_info['TC_DATA']
                    sync_tc_data = server_info['SYNCTCDATA_PATH']

                    _tcprofile_backup_dir = os.path.join(sync_tc_data, os.pardir, 'tcprofilevarsbackup')

                    if not os.path.exists(_tcprofile_backup_dir):
                        os.makedirs(_tcprofile_backup_dir)

                    if os.path.exists(tc_data) and os.path.exists(sync_tc_data):  

                        _scp = SCP(self.__environment_provider.get_ssh_command(server_info, True))

                        # backup the tc_profilevars.bat file from sync_tc_data share location
                        if os.path.exists(os.path.join(sync_tc_data, 'tc_profilevars.bat')):

                            _backuptc_profilevars = _scp.copy_to_local(os.path.join(sync_tc_data, 'tc_profilevars.bat'),_tcprofile_backup_dir)
                            self.__console_msg(_backuptc_profilevars, f'tc_profilevars.bat Backup')
                            self._processes.append({'NODE':server_info['NODE'],'process': _backuptc_profilevars ,'module': self.__module_label, 'package_id': '','label': f"SyncData TC"})

                        # backup the tc_profilevars file from sync_tc_data share location
                        if os.path.exists(os.path.join(sync_tc_data,'tc_profilevars')):

                            _backuptc_profilevars = _scp.copy_to_local(os.path.join(sync_tc_data,'tc_profilevars'),_tcprofile_backup_dir)
                            self.__console_msg(_backuptc_profilevars, f'tc_profilevars Backup')
                            self._processes.append({'NODE':server_info['NODE'],'process': _backuptc_profilevars ,'module': self.__module_label, 'package_id': '','label': f"SyncData TC"})
                        
                        
                        # rsync the tc_data
                        _copytcdataResult = _scp.rsnyc_to_local(tc_data + '/*', sync_tc_data + '/', self._parallel, [], self.__arguments._log_file)

                        self.__console_msg(_copytcdataResult, f'SyncTCData')
                        self._processes.append({'NODE':server_info['NODE'],'process': _copytcdataResult ,'module': self.__module_label, 'package_id': '','label': f"SyncData TC"})

                        if _copytcdataResult == 0:
                            # restore the tc_profilevars.bat
                            if os.path.exists(os.path.join(_tcprofile_backup_dir, 'tc_profilevars.bat')):
                                _restoredtc_profilevarsbat = _scp.copy_to_local(os.path.join(_tcprofile_backup_dir, 'tc_profilevars.bat'),os.path.join(sync_tc_data, 'tc_profilevars.bat'))
                                self.__console_msg(_restoredtc_profilevarsbat, f'tc_profilevars.bat Restored')
                                self._processes.append({'NODE':server_info['NODE'],'process': _restoredtc_profilevarsbat ,'module': self.__module_label, 'package_id': '','label': f"SyncData TC"})
                            if os.path.exists(os.path.join(_tcprofile_backup_dir,'tc_profilevars')):
                                _restoredtc_profilevars = 0
                                # For tc_profilevars not replaced as discussed with team, its using tc_data file
                                # _restoredtc_profilevars = _scp.copy_to_local(os.path.join(_tcprofile_backup_dir, 'tc_profilevars'),os.path.join(sync_tc_data,'tc_profilevars'))
                                # self._processes.append({'NODE':server_info['NODE'],'process': _restoredtc_profilevars ,'module': self.__module_label, 'package_id': '','label': f"SyncData TC"})
                                # self.__console_msg(_restoredtc_profilevars, f'tc_profilevars Restored')
                        self.__environment_provider.change_execmod(os.path.join(sync_tc_data)) 

            except Exception as exp:                
               self.log.error(f'{exp}')

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
                        getattr(SyncData, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        dynamicExecutor.run_module()              
        except Exception as exp:
            self.log.error(exp)
            
   
    def __console_msg(self, result, action_msg):
        
        if result == 0:
            Loggable.log_success(self, f"{action_msg.capitalize()} Copied Successfully!.")
        else:
            self.log.error(f"{action_msg.capitalize()} Copied Failed.")
        self.log.info('..............................................................')
                

    def _execute(self, command):
        """
         Used to process services/command
        """
        process = Process(command)
        return process.execute()
