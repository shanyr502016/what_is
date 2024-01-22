"""
ITK Build 
"""
import os
from corelib.Loggable import Loggable
from corelib.SSHConnection import SSHConnection
from corelib.File import BaseFile, File, Directory
from corelib.DynamicExecutor import DynamicExecutor
from corelib.SystemExecutor import SystemExecutor
from corelib.RemoteExecutor import RemoteExecutor
from corelib.SCP import SCP
from corelib.Constants import Constants
from corelib.ExceptionHandler import ITKException
from build.lib.TCBuildConfig import TCBuildConfig
from build.lib.TCLib import TCLib

class ITK(Loggable):
    
    def __init__(self, args):   

        super().__init__(__name__)
       
        self.__arguments = args # Set arguments from DynamicImporter
        
        self.__environment = args._environment # Get the Environment Specific Values from config json
        
        self.__environment_provider = args._environment_provider # Get the Environment Provider method. Reusable method derived
    
        self.__module_name = args._module_name # Module name from user command line (Only Module (classname))
        
        self.__module = args._arguments.module # Module name with submodule from user command line (full name)
        
        self.__module_label = self.__module # Module label  
     
        self.__properties = args._properties # Get the Module Specific Values from config json

        self.__security = args._security # Get the Security Values
        
        self.__sub_module_name = args._sub_module_name # Sub Module name from user command line (Only Sub Module (classname))
        
        self.__target = None # Target Instances setup
        
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name) # Scope and target setup based on configuration
  
       
        self._processes = []
        self._processesResult = []
        
        self.tc_build_config = TCBuildConfig(self.__arguments)
        self.tc_lib = TCLib(self.__arguments)

        
    def default(self):        
        return self._executeTargets()

    def build(self):
    
        if 'executeTargets' in self.__properties[self.__target]:

            self._executeCombineTargets()

        else:
        
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
            
            for index, server_info in enumerate(_execute_servers):

                if self.tc_build_config.get_workspace() and self.tc_build_config.get_branch() and self.tc_build_config.get_package_name() and self.tc_build_config.get_tc_version() and self.tc_build_config.get_software_version():

                    # Check the Repo Path and Found the Git Changes
                    DELTA_CHECKOUT_PATH = server_info['DELTA_CHECKOUT_PATH'].replace('$BRANCH', self.tc_build_config.get_branch())
                    commit_logs, delta_changes = self.tc_lib.get_repo_changes(DELTA_CHECKOUT_PATH) # commit logs and file changes
                    
                    self.log.debug(f"Commits Changes: {commit_logs}")

                    __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
                    __is_linux = self.__environment_provider.is_linux(server_info['OS_TYPE'])            
                    
                    packages_lists = self.__properties[self.__target]['packages']

                    _build_status = 1
                    
                    for package_name in packages_lists:
                    
                        package_name = package_name.split(':') 
                    
                        full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())
                        
                        self.log.info(f"{package_name[2]} Package Name: {full_package_name}")

                        location_in_package = os.path.join(self.tc_build_config.get_workspace(), package_name[0], self.__properties[self.__target]['location_in_package'])  

                        location_in_package_with_package_name = os.path.join(package_name[0], self.__properties[self.__target]['location_in_package'])           

                        
                        if __is_windows:

                            # check the git changes present in the package
                            delta_found = any(location_in_package_with_package_name in line for line in delta_changes)

                            if (self.tc_build_config.get_delta_build().lower() == 'true' and delta_found) or self.tc_build_config.get_delta_build().lower() == 'false': 

                                if self.tc_build_config.get_delta_build().lower() == 'true' and delta_found:
                                    self.log.info(f"ITK Delta Code Changes Found") 
                                    self.log.info(commit_logs)                                                                                      
                            
                                ssh_client = None
                                try:     
                                    _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider) 

                                    build_args = []  # calling the build_wnxt64.bat                          

                                    _build_command_with_path = os.path.join(location_in_package, self.__properties[self.__target]['command']).replace('/', '\\')
                                    
                                    build_args.append(_build_command_with_path) 
                                    build_args.append('-m')
                                    
                                    build_args = ' '.join([str(elem) for elem in build_args])   

                        
                                    if _system_executor.check_file_exists(_build_command_with_path) == 0:  
                                        # Preparing the Environment Variables and Escaping the Paths
                                        TC_ROOT = server_info['TC_ROOT'].replace('/', '\\')
                                        TC_ROOT = TC_ROOT.replace('$TC_VERSION', self.tc_build_config.get_tc_version())

                                        TC_BIN = os.path.join(server_info['TC_ROOT'], 'bin').replace('/', '\\')
                                        TC_BIN = TC_BIN.replace('$TC_VERSION', self.tc_build_config.get_tc_version())

                                        VCVARS_FILE = server_info['VCVARS_FILE'].replace('/', '\\')
                                                                    
                                        env_vars = {
                                            'TC_ROOT': TC_ROOT,
                                            'TC_BIN': TC_BIN,
                                            'VCVARS_FILE': VCVARS_FILE
                                        }
                                        try:     
                                            self.log.info(f"Build ITK {package_name[2]} Starting....")

                                            self.log.debug(f"Build Command: {build_args}")                        
                                            exit_code, output, error  = _system_executor.execute(build_args, env_vars=env_vars, error_keywords=self.__properties[self.__target]['error_keywords'], success_keywords=self.__properties[self.__target]['success_keywords'], custom_exception=ITKException)
                                            self._processes.append({'NODE':server_info['NODE'], 'process': exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"ITK {package_name[1]} Build"})
                                            self.__console_msg( exit_code, f"ITK {package_name[1]} Build")
                                            _build_status = exit_code
                                        except ITKException as e:
                                            self.log.error(e)
                                            _build_status = 1
                                        else:
                                            # Command to copy files and folders using xcopy
                                            build_output_location = os.path.join(location_in_package,'output', '*.dll').replace('/', '\\')
                                            destination_path = os.path.join(self.tc_build_config.get_workspace(),package_name[0],self.__properties[self.__target]['location_out_package']).replace('/', '\\')
                                            
                                            mkdir_exit_code, mkdir_output, mkdir_error  = _system_executor.create_directory_if_not_exists(destination_path)
                                            self._processes.append({'NODE':server_info['NODE'], 'process': mkdir_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"Make Directory {destination_path}"})
                                            self.__console_msg( mkdir_exit_code, f"Make Directory {destination_path}")
                                            if mkdir_exit_code == 0:
                                                xcopy_command = f'xcopy "{build_output_location}" "{destination_path}" /Y'
                                                xcopy_exit_code, xcopy_output, xcopy_error  = _system_executor.execute(xcopy_command)
                                                self._processes.append({'NODE':server_info['NODE'], 'process': xcopy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"Copy Output Files into {destination_path}"})
                                                self.__console_msg( xcopy_exit_code, f"Copy Output Files into {destination_path}")

                                            
                                    else:
                                        self.log.warning(f"{_build_command_with_path} File Not Exists! {package_name[2]} Build Skipped")
                                except Exception as e:
                                    self.log.error(f"Failed: {e}")
                            else:
                                if self.tc_build_config.get_delta_build().lower() == 'true' and not delta_found:
                                    self.log.warning(f'Delta Build Enabled! ITK Code Changes Not Found in {package_name[2]}')                                
                                self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"ITK {package_name[1]} Build Skipped"})
                                self.log.warning( f"ITK {package_name[2]} Build Skipped")
                        
                        if __is_linux: 

                             # check the git changes present in the package
                            delta_found = any(location_in_package_with_package_name in line for line in delta_changes)

                            dependent_in_package_with_package_name = os.path.join(package_name[0], self.__properties[self.__target]['dependent_in_package'])     

                            delta_with_dependent_found = any(dependent_in_package_with_package_name in line for line in delta_changes)

                            if (self.tc_build_config.get_delta_build().lower() == 'true' and delta_found or delta_with_dependent_found) or self.tc_build_config.get_delta_build().lower() == 'false': 

                                if self.tc_build_config.get_delta_build().lower() == 'true' and delta_found or delta_with_dependent_found:
                                    self.log.info(f"ITK Delta Code Changes Found") 
                                    self.log.info(commit_logs)    

                                try:
                                    
                                    _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider)  

                                    build_args = []                    
                                    
                                    build_path = os.path.join(self.tc_build_config.get_workspace(),package_name[0],self.__properties[self.__target]['location_in_package'])
                                    
                                    build_command = self.__properties[self.__target]['command']
                                    
                                    build_args.append(f'cd {build_path} && ./{build_command}')                       
                                    
                                    build_args = ' '.join([str(elem) for elem in build_args])                 
                                    
                                                
                                    try:
                                        TC_ROOT = server_info['TC_ROOT']
                                        TC_ROOT = TC_ROOT.replace('$TC_VERSION', self.tc_build_config.get_tc_version())
                                        self.log.debug(f"TC_ROOT: {TC_ROOT}")
                                        self.log.debug(f"BUILD_ARGS: {build_args}")
                                        
                                        env_vars = {
                                            'TC_ROOT': TC_ROOT
                                        }                        
                                        
                                        if os.path.exists(os.path.join(build_path, build_command)):
                                            try:
                                                change_permission_location = os.path.join(self.tc_build_config.get_workspace(),package_name[0])
                                                self.__environment_provider.change_execmod(change_permission_location, '0755')
                                                                            
                                                exit_code, output, error = _system_executor.execute(build_args, env_vars=env_vars, error_keywords=self.__properties[self.__target]['error_keywords'], success_keywords=self.__properties[self.__target]['success_keywords'], custom_exception=ITKException)  # Build
                                                
                                                self._processes.append({'NODE':server_info['NODE'], 'process': exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"ITK {package_name[1]} Build LnxSO"})
                                                self.__console_msg( exit_code, f"ITK {package_name[1]} Build LnxSO")
                                            except ITKException as e:
                                                self.log.error(e)
                                            else:
                                                build_output_location = os.path.join(self.tc_build_config.get_workspace(),package_name[0],self.__properties[self.__target]['location_in_package'],'output', '*.so')
                                                destination_path = os.path.join(self.tc_build_config.get_workspace(),package_name[0],self.__properties[self.__target]['location_out_package'])
                                                
                                                mkdir_exit_code, mkdir_output, mkdir_error  = _system_executor.create_directory_if_not_exists(destination_path)
                                                self._processes.append({'NODE':server_info['NODE'], 'process': mkdir_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"Make Directory {destination_path}"})
                                                self.__console_msg( mkdir_exit_code, f"Make Directory {destination_path}")
                                                
                                                if mkdir_exit_code == 0:                                                                       
                                                    copy_exit_code = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_local(build_output_location,destination_path)
                                                    self._processes.append({'NODE':server_info['NODE'], 'process': copy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"Copy Output Files into {destination_path}"})
                                                    self.__console_msg( copy_exit_code, f"Copy Output Files into {destination_path}")
                                        else:
                                            self.log.warning(f"{os.path.join(build_path, build_command )} File Not Exists! {package_name[2]} Build Skipped ")
                                    except Exception as e:
                                        self.log.error(f"Executions failed: {e}")    
                                except Exception as e:
                                    self.log.error(f"Failed: {e}")    
                            else:
                                if self.tc_build_config.get_delta_build().lower() == 'true' and not delta_found:
                                    self.log.warning(f'Delta Build Enabled! ITK Code Changes Not Found in {package_name[2]}')                                
                                self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"ITK {package_name[1]} Build Skipped"})
                                self.log.warning( f"ITK {package_name[2]} Build Skipped")                
                            
                    
            return self._processes        
        
                    
                                    
    def _executeCombineTargets(self):
        try:
            for thread_count, targets in enumerate(self.__environment_provider.get_execute_targets(self.__target).split(',')):
                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name

                if dynamicExecutor.get_sub_module_name():  
                    _processesResult = getattr(ITK, dynamicExecutor.get_sub_module_name())(self)
                else:
                    _processesResult = dynamicExecutor.run_module()
                self._processesResult = self._processesResult + _processesResult  
            return self._processesResult
        except Exception as exp:
            self.log.error(exp)
            
    def __console_msg(self, result, action_msg):
        
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')