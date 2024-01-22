"""
Project deployment activities
"""
import os

from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants
from corelib.SCP import SCP
import shutil

class Project(Loggable):
    
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
        """
        Scope and target setup based on configuration
        """   
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel
        
        
    def default(self):
                
        self.log.info("Project Import All")
        return self._executeTargets()           
   
    
    def Import(self):

        """
        Action: Import
        Command:  project_import -u= -g= -pf= import_mode= -transfermode= -xml_file=
        """
         
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
         
        for index, server_info in enumerate(_execute_servers):

            self.log.info(f'Project Import')

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                
                _replacement_foldername = 'deploy_'+self.__environment_provider.get_environment_name().lower()

                _replacement_path = self.__environment_provider.get_location_in_package(tc_package_id, _replacement_foldername)

                _loc_package = '/'.join(self.__properties[self.__target]['location_in_package'].split('/')[:2])

                _location_in_package_replacement = os.path.join(_replacement_path, _loc_package)

                self.log.info(_location_in_package_replacement)

                if os.path.exists(os.path.join(_location_in_package_replacement, 'create')):
                    shutil.rmtree(os.path.join(_location_in_package_replacement, 'create'), ignore_errors=True)
                                
                if not os.path.exists(os.path.join(_location_in_package_replacement, 'create')):
                    os.makedirs(os.path.join(_location_in_package_replacement, 'create'))       
                
                
                copy_package = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(_location_in_package, os.path.join(_replacement_path, _loc_package))
                
                if copy_package == 0:
                
                
                    if 'PROJECT_ADMIN' in server_info and server_info['PROJECT_ADMIN'].__ne__('') and 'PROJECT_PWF' in server_info and server_info['PROJECT_PWF'].__ne__('') and 'PROJECT_GROUP' in server_info and server_info['PROJECT_GROUP'].__ne__(''):
                        try:
                            if os.path.exists(os.path.join(_location_in_package_replacement, 'create')):
                                for file in os.listdir(os.path.join(_location_in_package_replacement, 'create')):
                                    if file.endswith('.txt'):
                                        self.log.info(f'Project Import Started..')
                                        command = self.__build_arguments(server_info, os.path.join(os.path.join(_location_in_package_replacement, 'create'),file))
                                        self.log.info(f"Project Command: {command}")
                                        result = self._execute(command)
                                        self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Project Import"})
                                        if not self._parallel:
                                            self.__console_msg(result, f"[{tc_package_id}] - Project Import")
                                    else:
                                        self.log.warning(f"Required File not Present from this location {tc_package_id}. Project Import Skipped")
                            else:
                                self.log.warning(f"Required Package Folder not Present from this location {tc_package_id}. Project Import Skipped")

                        except Exception as exp:
                            self.log.error(exp)
                            self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Project Import"})
                    else:
                        self.log.error('PROJECT_ADMIN,PROJECT_PWF,PROJECT_GROUP is required')
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Project Import"})
        return self._processes  


    def Update(self):

        WINDOWS_LINE_ENDING = b'\r\n'
        UNIX_LINE_ENDING = b'\n'

        """
        Action: Import
        Command:  project_import -u= -g= -pf= import_mode= -transfermode= -xml_file=
        """
         
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
         
        for index, server_info in enumerate(_execute_servers):

            self.log.info(f'Project Update')

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                
                _replacement_foldername = 'deploy_'+self.__environment_provider.get_environment_name().lower()
                
                _replacement_path = self.__environment_provider.get_location_in_package(tc_package_id, _replacement_foldername)
                
                _loc_package = '/'.join(self.__properties[self.__target]['location_in_package'].split('/')[:2])
                
                _location_in_package_replacement = os.path.join(_replacement_path, _loc_package)
                
                self.log.info(_location_in_package_replacement)
                
                if os.path.exists(os.path.join(_location_in_package_replacement, 'update')):
                    shutil.rmtree(os.path.join(_location_in_package_replacement, 'update'), ignore_errors=True)
                                
                if not os.path.exists(os.path.join(_location_in_package_replacement, 'update')):
                    os.makedirs(os.path.join(_location_in_package_replacement, 'update'))        
                
                
                copy_package = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(_location_in_package, os.path.join(_replacement_path, _loc_package))
                
                if copy_package == 0:
                    if 'PROJECT_ADMIN' in server_info and server_info['PROJECT_ADMIN'].__ne__('') and 'PROJECT_PWF' in server_info and server_info['PROJECT_PWF'].__ne__('') and 'PROJECT_GROUP' in server_info and server_info['PROJECT_GROUP'].__ne__(''):
                        try:
                            if os.path.exists(os.path.join(_location_in_package_replacement, 'update')):
                                for file in os.listdir(os.path.join(_location_in_package_replacement, 'update')):
                                    if file.endswith('.txt'):

                                        # Windows to Linux/Unix CRLF -> LF
                                        content = ""
                                        with open(os.path.join(os.path.join(_location_in_package_replacement, 'update'),file), 'rb') as open_file:
                                            content = open_file.read()

                                        # Windows -> Unix
                                        content = content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)

                                        with open(os.path.join(os.path.join(_location_in_package_replacement, 'update'),file), 'wb') as open_file:
                                            open_file.write(content)

                                        self.log.info(f'Project Update Started..')
                                        command = self.__build_arguments(server_info, os.path.join(os.path.join(_location_in_package_replacement, 'update'),file), True)
                                        self.log.info(f"Project Command: {command}")                                        
                                        result = self._execute(command)
                                        self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Project Update"})
                                        if not self._parallel:
                                            self.__console_msg(result, f"[{tc_package_id}] - Project Update")
                                    else:
                                        self.log.warning(f"Required File not Present from this location {tc_package_id}. Project Update Skipped")
                            else:
                                self.log.warning(f"Required Package Folder not Present from this location {tc_package_id}. Project Update Skipped")

                        except Exception as exp:
                            self.log.error(exp)
                            self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Project Update"})
                    else:
                        self.log.error('PROJECT_ADMIN,PROJECT_PWF,PROJECT_GROUP is required')
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Project Update"})
                else:
                    self.log.error('Project Update files copy failed')
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Project Update"})
        return self._processes  
                
    
    def __build_arguments(self, server_info, file, update=False):
        
        __ssh_command = self.__environment_provider.get_ssh_command(server_info)

        args = [__ssh_command]
            
        if self.__environment_provider.get_property_validation('command', self.__properties[self.__target]):
            args.append(self.__properties[self.__target]['command'])

        # Get Infodba Credentials
        args.extend(self.__environment_provider.get_project_credentials(server_info))

        # Get Group Name
        args.extend(self.__environment_provider.get_project_group(server_info))

        if update:
            args.append('-update')
        
        args.append('-input='+ file)

            
        return ' '.join([str(elem) for elem in args])  
                
        
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
                        _processesResult = getattr(Project, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()   
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult           
        except Exception as exp:
            self.log.error(exp)
        
           
    def _execute(self, command):

        """ Used to process services/command
        """
        process = Process(command)
        process.set_parallel_execution(self._parallel)
        return process.execute()


    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Imported Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Import Failed.")
        self.log.info('..............................................................')
