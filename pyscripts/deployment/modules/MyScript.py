from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.SCP import SCP
from corelib.Constants import Constants
import os


class MyScript(Loggable):
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


        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel 

    def default(self):        
        return self._executeTargets()


    def AWC(self):
    
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        
        for index, server_info in enumerate(_execute_servers):
        
            _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))

            _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

            _is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            
            try:
                location_in_share = None
                if 'location_in_share' in self.__properties[self.__target]:
                    location_in_share = os.path.join(self.__properties[self.__target]['location_in_share'], server_info['MYSCRIPT_AW_PATH'])
                    
                    if os.path.exists(location_in_share):
                    
                        _deploy_paths = {}
                        if 'source_path' in self.__properties[self.__target] and 'destination_path' in self.__properties[self.__target]:
                           _deploy_paths[self.__properties[self.__target]['source_path']] = self.__properties[self.__target]['destination_path']
                    
                        for deploy_path in _deploy_paths:
                            if '$' in deploy_path:
                                _replace_deploy_path = deploy_path.split('/')[0][1:]
                                _destination = deploy_path.replace(f'${_replace_deploy_path}',server_info[_replace_deploy_path])
                                _deploy_paths.update({_destination:_deploy_paths[deploy_path]})
                                _deploy_paths.pop(deploy_path)
                            
                        if location_in_share is not None and len(_deploy_paths):
                        
                            for _deploy_execution_path in _deploy_paths:
                            
                                self.log.info(f'Copying files from [{location_in_share}] to [{_deploy_execution_path}]')
                                
                                if _scp_with_ssh.check_dir_to_remote(_is_windows,_deploy_execution_path):
                                
                                    for files in _deploy_paths[_deploy_execution_path]:
                                    
                                        copy_result = _scp_without_ssh.copy_to_remote(os.path.join(location_in_share,files),_deploy_execution_path)
                                    
                                        self.__console_msg(copy_result,f'[{os.path.join(location_in_share,files)}] into [{_deploy_execution_path}] Updated')
                                        
                                        self._processes.append({'NODE':server_info['NODE'],'process': copy_result,'module': self.__module_label, 'package_id': '','label': f"Myscript AWC"})
                                else:
                                    self.log.warning(f'{_deploy_execution_path} not Exists')
                                    self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': '','label': f"Myscript AWC"})                            
                        else:
                            self.log.warning(f'{location_in_share} not exists')
                            self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': '','label': f"Myscript AWC"})
                                
                    else:
                        self.log.warning(f'{location_in_share} not exists')
                        self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': '','label': f"Myscript AWC"})
                else:
                    self.log.warning(f'{"Source" if location_in_share is None else "Destination"} path is missing in configuration.delpoy skipped...')            
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript AWC"})   

            except Exception as exp:
                self.log.error(f"Execution Failed {exp}")
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript AWC"})
           
    
        return self._processes
    
    def Core(self):

        if 'executeTargets' in self.__properties[self.__target]:

            self._executeCombineTargets()

        else:

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

            for index, server_info in enumerate(_execute_servers):

                _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))

                _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

                _is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])

                try:
                    location_in_share = None
                    if 'location_in_share' in self.__properties[self.__target]:
                        location_in_share = os.path.join(self.__properties[self.__target]['location_in_share'], server_info['MYSCRIPT_CORE_PATH'])                       
                        
                        if os.path.exists(location_in_share):
                        
                            _deploy_paths = {}
                            if 'source_path' in self.__properties[self.__target] and 'destination_path' in self.__properties[self.__target]:
                                _deploy_paths[self.__properties[self.__target]['source_path']] = self.__properties[self.__target]['destination_path']
                                
                            if 'so_source_path' in self.__properties[self.__target] and 'so_destination_path' in self.__properties[self.__target]:
                                _deploy_paths[self.__properties[self.__target]['so_source_path']] = self.__properties[self.__target]['so_destination_path']
                                
                            if 'soa_source_path' in self.__properties[self.__target] and 'soa_destination_path' in self.__properties[self.__target]:
                                _deploy_paths[self.__properties[self.__target]['soa_source_path']] = self.__properties[self.__target]['soa_destination_path']
                                
                            
                                
                            for deploy_path in _deploy_paths:
                                if '$' in deploy_path:
                                    _replace_deploy_path = deploy_path.split('/')[0][1:]
                                    _destination = deploy_path.replace(f'${_replace_deploy_path}',server_info[_replace_deploy_path])
                                    _deploy_paths.update({_destination:_deploy_paths[deploy_path]})
                                    _deploy_paths.pop(deploy_path)
                            
                            if location_in_share is not None and len(_deploy_paths):
                            
                                for _deploy_execution_path in _deploy_paths:
                                
                                    self.log.info(f'Copying files from [{location_in_share}] to [{_deploy_execution_path}]')
                                    
                                    if _scp_with_ssh.check_dir_to_remote(_is_windows,_deploy_execution_path):
                                    
                                        for files in _deploy_paths[_deploy_execution_path]:
                                        
                                            copy_result = _scp_without_ssh.copy_to_remote(os.path.join(location_in_share,files),_deploy_execution_path)
                                        
                                            self.__console_msg(copy_result,f'[{os.path.join(location_in_share,files)}] into [{_deploy_execution_path}] Updated')
                                            
                                            self._processes.append({'NODE':server_info['NODE'],'process': copy_result,'module': self.__module_label, 'package_id': '','label': f"Myscript Core"})
                                    else:
                                        self.log.warning(f'{_deploy_execution_path} not Exists')
                                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript Core"})
                            else:
                                self.log.warning(f'{location_in_share} not exists')
                                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript Core"})
                        else:
                            self.log.warning(f'{location_in_share} not exists')
                            self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript Core"})

                    else:
                        self.log.warning(f'{"Source" if location_in_share is None else "Destination"} path is missing in configuration.delpoy skipped...')            
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript Core"})   

                except Exception as exp:
                    self.log.error(f"Execution Failed {exp}")
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript Core"})

            return self._processes
    

    def Deploy(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        for index, server_info in enumerate(_execute_servers):

            _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))

            _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

            _is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])

            lua_path = None
            if 'lua_path' in self.__properties[self.__target]:
                lua_path = self.__properties[self.__target]['lua_path']            
                

            _destination_path = None
            if 'destination_path' in self.__properties[self.__target]:
                _destination_path = self.__properties[self.__target]['destination_path'].replace(f'$ENVIRONMENT_NAME',self.__environment_provider.get_environment_name().lower())               
                

            try:

                if lua_path is not None and _destination_path is not None:

                    if _scp_with_ssh.check_dir_to_remote(_is_windows,_destination_path):                    
                    
                        if _scp_with_ssh.check_dir_to_remote(_is_windows,os.path.join(_destination_path,lua_path)):                        
                            _scp_with_ssh.remove_file_to_remote(_is_windows,os.path.join(_destination_path,lua_path),True)                        
                        _scp_with_ssh.create_dir_to_remote(_is_windows,os.path.join(_destination_path,lua_path))                         
                            
                        
                        _result = 1

                        for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):
                        
                            _source_path = None
                            
                            
                            if 'location_in_package' in self.__properties[self.__target]:
                                _source_path = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                                
                            if os.path.exists(_source_path):
                                copy_result = _scp_without_ssh.copy_to_remote(os.path.join(_source_path,'*'),os.path.join(_destination_path,lua_path))
                                self.__console_msg(copy_result,f'{os.path.join(_destination_path,lua_path)} copied')
                                
                                if copy_result == 0:
                                    _result = 0
                            
                                if copy_result == 0:
                                    self.log.info(f'Updating {lua_path} in tc_profilevars')
                                    out_content = []
                                    try:
                                        self.log.info(f"{os.path.join(server_info['TC_DATA'],'tc_profilevars')} TCProfileVars File")
                                        with open((os.path.join(server_info['TC_DATA'],'tc_profilevars'))) as tc_profile:
                                            check_exists = False
                                            content = tc_profile.readlines()
                                            for index,lines in enumerate(content):
                                                if 'LUA_PATH' in lines:
                                                    lines = 'LUA_PATH='+ os.path.join(_destination_path,lua_path,'?.lua')+'; export LUA_PATH\n'
                                                    check_exists = True
                                                out_content.append(lines)
                                            if not check_exists:
                                                out_content = []
                                                for index,newlines in enumerate(content):
                                                    if 'TC_BUILD_DATE' in newlines:
                                                        newlines = content[index] + '\nLUA_PATH='+ os.path.join(_destination_path,lua_path,'?.lua')+'; export LUA_PATH\n'
                                                        self.log.debug(newlines)
                                                    out_content.append(newlines)
                                        if len(out_content):
                                            with open((os.path.join(server_info['TC_DATA'],'tc_profilevars')),'w') as tc_profile_file:
                                                tc_profile_file.writelines(out_content)
                                                self.__console_msg(copy_result,f'tc_profilevars LUA_PATH Updated')
                                        else:
                                            self.log.error(f'tc_profilevars not Updated...')   
                                            self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript Deployscripts"})
                                    
                                    except Exception as exp:
                                        self.log.error(f'unable to access the tc_profilevars - {exp}')   
                                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript Deployscripts"})
                            
                                else:
                                    self.log.error(f"{os.path.join(_destination_path,lua_path)} Copied Failed")
                                    self._processes.append({'NODE':server_info['NODE'],'process': copy_result,'module': self.__module_label, 'package_id': '','label': f"Myscript Deployscripts"})

                            else:
                                self.log.warning(f"Required File or Folder not Present from this location {tc_package_id} {__class__.__name__} Skipped")
                                self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - Myscript Deploy to {server_info['HOSTNAME']}"})
                    else:
                        self.log.warning(f"{_destination_path} not Exists. Delpoyment skipped... ")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript Deployscripts"})
                
                else:
                    self.log.warning(f'{"LUA_PATH" if lua_path is None else "Destination"} is missing in configuration.delpoy skipped...')            
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript Deployscripts"})   

            except Exception as exp:
                self.log.error(f"Execution Failed {exp}")
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"Myscript Deployscripts"})

        return self._processes

    
    def _executeCombineTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__target).split(',')):
                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name

                if dynamicExecutor.get_sub_module_name():  
                    _processesResult = getattr(MyScript, dynamicExecutor.get_sub_module_name())(self)
                else:
                    _processesResult = dynamicExecutor.run_module()
                self._processesResult = self._processesResult + _processesResult  
            return self._processesResult
        except Exception as exp:
            self.log.error(exp)
             
            
    def _execute(self, command, path): 
        """
        Used to process services/command
        """
        process = Process(command, path)
        process.set_parallel_execution(self._parallel)
        return process.execute() 
     
    def __console_msg(self, result, action_msg):
        
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Copied Failed.")
        self.log.info('..............................................................')
