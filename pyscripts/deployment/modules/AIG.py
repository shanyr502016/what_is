import os
import shutil
import re

from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.SCP import SCP
from corelib.File import Directory
from corelib.Constants import Constants
from deployment.lib.DitaReplacements import DitaReplacements

class AIG(Loggable):
    
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

        self._ditaReplacements = DitaReplacements(self.__environment_provider)

        self._directory = Directory()

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel
        
        """
        Scope and target setup based on configuration
        """ 
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
        
        
    def default(self):
                
        self.log.info("T4S Deploy")        
        return self._executeTargets() 
    

    def deploy(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 
        
        for index, server_info in enumerate(_execute_servers):
            
            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):
                try:

                    _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                    _replacement_foldername = 'deploy_'+self.__environment_provider.get_environment_name().lower()

                    _replacement_path = self.__environment_provider.get_location_in_package(tc_package_id, _replacement_foldername)

                    _excludes_replacements = self.__properties[self.__target]['excludes_replacements']

                    _replacement_status = self._ditaReplacements._getDitaProperties(tc_package_id, server_info, self.__properties[self.__target]['location_in_package'], _excludes_replacements, self._parallel)

                    if _replacement_status == 0:

                        if os.path.exists(os.path.join(_replacement_path,self.__properties[self.__target]['location_in_package'])):
                            _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))
                            _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

                            aig_path = server_info['GS_ROOT']
                            #bgs_path = server_info['BGS_ROOT']

                            aig_source_path = os.path.join(_replacement_path,self.__properties[self.__target]['location_in_package'], "t4s_custom_APPS")

                            _check_aig_path = _scp_with_ssh.check_dir_to_remote(self.__environment_provider.is_windows(server_info['OS_TYPE']), aig_path)

                            if _check_aig_path:
                                
                                _copyAigResult =  _scp_without_ssh.copy_to_remote(os.path.join(aig_source_path,'*'), aig_path)
                                self._processes.append({'NODE':server_info['NODE'],'process': _copyAigResult,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG"})

                                if _copyAigResult == 0:
                                    self.__console_msg(_copyAigResult, f'AIG GS Updated Successfully. {tc_package_id}')

                                    # start.sh sleep for a minute
                                    # bgs_start_command = os.path.join(bgs_path, 'bin64', 'restart')
                                    # self._processes.append({'NODE':server_info['NODE'],'process': self._execute(bgs_start_command, os.path.join(aig_path, 'bin64')),'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG BGS Start"})


                                    # start.sh sleep for a minute
                                    # gs_start_command = os.path.join(aig_path, 'bin64', 'restart')
                                    # self._processes.append({'NODE':server_info['NODE'],'process': self._execute(gs_start_command, os.path.join(aig_path, 'bin64')),'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG GS Start"})

                                    # self.__environment_provider.wait_execute(60)

                                    # aig_tc_connection.sh
                                    # aig_tc_command = os.path.join(aig_path, 'custom_scripts', 'aig_tc_connection.sh')                                         
                                    # self._processes.append({'NODE':server_info['NODE'],'process': self._execute('sh ' +aig_tc_command,os.path.join(aig_path, 'custom_scripts')),'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG"})

                                    # build_mmap.sh
                                    # custom_build_mmap_command = os.path.join(aig_path, 'custom_scripts', 'build_mmap.sh')
                                    # self._processes.append({'NODE':server_info['NODE'],'process': self._execute('sh ' + custom_build_mmap_command, os.path.join(aig_path, 'custom_scripts')),'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG"})

                                    # restart.sh sleep for a minute
                                    # gs_restart_command = os.path.join(aig_path, 'bin64', 'restart')
                                    # self._processes.append({'NODE':server_info['NODE'],'process': self._execute(gs_restart_command,os.path.join(aig_path, 'bin64')),'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG"})

                                    # self.__environment_provider.wait_execute(60)

                                    # aig_sap_connection.sh
                                    # aig_sap_command = os.path.join(aig_path, 'custom_scripts', 'aig_sap_connection.sh')
                                    # self._processes.append({'NODE':server_info['NODE'],'process': self._execute('sh ' +aig_sap_command, os.path.join(aig_path, 'custom_scripts')),'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG"})

                                else:
                                    self.log.warning(f'AIG Copy Failed. {tc_package_id}') 
                                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG"})                         

                        else:
                            self.log.warning(f'Replacement Environment is not available in {tc_package_id}')
                            self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG"})
                    else:
                        self.log.warning(f'Replacement not updated {tc_package_id}')
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG"})
                except Exception as exp:
                    self.log.error(f'{exp}')
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - AIG"})
        return self._processes

    def SNC(self):
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 
        
        for index, server_info in enumerate(_execute_servers):
            try: 

                _ssh_command = self.__environment_provider.get_ssh_command(server_info)
                _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))
                _is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
                _target_path =os.path.join(server_info['GS_ROOT'],'snc')
                _check_dir_exists = _scp_with_ssh.check_dir_to_remote(_is_windows,_target_path)
                if _check_dir_exists:
                    delete_files_list = []
                    if 'files_to_delete' in self.__properties[self.__target]:                        
                        delete_files_list = self.__properties[self.__target]['files_to_delete']
                    _result = 0 
                    # Temporary commented the certification deletion part
                    # if len(delete_files_list):
                    #     for file in delete_files_list:
                    #         self.log.info(f'Requesting to Delete - {os.path.join(_target_path,file)}')                            
                    #         delete_result = _scp_with_ssh.remove_file_to_remote(_is_windows,os.path.join(_target_path,file))
                    #         if delete_result != 0:
                    #             _result = 1
                    #             _failed_file = os.path.join(_target_path,file)

                    if _result == 0:                    
                        aig_path = server_info['GS_ROOT']
                        #bgs_path = server_info['BGS_ROOT']
                    
                        # start.sh sleep for a minute
                        gs_start_command = f'cd {os.path.join(aig_path, "bin64")} && {os.path.join(aig_path, "bin64", "restart")}'
                        if _ssh_command != '':
                            gs_start_command = f'{_ssh_command} "{gs_start_command}"'

                        self._processes.append({'NODE':server_info['NODE'], 'process': self._execute(gs_start_command), 'module': self.__module_label, 'package_id': '', 'label': f"AIG GS Start"})

                        # aig_tc_connection.sh
                        #aig_tc_command = os.path.join(aig_path, 'custom_scripts', 'aig_tc_connection.sh')                                         
                        #self._processes.append({'NODE':server_info['NODE'],'process': self._execute('sh ' +aig_tc_command,os.path.join(aig_path, 'custom_scripts')),'module': self.__module_label, 'package_id': '', 'label': f"AIG"})

                        _command = self.__properties[self.__target]['command']   
                        args = f'cd {_target_path} && {os.path.join(_target_path, _command)}'
                        if _ssh_command != '':
                            args = f'{_ssh_command} "{args}"'

                        if _scp_with_ssh.check_dir_to_remote(_is_windows,os.path.join(_target_path, _command)):
                            result = self._execute(args)
                            self.__console_msg(result,'SNC Execution')

                            if result == 0:                                

                                #bgs_start_command = os.path.join(bgs_path, 'bin64', 'restart')
                                #self._processes.append({'NODE':server_info['NODE'],'process': self._execute(bgs_start_command, os.path.join(aig_path, 'bin64')),'module': self.__module_label, 'package_id': '', 'label': f"AIG BGS Start"})
                                
                                #self.__environment_provider.wait_execute(60)                                

                                # aig_sap_connection.sh
                                #aig_sap_command = os.path.join(aig_path, 'custom_scripts', 'aig_sap_connection.sh')
                                #self._processes.append({'NODE':server_info['NODE'],'process': self._execute('sh ' +aig_sap_command, os.path.join(aig_path, 'custom_scripts')),'module': self.__module_label, 'package_id': '', 'label': f"AIG"})
                                
                                # build_mmap.sh
                                custom_build_mmap_command = f'cd {os.path.join(aig_path, "custom_scripts")} && sh {os.path.join(aig_path, "custom_scripts", "build_mmap.sh")}'
                                if _ssh_command != '':
                                    custom_build_mmap_command = f'{_ssh_command} "{custom_build_mmap_command}"'

                                self._processes.append({'NODE':server_info['NODE'], 'process': self._execute(custom_build_mmap_command), 'module': self.__module_label, 'package_id': '', 'label': f"AIG"})

                                self.__environment_provider.wait_execute(20)

                                # restart.sh sleep for a minute
                                gs_restart_command = f'cd {os.path.join(aig_path, "bin64")} && {os.path.join(aig_path, "bin64", "restart")}'
                                if _ssh_command != '':
                                    gs_restart_command = f'{_ssh_command} "{gs_restart_command}"'

                                self._processes.append({'NODE':server_info['NODE'], 'process': self._execute(gs_restart_command), 'module': self.__module_label, 'package_id': '', 'label': f"AIG"})
                        else:
                            self.log.warning(f"{os.path.join(_target_path,_command)} Not exists. SNC Execution Skipped")
                            self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '', 'label': f"[ {self.__target}] - AIG"})
                    # else:
                    #     self.log.error(f'Deleting the file {_failed_file} - Failed.')
                    #     self._processes.append({'NODE':server_info['NODE'],'process': _result,'module': self.__module_label, 'package_id': '', 'label': f"[ {self.__target}] - AIG"})
                else:
                    self.log.warning(f'{_target_path} Does not Exists. Execution Skipped.')
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '', 'label': f"[ {self.__target}] - AIG"})
            except Exception as exp:
                self.log.error(f'Execution Failed - {exp}')                    
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '', 'label': f"[ {self.__target}] - AIG"})
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
                        _processesResult = getattr(AIG, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult             
        except Exception as exp:
            self.log.error(exp)              
            
    def _execute(self, command, path=''):
        
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