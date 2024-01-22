"""CreatePackage"""
import os
from corelib.Loggable import Loggable
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants
from corelib.Properties import Properties
from corelib.GitUtilities import GitUtilities
from build.lib.TCBuildConfig import TCBuildConfig
from build.lib.TCLib import TCLib
from corelib.SystemExecutor import SystemExecutor
from corelib.ExceptionHandler import PackageException

class BuildPackage(Loggable):
    
    def __init__(self, args):   

        super().__init__(__name__)
        
        self.__arguments = args # Set arguments from DynamicImporter
        
        self.__environment = args._environment # Get the Environment Specific Values from config json
        
        self.__environment_provider = args._environment_provider # Get the Environment Provider method. Reusable method derived
    
        self.__module_name = args._module_name # Module name from user command line (Only Module (classname))
        
        self.__module = args._arguments.module # Module name with submodule from user command line (full name)

        self.__module_label = self.__module # Module label 

        self.__properties = args._properties # Get the Module Specific Values from config json

        self.__sub_module_name = args._sub_module_name # Sub Module name from user command line (Only Sub Module (classname))
        
        self.__target = None # Target Instances setup
        
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name) # Scope and target setup based on configuration           
        
        self.__git_provider = GitUtilities()

        self._processes = []
        self._processesResult = []

        self.tc_build_config = TCBuildConfig(self.__arguments)

        self.tc_lib = TCLib(self.__arguments)

        self.props_lib = Properties(self.__arguments)


    def checkproperties(self):

        self.log.info("Pre Validation")
        if 'executeTargets' in self.__properties[self.__target]:

            self._executeCombineTargets()

        else:
        
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
            
            for index, server_info in enumerate(_execute_servers):
                try:
                    if self.tc_build_config.get_workspace():

                        self.log.debug(f"Workspace Location: {self.tc_build_config.get_workspace()}")

                        packages_lists = self.__properties[self.__target]['packages'] 

                        _excludes_extension = self.__properties[self.__target]['excludes_replacements_extension']

                        _excludes_replacements = self.__properties[self.__target]['excludes_replacements']

                        for package_name in packages_lists: 

                            package_name = package_name.split(':')

                            package_location = os.path.join(self.tc_build_config.get_workspace(),package_name[0])

                            # Properties Folder location
                            properties_config_in_package = os.path.join(package_location, self.__properties[self.__target]['location_in_package'])

                            if os.path.exists(properties_config_in_package):

                                # Only listing the environment directory
                                environment_folders = [d for d in os.listdir(properties_config_in_package) if os.path.isdir(os.path.join(properties_config_in_package, d))]
                                
                                for environment_folder in environment_folders: # check each environment
                                    _status = 0
                                    self.log.info(f"{package_name[0]} Checking the Environment Folders {environment_folder}")                                    

                                    property_files = os.listdir(os.path.join(properties_config_in_package, environment_folder))

                                    if any(property_files):                                        

                                        # Checking if properties are present or not 
                                        for property_file in property_files:                                            

                                            properties_name = ''.join(property_file.split('.')[:-1]).split('__')

                                            properties_files_content = self.__environment_provider.read_properties_file(os.path.join(properties_config_in_package, environment_folder, property_file))

                                            if len(properties_name) > 0:                                                                                            

                                                properties_present_data = self.props_lib.get_properties_from_files(package_location, properties_name, _excludes_extension, _excludes_replacements)
                                                
                                                for properties_present_content in properties_present_data:
                                                    # Check the missing Properties
                                                    if properties_present_content['property_keys']:
                                                        for properties_present_keys in properties_present_content['property_keys']:
                                                            if properties_present_keys not in properties_files_content:
                                                                _status = 1
                                                                self.log.error(f"Environment: {environment_folder}")
                                                                self.log.error(f"Property File: {property_file}")                                                                
                                                                self.log.error(properties_present_content['property_filename'])
                                                                self.log.error(f"{properties_present_keys} missing in Properties File {property_file}")
                                                                self.log.debug("------------------------------------------------------------------------")
                                        if _status == 0:                                   
                                            self.log.info(Constants.colorize(f"{package_name[0]} - Package Verified - {environment_folder}",Constants.TEXT_GREEN))
                                        if _status == 1:
                                            self.log.error(Constants.colorize(f"{package_name[0]} - Package Failed - {environment_folder}", Constants.TEXT_RED))
                            self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[2]}', 'label': f"{package_name[2]} Package Created"})
                                                         

                except Exception as e:
                    self.log.error(e)
            
            return self._processes

    def create(self):
        
        if 'executeTargets' in self.__properties[self.__target]:

            self._executeCombineTargets()

        else:
        
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
            
            for index, server_info in enumerate(_execute_servers):

                try:
                    if self.tc_build_config.get_workspace() and self.tc_build_config.get_branch() and self.tc_build_config.get_package_name() and self.tc_build_config.get_tc_version() and self.tc_build_config.get_software_version() and self.tc_build_config.get_artifacts_creation():
                        

                        # Check the Repo Path and Found the Git Changes
                        DELTA_CHECKOUT_PATH = server_info['DELTA_CHECKOUT_PATH'].replace('$BRANCH', self.tc_build_config.get_branch())
                        commit_logs, delta_changes = self.tc_lib.get_repo_changes(DELTA_CHECKOUT_PATH) # commit logs and file changes

                        self.log.debug(commit_logs)


                        if self.tc_build_config.get_artifacts_creation().lower() == 'true':
                            
                            __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
                            __is_linux = self.__environment_provider.is_linux(server_info['OS_TYPE'])

                            if __is_windows:  
                                
                                                            

                                if self.tc_build_config.get_delta_build().lower() == 'false': 

                                    # Windows Build Package Creation
                                    self._create_bmide_package(server_info)
                                    self._create_itk_package(server_info)
                                    self._create_dlls_package(server_info)                                    

                                    build_packages = ['BMIDE.build.win','ITK.build.win','BMIDE.dlls']

                                    build_package_transferred_list = []

                                    for build_package in build_packages:

                                        location_in_package = self.__properties[build_package]['location_in_package']

                                        build_package_transferred_list.append(location_in_package)                                
                                    
                                    # non build package creation
                                    packages_lists = self.__properties[self.__target]['packages'] 

                                    for package_name in packages_lists: 

                                        package_name = package_name.split(':')

                                        full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())

                                        build_out_location = os.path.join(self.tc_build_config.get_workspace(), package_name[0]).replace('/', '\\')

                                        destination_path = os.path.join(server_info['TARGET_BASE_LOCATION'], self.tc_build_config.get_branch(), package_name[2], full_package_name).replace('/', '\\')


                                        _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider)

                                        if _system_executor.check_file_exists(build_out_location) == 0:
                                            
                                            build_package_transferred_folder_names = [os.path.basename(os.path.normpath(path)) for path in build_package_transferred_list]

                                            excludes = ' '.join(build_package_transferred_folder_names)

                                            command = f"robocopy {build_out_location} {destination_path} /XF .gitignore *.log README.md delete_me_when_putting_files_here.txt /XD .git {excludes} /E /NJH /NJS  1>{self.tc_build_config.get_workspace()}\{package_name[0]}\{full_package_name}_creation.log"
                            
                                            copy_exit_code, copy_output, copy_error = _system_executor.execute(command, custom_exception=PackageException)


                                else:                                    

                                    build_packages = ['BMIDE.build.win','ITK.build.win','BMIDE.dlls']

                                    build_package_transferred_list = []

                                    for build_package in build_packages:

                                        location_in_package = self.__properties[build_package]['location_in_package']

                                        build_package_transferred_list.append(location_in_package)

                                    # non build package creation
                                    packages_lists = self.__properties[self.__target]['packages'] 

                                    # check the git changes present in the package
                                    #delta_found = any(location_in_package in line for line in delta_changes)

                                    # Windows Build Package Creation
                                    self._create_bmide_package(server_info)
                                    self._create_itk_package(server_info)
                                    self._create_dlls_package(server_info) 

                                    for package_name in packages_lists: 

                                        package_name = package_name.split(':')

                                        full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())

                                        build_out_location = os.path.join(self.tc_build_config.get_workspace(), package_name[0]).replace('/', '\\')

                                        destination_path = os.path.join(server_info['TARGET_BASE_LOCATION'], self.tc_build_config.get_branch(), package_name[2], full_package_name).replace('/', '\\')

                                        _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider)

                                        if _system_executor.check_file_exists(build_out_location) == 0:

                                            build_package_transferred_folder_names = [os.path.basename(os.path.normpath(path)) for path in build_package_transferred_list]

                                            excludes = ' '.join(build_package_transferred_folder_names)                                           

                                            delta_changes_filtered_by_package_name_lists = [item for item in delta_changes if item.startswith(package_name[0])]

                                            for build_package_transferred_folder_name in build_package_transferred_folder_names:

                                                    delta_changes_filtered_by_package_name_lists = [item for item in delta_changes_filtered_by_package_name_lists if build_package_transferred_folder_name not in item]


                                            self.log.info(f"excludes : {excludes}")

                                            self.log.info(f"includes: {delta_changes_filtered_by_package_name_lists}")
                                            
                                            if len(delta_changes_filtered_by_package_name_lists) > 0:

                                                additional_folders = self.__properties[self.__target]['additional_folders']                                 
                                                

                                                self.log.info('Delta Changes Found..') 

                                                for additional_folder in additional_folders:
                                                    if _system_executor.check_file_exists(os.path.join(build_out_location,additional_folder)) == 0:
                                                        # Copy Properties Files                                            
                                                        command = f"robocopy {os.path.join(build_out_location,additional_folder)} {os.path.join(destination_path, additional_folder)} /E"
                                                        self.log.info(f"Additional Folders: {command}")
                                                        copy_exit_code, copy_output, copy_error = _system_executor.execute(command, custom_exception=PackageException)
                                                        self._processes.append({'NODE':server_info['NODE'], 'process': copy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[2]}', 'label': f"{package_name[2]} Package Created"})
                                                                                                
                                                
                                                self.log.info(delta_changes_filtered_by_package_name_lists)
                                                
                                                for delta_changes_filtered_by_package_name_list in delta_changes_filtered_by_package_name_lists:

                                                    source_file_path = os.path.join(self.tc_build_config.get_workspace(),delta_changes_filtered_by_package_name_list).replace('/', '\\')

                                                    destination_file = delta_changes_filtered_by_package_name_list[len(package_name[0]+'/'):] if delta_changes_filtered_by_package_name_list.startswith(package_name[0]+'/') else delta_changes_filtered_by_package_name_list

                                                    destination_file_path = os.path.join(destination_path, destination_file).replace('/', '\\')

                                                    command = f"echo F|xcopy /S /Q /Y /F {source_file_path} {destination_file_path}"
                                                    self.log.debug(f"{command}")
                                                    copy_exit_code, copy_output, copy_error = _system_executor.execute(command, custom_exception=PackageException) 
                                                    self._processes.append({'NODE':server_info['NODE'], 'process': copy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[2]}', 'label': f"{package_name[2]} Package Created"})
                                            else:
                                                 self.log.info(f"There is no changes on this non build {package_name[2]} Package")

                            if __is_linux:
                                # Lnx Build Package Creation
                                self._create_bmide_so_package(server_info)
                                self._create_itk_so_package(server_info)                     

                                 
                except Exception as e:
                    self.log.error(e)
            
            return self._processes


    def _create_itk_so_package(self, server_info, delta_changes=[], delta=False):
        try:
            __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            __is_linux = self.__environment_provider.is_linux(server_info['OS_TYPE'])

            if __is_linux:

                build_config = self.__properties['ITK.build.lnx']

                for package_name in build_config['packages']:

                    package_name = package_name.split(':') 

                    full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())                                                      

                    location_out_package = build_config['location_out_package']

                    build_out_location = os.path.join(self.tc_build_config.get_workspace(), package_name[0], build_config['location_out_package']) 

                    self.log.info(f"Full Package location: {full_package_name}")

                    self.log.info(f"BUILD_OUTPUT_LOCATION: {build_out_location}")

                    destination_path = os.path.join(server_info['TARGET_BASE_LOCATION'], self.tc_build_config.get_branch(), package_name[2], full_package_name, build_config['location_out_package'])

                    self.log.info(f"BUILD_ARTIFACTS_LOCATION: {destination_path}")

                    _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider)

                    if not os.path.exists(destination_path):
                        os.makedirs(destination_path)

                    if os.path.exists(build_out_location):

                        copy_exit_code = _system_executor.copy_files(build_out_location + '/*', destination_path)
                        self._processes.append({'NODE':server_info['NODE'], 'process': copy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"ITK SO {package_name[2]} Package Created"})
                        self.__console_msg( copy_exit_code, f"ITK SO {package_name[2]} Package Created")  
                    else:
                        self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"ITK SO {package_name[2]} Package Skipped"})
                        self.log.warning( f"ITK SO {package_name[2]} Package Skipped")                      

        except PackageException as e:
            self.log.error(e)

        

    def _create_bmide_so_package(self, server_info, delta_changes=[], delta=False):
        try:
            __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            __is_linux = self.__environment_provider.is_linux(server_info['OS_TYPE'])

            if __is_linux:

                build_config = self.__properties['BMIDE.so']

                for package_name in build_config['packages']:

                    package_name = package_name.split(':') 

                    full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())                                                      

                    location_out_package = build_config['location_out_package']

                    build_out_location = os.path.join(self.tc_build_config.get_workspace(), package_name[0], build_config['location_out_package'])

                    self.log.info(f"Full Package location: {full_package_name}")

                    self.log.info(f"BUILD_OUTPUT_LOCATION: {build_out_location}")

                    destination_path = os.path.join(server_info['TARGET_BASE_LOCATION'], self.tc_build_config.get_branch(), package_name[2], full_package_name, build_config['location_out_package'])

                    self.log.info(f"BUILD_ARTIFACTS_LOCATION: {destination_path}")

                    _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider)

                    if not os.path.exists(destination_path):
                        os.makedirs(destination_path)

                    if os.path.exists(build_out_location):
                        copy_exit_code = _system_executor.copy_files(build_out_location+ '/*', destination_path)
                        self._processes.append({'NODE':server_info['NODE'], 'process': copy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE SO {package_name[2]} Package Created"})
                        self.__console_msg( copy_exit_code, f"BMIDE SO {package_name[2]} Package Created")
                    else:
                        self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE SO {package_name[2]} Package Skipped"})
                        self.log.warning( f"BMIDE SO {package_name[2]} Package Skipped")   

        except PackageException as e:
            self.log.error(e)
        
    def _create_dlls_package(self, server_info, delta_changes=[], delta=False):
        try:
            __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            if __is_windows:

                build_config = self.__properties['BMIDE.dlls']

                for package_name in build_config['packages']:

                    package_name = package_name.split(':') 

                    full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())                                                      

                    location_out_package = build_config['location_out_package']

                    build_out_location = os.path.join(self.tc_build_config.get_workspace(), package_name[0], build_config['location_out_package']).replace('/', '\\')

                    self.log.info(f"Full Package location: {full_package_name}")

                    self.log.info(f"BUILD_OUTPUT_LOCATION: {build_out_location}")

                    destination_path = os.path.join(server_info['TARGET_BASE_LOCATION'], self.tc_build_config.get_branch(), package_name[2], full_package_name, build_config['location_out_package']).replace('/', '\\')

                    self.log.info(f"BUILD_ARTIFACTS_LOCATION: {destination_path}")

                    _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider)

                    if _system_executor.check_file_exists(build_out_location) == 0:

                        command = f"robocopy {build_out_location} {destination_path} /XF .gitignore *.log README.md delete_me_when_putting_files_here.txt /XD .git {package_name[1]} /E /NJH /NJS  1>{self.tc_build_config.get_workspace()}\{package_name[0]}\{full_package_name}_creation.log"
        
                        copy_exit_code, copy_output, copy_error = _system_executor.execute(command, custom_exception=PackageException)

                        self._processes.append({'NODE':server_info['NODE'], 'process': copy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"DLLs {package_name[2]} Package Created"})
                        self.__console_msg( copy_exit_code, f"DLLs {package_name[2]} Package Created") 
                    else:
                        self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"DLLs {package_name[2]} Package Created"})
                        self.log.warning(f"DLLs {package_name[2]} Package Skipped") 


        except PackageException as e:
            self.log.error(e)

    def _create_itk_package(self, server_info, delta_changes=[], delta=False):
        try:
            __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            if __is_windows:

                build_config = self.__properties['ITK.build.win']

                for package_name in build_config['packages']:

                    package_name = package_name.split(':')

                    full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())                                                      

                    location_out_package = build_config['location_out_package']

                    build_out_location = os.path.join(self.tc_build_config.get_workspace(), package_name[0], build_config['location_out_package']).replace('/', '\\')

                    self.log.info(f"Full Package location: {full_package_name}")

                    self.log.info(f"BUILD_OUTPUT_LOCATION: {build_out_location}")

                    destination_path = os.path.join(server_info['TARGET_BASE_LOCATION'], self.tc_build_config.get_branch(), package_name[2], full_package_name, build_config['location_out_package']).replace('/', '\\')

                    self.log.info(f"BUILD_ARTIFACTS_LOCATION: {destination_path}")

                    _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider)

                    if _system_executor.check_file_exists(build_out_location) == 0:

                        command = f"robocopy {build_out_location} {destination_path} /XF .gitignore *.log README.md delete_me_when_putting_files_here.txt /XD .git {package_name[1]} /E /NJH /NJS  1>{self.tc_build_config.get_workspace()}\{package_name[0]}\{full_package_name}_creation.log"
        
                        copy_exit_code, copy_output, copy_error = _system_executor.execute(command, custom_exception=PackageException)

                        self._processes.append({'NODE':server_info['NODE'], 'process': copy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"ITK {package_name[2]} Package Created"})
                        self.__console_msg( copy_exit_code, f"ITK {package_name[2]} Package Created")
                    else:
                        self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"ITK {package_name[2]} Package Created"})
                        self.log.warning(f"ITK {package_name[2]} Package Skipped")


        except PackageException as e:
            self.log.error(e)


    def _create_bmide_package(self, server_info, delta_changes=[], delta=False):

        try:
            __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            if __is_windows:
                # Transfer the BMIDE Out Package 
                build_config = self.__properties['BMIDE.build.win']
                for package_name in build_config['packages']:

                    package_name = package_name.split(':') 

                    full_package_name = self.__environment_provider.get_build_package_name(self.tc_build_config.get_software_version(), package_name[2], self.tc_build_config.get_branch(), self.tc_build_config.get_package_name())

                    bmide_out_package_pattern = build_config['bmide_out_package_pattern']

                    BMIDE_BUILD_VERSION = build_config['bmide_build_version']

                    bmide_out_package = self.tc_build_config.get_bmide_out_folder_name(bmide_out_package_pattern, package_name[1], self.tc_build_config.get_software_version(), BMIDE_BUILD_VERSION, self.tc_build_config.get_tc_version())

                    self.log.info(f"Build Package Folder Name: {bmide_out_package}")

                    bmide_out_location = os.path.join(self.tc_build_config.get_workspace(), package_name[0], build_config['location_in_package'], bmide_out_package).replace('/', '\\')

                    self.log.info(f"Full Package location: {full_package_name}")

                    self.log.info(f"BUILD_OUTPUT_LOCATION: {bmide_out_location}")

                    destination_path = os.path.join(server_info['TARGET_BASE_LOCATION'], self.tc_build_config.get_branch(), package_name[2], full_package_name, build_config['location_in_package'], bmide_out_package).replace('/', '\\')

                    self.log.info(f"BUILD_ARTIFACTS_LOCATION: {destination_path}")

                    _system_executor = SystemExecutor(self.__arguments, server_info, self.__environment_provider)

                    if _system_executor.check_file_exists(bmide_out_location) == 0:

                        command = f"robocopy {bmide_out_location} {destination_path} /XF .gitignore *.log README.md delete_me_when_putting_files_here.txt /XD .git {package_name[1]} /E /NJH /NJS  1>{self.tc_build_config.get_workspace()}\{package_name[0]}\{full_package_name}_creation.log"
    
                        copy_exit_code, copy_output, copy_error = _system_executor.execute(command, custom_exception=PackageException)

                        self._processes.append({'NODE':server_info['NODE'], 'process': copy_exit_code, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE {package_name[2]} Package Created"})
                        self.__console_msg( copy_exit_code, f"BMIDE {package_name[2]} Package Created") 
                    else:
                        self._processes.append({'NODE':server_info['NODE'], 'process': 0, 'module': self.__module_label, 'package_id': f'{package_name[1]}', 'label': f"BMIDE {package_name[2]} Package Created"})
                        self.log.warning(f"BMIDE {package_name[2]} Package Skipped") 


        except Exception as e:
            self.log.error(e) 



        
    def _executeCombineTargets(self):
        try:
            for thread_count, targets in enumerate(self.__environment_provider.get_execute_targets(self.__target).split(',')):
                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name

                if dynamicExecutor.get_sub_module_name():  
                    _processesResult = getattr(BuildPackage, dynamicExecutor.get_sub_module_name())(self)
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