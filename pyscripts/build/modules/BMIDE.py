"""
BMIDE Build 
"""
import os
from corelib.Loggable import Loggable
from corelib.File import BaseFile, File, Directory
from corelib.DynamicExecutor import DynamicExecutor
from corelib.RemoteExecutor import RemoteExecutor
from corelib.SystemExecutor import SystemExecutor
from corelib.Constants import Constants
from corelib.SCP import SCP
from corelib.ExceptionHandler import BMIDEException, DLLsException
from build.lib.TCBuildConfig import TCBuildConfig
from build.lib.TCLib import TCLib

class BMIDE(Loggable):
    
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
                      
                    BMIDE_LOCATION = server_info['BMIDE_LOCATION'].replace('$TC_VERSION', self.tc_build_config.get_tc_version())
                    
                    self.log.debug(f"BMIDE_LOCATION: {BMIDE_LOCATION}")
                    
                    self.log.debug(f"Commits Changes: {commit_logs}")

                    BMIDE_TEMPLATE_LOCATION = server_info['BMIDE_TEMPLATE_LOCATION']

                    self.log.debug(f"BMIDE_TEMPLATE_LOCATION: {BMIDE_LOCATION}")
                        
                    __ssh_command = self.__environment_provider.get_ssh_command(server_info)
                    __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
                    __is_linux = self.__environment_provider.is_linux(server_info['OS_TYPE'])
                    
                    packages_lists = self.__properties[self.__target]['packages']
                    
                    _dependent_build_status = 1
                    _non_dependent_build_status = 1                   
                    
                    for package_name in packages_lists:
                    
                        package_name = package_name.split(':') 
                    
                        full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())
                        
                        self.log.info(f"{package_name[2]} Package Name: {full_package_name}")


                        TC_ROOT = server_info['TC_ROOT'].replace('/', '\\')
                        TC_ROOT = TC_ROOT.replace('$TC_VERSION', self.tc_build_config.get_tc_version())

                        location_in_package = os.path.join(self.tc_build_config.get_workspace(), package_name[0], self.__properties[self.__target]['location_in_package'])

                        BMIDE_BUILD_VERSION = self.__properties[self.__target]['bmide_build_version']

                        bmide_out_package_pattern = self.__properties[self.__target]['bmide_out_package_pattern']

                        bmide_out_package = self.tc_build_config.get_bmide_out_folder_name(bmide_out_package_pattern, package_name[1], self.tc_build_config.get_software_version(), BMIDE_BUILD_VERSION, self.tc_build_config.get_tc_version() )

                        #bmide_out_package = f"{package_name[1]}_all_{self.tc_build_config.get_software_version()}_{BMIDE_BUILD_VERSION}_{self.tc_build_config.get_tc_version()}"

                        self.log.info(f"Build Package Folder Name: {bmide_out_package}")

                        location_out_package = os.path.join(self.tc_build_config.get_workspace(), package_name[0], self.__properties[self.__target]['location_in_package'], bmide_out_package).replace('/', '\\')   
                 

                        PROJECT_LOCATION = os.path.join(location_in_package, package_name[1]).replace('/', '\\')
                        PACKAGE_LOCATION = os.path.join(location_in_package).replace('/', '\\')
                        BMIDE_TEMPLATES_DIR = os.path.join(BMIDE_TEMPLATE_LOCATION, self.tc_build_config.get_branch()).replace('/', '\\')
                        BMIDE_LOG_PATH = os.path.join(location_in_package, f'{full_package_name}_bmide.log').replace('/', '\\')   

                        location_in_package_with_package_name = os.path.join(package_name[0], self.__properties[self.__target]['location_in_package'], package_name[1])                        
              
                        if __is_windows:
                            
                            # check the git changes present in the package
                            delta_found = any(location_in_package_with_package_name in line for line in delta_changes)
                            
                            self.log.debug(delta_changes)
                            

                            if (self.tc_build_config.get_delta_build().lower() == 'true' and delta_found) or self.tc_build_config.get_delta_build().lower() == 'false': 

                                if self.tc_build_config.get_delta_build().lower() == 'true' and delta_found:
                                    self.log.info(f"BMIDE Delta Code Changes Found") 
                                    self.log.info(commit_logs) 
                                try:
                                    _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider) 

                                    build_args = []

                                    build_args.append(os.path.join(BMIDE_LOCATION,self.__properties[self.__target]['command']).replace('/', '\\'))                       
                            
                                    build_args.append(f"-projectLocation={PROJECT_LOCATION}")                        
                            
                                    build_args.append(f"-packageLocation={PACKAGE_LOCATION}")                        
                            
                                    build_args.append(f"-dependencyTemplateFolder={BMIDE_TEMPLATES_DIR}")
                            
                                    build_args.append(f"-softwareVersion='{self.tc_build_config.get_software_version()}'")
                            
                                    build_args.append(f"-buildVersion={BMIDE_BUILD_VERSION}")
                            
                                    build_args.append(f"-allPlatform")                       
                            
                                    build_args.append(f"-log={BMIDE_LOG_PATH}")
                            
                                    build_args = ' '.join([str(elem) for elem in build_args])             
                                    
                                    if package_name[2] == self.__properties[self.__target]['build_dependent']:
                                        try:                                       

                                            self.log.info(f"Build BMIDE {package_name[2]} Starting....")

                                            self.log.debug(f"Build Command: {build_args}")

                                            exit_code, output, error = _system_executor.execute(build_args, env_vars={}, execution_location='', error_keywords=self.__properties[self.__target]['error_keywords'], success_keywords=self.__properties[self.__target]['success_keywords'], custom_exception=BMIDEException)
                                            self._processes.append({'NODE':server_info['NODE'], 'process': exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE Build {package_name[1]}"})
                                            self.__console_msg( exit_code, f"BMIDE {package_name[2]} Build")


                                            # BMIDE Build Dependent Package
                                            _dependent_build_status = exit_code

                                        except BMIDEException as e:
                                            self.log.error(e)
                                            _dependent_build_status = 1

                                        else: # Build Completed without any Exception
                                            # BMIDE Build Successful, Update the Template and dependency files into tc root
                                            self.log.info(f"Build BMIDE {package_name[2]} Dependency and Template Copied to TC_ROOT {TC_ROOT}....")

                                            self.log.info(f"Build Output path: {location_out_package}")

                                            # Command to extract a specific file using 7-Zip
                                            output_template_path = os.path.join(BMIDE_TEMPLATE_LOCATION, self.tc_build_config.get_branch()).replace('/', '\\')

                                            template_path = os.path.join(location_in_package, f"{bmide_out_package}", 'artifacts', f'{package_name[1]}_template.zip').replace('/', '\\')
                                            

                                            template_args = f"{server_info['7ZIP_PATH']} e {template_path} -o{output_template_path} {package_name[1]}_template.xml -r -y"
                                            template_exit_code, template_output, template_error = _system_executor.execute(template_args, custom_exception=BMIDEException)
                                            _dependent_build_status = template_exit_code
                                            self._processes.append({'NODE':server_info['NODE'], 'process': template_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"Extract {package_name[1]}_template.xml"})
                                            self.__console_msg( template_exit_code, f"Extract {package_name[1]}_template.xml")
                                            
                                            if template_exit_code == 0:
                                                # Command to extract a specific file using 7-Zip
                                                dependency_args = f"{server_info['7ZIP_PATH']} e {template_path} -o{output_template_path} {package_name[1]}_dependency.xml -r -y"
                                                dependency_exit_code, dependency_output, dependency_error = _system_executor.execute(dependency_args, custom_exception=BMIDEException)
                                                _dependent_build_status = dependency_exit_code
                                                if dependency_exit_code == 0:
                                                    self._processes.append({'NODE':server_info['NODE'], 'process': dependency_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"Extract {package_name[1]}_dependency.xml"})
                                                    self.__console_msg( dependency_exit_code, f"Extract {package_name[1]}_dependency.xml")                                           
                                                    
                                    
                                    try:
                                        # BMIDE Dependent Build Successful, lets start Business package build
                                        
                                        if package_name[2] != self.__properties[self.__target]['build_dependent'] and _dependent_build_status == 0:

                                            self.log.info(f"Build BMIDE {package_name[2]} Starting....")
                                            
                                            self.log.debug(f"Build Command: {build_args}")

                                            exit_code, output, error = _system_executor.execute(build_args, env_vars={}, execution_location='', error_keywords=self.__properties[self.__target]['error_keywords'], success_keywords=self.__properties[self.__target]['success_keywords'], custom_exception=BMIDEException)
                                            self._processes.append({'NODE':server_info['NODE'], 'process': exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE {package_name[1]} Build"})
                                            self.__console_msg( exit_code, f"BMIDE {package_name[1]} Build") 
                                            
                                            _non_dependent_build_status = exit_code

                                    except BMIDEException as e:
                                        _non_dependent_build_status = 1

                                    #else: # Build Completed without any Exception
                                        #if self.tc_build_config.get_artifacts_creation().lower() == 'true' and _dependent_build_status == 0 and _non_dependent_build_status == 0:
                                            
                                            #self.log.info(f"BMIDE Create Package.....")
                                            # Package Creation in Separate Command                          
                                    
                                except Exception as e:
                                    self.log.error(f"Exception failed: {e}")
                            else:
                                if self.tc_build_config.get_delta_build().lower() == 'true' and not delta_found:
                                    self.log.warning(f'Delta Build Enabled! BMIDE Build Win Code Changes Not Found in {package_name[2]}')                                
                                self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE {package_name[1]} Build Skipped"})
                                self.log.warning( f"BMIDE {package_name[2]} Build Skipped")
                            
                                
                        if __is_linux:
                            self.log.info("TODO: Not Implemented")
                                            
            return self._processes        


    def dlls(self):
    
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

                            
                    __ssh_command = self.__environment_provider.get_ssh_command(server_info)
                    __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
                    __is_linux = self.__environment_provider.is_linux(server_info['OS_TYPE'])
                    
                    BMIDE_TEMPLATE_LOCATION = server_info['BMIDE_TEMPLATE_LOCATION']
                    
                    packages_lists = self.__properties[self.__target]['packages']
                    
                    _build_status = 1
                    
                    for package_name in packages_lists:
                    
                        package_name = package_name.split(':') 
                    
                        full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())
                        
                        self.log.info(f"{package_name[2]} Package Name: {full_package_name}")

                        location_in_package = os.path.join(self.tc_build_config.get_workspace(), package_name[0], self.__properties[self.__target]['location_in_package'])

                        location_in_package_with_package_name = os.path.join(package_name[0], self.__properties[self.__target]['location_in_package'], package_name[1])   
                        
                        if __is_windows: 

                            # check the git changes present in the package
                            delta_found = any(location_in_package_with_package_name in line for line in delta_changes)

                            if (self.tc_build_config.get_delta_build().lower() == 'true' and delta_found) or self.tc_build_config.get_delta_build().lower() == 'false': 

                                if self.tc_build_config.get_delta_build().lower() == 'true' and delta_found:
                                    self.log.info(f"BMIDE DLLs Delta Code Changes Found") 
                                    self.log.info(commit_logs)                      
                            
                                try:                    
                                    _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider) 

                                    build_args = []
                                
                                    _build_command_with_path = os.path.join(location_in_package, package_name[1] ,self.__properties[self.__target]['command']).replace('/', '\\')                    
                                
                                    build_args.append(_build_command_with_path)
                                    build_args.append('-m')                
                                    
                                    build_args = ' '.join([str(elem) for elem in build_args])                    
                                    
                            
                                    if _system_executor.check_file_exists(_build_command_with_path) == 0:                               

                                        execution_location = os.path.join(location_in_package, package_name[1]).replace('/', '\\')
                                        BMIDE_TEMPLATES_DIR = os.path.join(BMIDE_TEMPLATE_LOCATION, self.tc_build_config.get_branch()).replace('/', '\\')                    
                                        SMO_SM4_SERVER_BASEPATH = os.path.join(self.tc_build_config.get_workspace(),package_name[0],self.__properties[self.__target]['server_code_in_package']).replace('/', '\\')
                                        
                                        # Preparing the Environment Variables and Escaping the Paths
                                        TC_ROOT = server_info['TC_ROOT'].replace('/', '\\')
                                        TC_ROOT = TC_ROOT.replace('$TC_VERSION', self.tc_build_config.get_tc_version())

                                        TC_BIN = os.path.join(server_info['TC_ROOT'], 'bin').replace('/', '\\')
                                        TC_BIN = TC_BIN.replace('$TC_VERSION', self.tc_build_config.get_tc_version())

                                        VCVARS_FILE = server_info['VCVARS_FILE'].replace('/', '\\')
                                                                        
                                        env_vars = {
                                            'TC_ROOT': TC_ROOT,
                                            'TC_BIN': TC_BIN,
                                            'VCVARS_FILE': VCVARS_FILE,
                                            'BMIDE_TEMPLATES_DIR': BMIDE_TEMPLATES_DIR,
                                            'SMO_SM4_SERVER_BASEPATH': SMO_SM4_SERVER_BASEPATH
                                        }
                                        
                                        try:          
                                            self.log.info(f"Build BMIDE DLLs {package_name[2]} Starting....")

                                            self.log.debug(f"Build Command: {build_args}") 

                                            exit_code, output, error  = _system_executor.execute(build_args, execution_location=execution_location, env_vars=env_vars, error_keywords=self.__properties[self.__target]['error_keywords'], success_keywords=self.__properties[self.__target]['success_keywords'], custom_exception=DLLsException)
                                            self._processes.append({'NODE':server_info['NODE'], 'process': exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE DLLs {package_name[1]} Build"})
                                            self.__console_msg( exit_code, f"BMIDE DLLs {package_name[1]} Build")
                                            _build_status = exit_code
                                        except DLLsException as e:
                                            self.log.error(e)
                                            _build_status = 1
                                        else:
                                            # Command to copy files and folders using xcopy
                                            build_output_location = os.path.join(location_in_package, package_name[1], 'output', 'wntx64', 'lib','*.dll').replace('/', '\\')

                                            destination_path = os.path.join(self.tc_build_config.get_workspace(),package_name[0],self.__properties[self.__target]['location_out_package']).replace('/', '\\')
                                            
                                            mkdir_exit_code, mkdir_output, mkdir_error  = _system_executor.create_directory_if_not_exists(destination_path)
                                            self._processes.append({'NODE':server_info['NODE'], 'process': mkdir_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"Make Directory {destination_path}"})
                                            self.__console_msg( mkdir_exit_code, f"Make Directory {destination_path}")
                                            if mkdir_exit_code == 0:
                                                xcopy_command = f'xcopy "{build_output_location}" "{destination_path}" /Y'
                                                xcopy_exit_code, xcopy_output, xcopy_error  = _system_executor.execute(xcopy_command)
                                                _build_status = exit_code
                                                self._processes.append({'NODE':server_info['NODE'], 'process': xcopy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"Copy Output Files into {destination_path}"})
                                                self.__console_msg( xcopy_exit_code, f"Copy Output Files into {destination_path}")   
                                            else:
                                                _build_status = 1
                                            
                                    else:
                                        self.log.warning(f"{_build_command_with_path} File Not Exists! {package_name[2]} Build Skipped")
                                except Exception as e:
                                    self.log.error(f"BMIDE DLLs failed: {e}")
                            else:
                                if self.tc_build_config.get_delta_build().lower() == 'true' and not delta_found:
                                    self.log.warning(f'Delta Build Enabled! BMIDE DLLs Build Win Code Changes Not Found in {package_name[2]}')                                
                                self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE DLLs {package_name[1]} Build Skipped"})
                                self.log.warning( f"BMIDE DLLs {package_name[2]} Build Skipped")
                            
                        if __is_linux:  
                            self.log.info("TODO: Not Implemented")           

            return self._processes 
                    

    def so(self):
    
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

                           
                    __ssh_command = self.__environment_provider.get_ssh_command(server_info)
                    __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
                    __is_linux = self.__environment_provider.is_linux(server_info['OS_TYPE'])
                    
                    BMIDE_TEMPLATE_LOCATION = server_info['BMIDE_TEMPLATE_LOCATION']
                    
                    packages_lists = self.__properties[self.__target]['packages']
                    _build_status = 1
                    for package_name in packages_lists:
                    
                        package_name = package_name.split(':') 
                    
                        full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())
                        
                        self.log.info(f"Package Name: {full_package_name}") 

                        location_in_package_with_package_name = os.path.join(package_name[0], self.__properties[self.__target]['location_in_package'], package_name[1])  

                        server_code_in_package_with_package_name = os.path.join(package_name[0], self.__properties[self.__target]['server_code_in_package'])                  
                        
                        if __is_windows:
                        
                            self.log.info("TODO")
                        if __is_linux:

                            # check the git changes present in the package
                            delta_found = any(location_in_package_with_package_name in line for line in delta_changes)

                            

                            if (self.tc_build_config.get_delta_build().lower() == 'true' and delta_found ) or self.tc_build_config.get_delta_build().lower() == 'false': 

                                if self.tc_build_config.get_delta_build().lower() == 'true' and delta_found:
                                    self.log.info(f"BMIDE DLLs Delta Code Changes Found") 
                                    self.log.info(commit_logs) 
                        
                                _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider)  
                            
                                build_args = []
                                
                                build_path = os.path.join(self.tc_build_config.get_workspace(),package_name[0],self.__properties[self.__target]['location_in_package'], package_name[1])
                                
                                build_command = self.__properties[self.__target]['command']                       
                                                
                                build_args.append(f'cd {build_path} && ./{build_command}')                  
                                                        
                                build_args = ' '.join([str(elem) for elem in build_args])                
                            
                                try:
                                    TC_ROOT = server_info['TC_ROOT']
                                    TC_ROOT = TC_ROOT.replace('$TC_VERSION', self.tc_build_config.get_tc_version())
                                    
                                    BMIDE_TEMPLATES_DIR = os.path.join(BMIDE_TEMPLATE_LOCATION, self.tc_build_config.get_branch())
                                
                                    SMO_SM4_SERVER_BASEPATH = os.path.join(self.tc_build_config.get_workspace(),package_name[0],self.__properties[self.__target]['server_code_in_package'])
                                    
                                    self.log.debug(f"TC_ROOT: {TC_ROOT}")
                                    self.log.debug(f"BMIDE_TEMPLATES_DIR: {BMIDE_TEMPLATES_DIR}")
                                    self.log.debug(f"SMO_SM4_SERVER_BASEPATH: {SMO_SM4_SERVER_BASEPATH}") 
                                    self.log.debug(f"BUILD_ARGS: {build_args}")
                                    env_vars = {
                                        'TC_ROOT': TC_ROOT,
                                        'BMIDE_TEMPLATES_DIR': BMIDE_TEMPLATES_DIR,
                                        'SMO_SM4_SERVER_BASEPATH': SMO_SM4_SERVER_BASEPATH
                                    }
                                    if os.path.exists(os.path.join(build_path, build_command)):
                                        try:
                                            change_permission_location = os.path.join(self.tc_build_config.get_workspace(),package_name[0])
                                            self.__environment_provider.change_execmod(change_permission_location, '0755')
                                                                        
                                            exit_code, output, error = _system_executor.execute(build_args, env_vars=env_vars, error_keywords=self.__properties[self.__target]['error_keywords'], success_keywords=self.__properties[self.__target]['success_keywords'], custom_exception=BMIDEException)  # Build
                                            
                                            self._processes.append({'NODE':server_info['NODE'], 'process': exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE {package_name[1]} Build LnxSO"})
                                            self.__console_msg( exit_code, f"BMIDE {package_name[1]} Build Lnx BMIDE SOs")
                                            _build_status = exit_code
                                        except BMIDEException as e:
                                            self.log.error(e)
                                            _build_status = 1
                                        else:
                                            build_output_location = os.path.join(self.tc_build_config.get_workspace(),package_name[0],self.__properties[self.__target]['location_in_package'],package_name[1],'output', 'lnx64', 'lib', '*.so')
                                            destination_path = os.path.join(self.tc_build_config.get_workspace(),package_name[0],self.__properties[self.__target]['location_out_package'])
                                            
                                            mkdir_exit_code, mkdir_output, mkdir_error  = _system_executor.create_directory_if_not_exists(destination_path)
                                            self._processes.append({'NODE':server_info['NODE'], 'process': mkdir_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"Make Directory {destination_path}"})
                                            self.__console_msg( mkdir_exit_code, f"Make Directory {destination_path}")
                                            
                                            if mkdir_exit_code == 0:                                                                       
                                                copy_exit_code = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_local(build_output_location,destination_path)
                                                _build_status = copy_exit_code
                                                self._processes.append({'NODE':server_info['NODE'], 'process': copy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"Copy Output Files into {destination_path}"})
                                                self.__console_msg( copy_exit_code, f"Copy Output Files into {destination_path}")
                                    
                                    else:
                                        self.log.warning(f"{os.path.join(build_path, build_command )} File Not Exists! {package_name[2]} Build Skipped ")
                                    
                                except Exception as e:
                                    self.log.error(f"BMIDE failed: {e}")
                            else:
                                if self.tc_build_config.get_delta_build().lower() == 'true' and not delta_found:
                                    self.log.warning(f'Delta Build Enabled! BMIDE SO Build Lnx Code Changes Not Found in {package_name[2]}')                                
                                self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE SO {package_name[2]} Build Skipped"})
                                self.log.warning( f"BMIDE SO {package_name[2]} Build Skipped")
                
            return self._processes 

            
    
    
    def _executeCombineTargets(self):
        try:
            for thread_count, targets in enumerate(self.__environment_provider.get_execute_targets(self.__target).split(',')):
                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name

                if dynamicExecutor.get_sub_module_name():  
                    _processesResult = getattr(BMIDE, dynamicExecutor.get_sub_module_name())(self)
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