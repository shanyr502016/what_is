"""
AWC Start and Stop Service
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.Services import WinService
from sbautomation.lib.StartStopUtilities import StartStopUtilities
from corelib.SCP import SCP
import os
import re

class AWC(Loggable):
    """
    AWC Start / Stop Services (Windows Service and Linux Service)
    """

    def __init__(self, args):   

        super().__init__(__name__)

        self.__environment = args._environment # Get the Environment Specific Values from config json
        
        self.__arguments = args

        self.__properties = args._properties # Get the Module Specific Values from config json

        self.__action = args._arguments.action # Action from user command line (Status, Start, Stop)

        self.__module = args._arguments.module # Module name with submodule from user command line (full name)
        self.__module_label = self.__module # Module label

        self.__environment_provider = args._environment_provider  # Get the Environment Provider method. Reusable method derived

        self.__module_name = args._module_name # Module name from user command line (Only Module (classname))


        self.__sub_module_name = args._sub_module_name # Sub Module name from user command line (Only Sub Module (classname))        

        self.__instances = args._instances # Get Instances from config json, based on that the module will execute
        

        self.__operation = None # Operation of command like (start, status, stop)
        

        self.__print_services = args._print_services # Print Services information when triggered the dita command without module
        

        self.__results = [] # Print Services Results are stored into results


        self.__remote_execution = False  # Remote Execution.
        

        self.__is_linux = False # Target Environment Type if linux
        

        self.__is_windows = False # Target Environment Type if windows


        self.__command = None # Execution Command
        
        
    def default(self):
        """
        Default method runs when get the print services
        """
        self.__results = []
        self.__action = 'Status'
        self.Status()    
        return self.__results  
    
    def Status(self):
        """
        Get the Service Status
        """        
        self.__operation = "status"
        return self._build_arguments() 
        
    def Start(self):  
        """
        Start the Service
        """      
        self.__operation = "start"                
        return self._build_arguments()
        
    def Stop(self):   
        """
        Stop the Service
        """     
        self.__operation = "stop"       
        return self._build_arguments() 
        
    def Restart(self):
        """
        Restart the Service
        """
        self.__operation = "restart"
        return self._build_arguments()  
        
        
    def _build_arguments(self):
        """
        Build the arguments based on the configuration and executing with environment based instances
        """  
        execute_servers = []
        if 'server' in self.__arguments._arguments:
            # Filtering the server specific filter        
            execute_servers = list(filter(lambda x: x['NODE'] == getattr(self.__arguments._arguments, 'server'), self.__instances))            
        else:            
            execute_servers = self.__instances
        for inscount, instance in enumerate(execute_servers):
                        
            _execute_servers = self.__environment_provider.get_execute_server_details(instance['NODE'])               
            _instance_count = len(_execute_servers)
            
            
            # LOCATION and Command
            _location = instance['LOCATION']
            self.__command = instance['COMMAND']
            
            if _instance_count > 0:
                
                for nodecount, nodes in enumerate(_execute_servers):          
                    
                    # Preparing SSH command
                    __ssh_command = self.__environment_provider.get_ssh_command(nodes) 

                    self.__is_linux = self.__environment_provider.is_linux(nodes['OS_TYPE'])
                    self.__is_windows = self.__environment_provider.is_windows(nodes['OS_TYPE']) 

                    _retry = 1  

                    
                    if __ssh_command == '':
                        self.__remote_execution = False  
                    else:
                        self.__remote_execution = True

                    if "MAX_RETRIES" in instance:
                        _retry = instance['MAX_RETRIES']

                    if self.__operation == 'status':
                        _retry = 1
                    for retry_count in range(_retry):
                        working_dir = []
                        command = []
                        if retry_count >0:
                            self.log.info(f"#{retry_count} Reattempting to {self.__operation} the service")

                        # Preparing the execution command
                        command = []

                        command.append(self.__command)
                        
                        # Preparing the remote connection with working directory
                        working_dir = []                  
                            
                        # set execution location
                        if _location:
                            working_dir.append(_location)

                        self.__module_label = self.__module
                        if self.__is_windows:
                            self.__module_label =  self.__command

                        # Execution command
                        if self.__print_services:
                            # Get Service Status with returns print services informations   
    
                            result = self._execute(command, working_dir, __ssh_command)
                            self.__results.append({
                                'pid': result,
                                'hostname': nodes['HOSTNAME'],
                                'os_type': nodes['OS_TYPE'],
                                'node': instance['NODE'],
                                'module': self.__module_label,
                                'command': self.__module,
                                'aliasname': nodes['ALIASNAME']
                            })
                        else:
                            self.log.info(f"Requesting the {self.__module_label} {self.__action} from {instance['NODE']} [{nodes['HOSTNAME']}]")
                            result=self._execute(command, working_dir, __ssh_command)
                        
                        # Checking the service result to move reattempting
                        if self.__operation == 'start':
                            if result != 0 and result != None and result != False:
                                break
                        elif self.__operation == 'stop':
                            if result == 0 or not result:
                                clear_temp_result = self._clear_temp(nodes, instance)
                                if clear_temp_result == 0:
                                    Loggable.log_success(self, f"Temp Directory Deleted Successfully.")
                                else:
                                    self.log.warning(f'Temp Directory Deletion Failed.')
                                break
            else:
                self.log.info(f"{instance['NODE']} are not avaliable") 
        return self.__results
                
    def _execute(self, command, path, ssh_command):
        """ 
        Used to process services/command
        """
        command = ' '.join([str(elem) for elem in command])
        
        path = ' '.join([str(elem) for elem in path])        
        
        # If target server is Linux  
        if self.__is_linux:
            process = Process(command, path, ssh_command)
            process.set_action(self.__action)
            self._startstopUtilities = StartStopUtilities(process, self.__action, self.__module_label, self.__is_windows, self.__print_services)
            return self._startstopUtilities._execute_msg()
        # If target server is windows         
        if self.__is_windows:
            process = WinService(command, path, ssh_command)
            self._startstopUtilities = StartStopUtilities(process, self.__action, self.__module_label, self.__is_windows, self.__print_services)
            return self._startstopUtilities._execute_msg()  

    def _clear_temp(self, nodes, instance):
        try:
            result = 0
            _paths_to_delete = []

            _temp_paths = instance.get('TEMP_PATHS', [])
            _temp_paths_with_pattern = instance.get('TEMP_PATHS_WITH_PATTERN', [])
            _match_delete_patterns = instance.get('CLEAR_TEMP_KEYWORD', '').split(',')

            _scp_with_ssh =SCP(self.__environment_provider.get_ssh_command(nodes))

            if self.__is_windows:
                _temp_dir= nodes['DEPLOYMENT_CENTER_TEMP_DIR']
            else:
                _temp_dir ='/tmp'

            # get temp paths and files to clear
            for _temp_path in _temp_paths:
                _temp_path = _temp_path.replace('$USERNAME', nodes['USERNAME'])
                if os.path.basename(os.path.normpath(_temp_path)) == '*':
                    _temp_path = os.path.dirname(_temp_path)

                if '*' in _temp_path:
                    _filter_pattern = os.path.basename(os.path.normpath(_temp_path))
                    _file_path = os.path.dirname(_temp_path)
                    if _scp_with_ssh.check_dir_to_remote(self.__is_windows, _file_path):
                        _list_of_files = _scp_with_ssh.get_filtered_files_from_remote(_file_path, self.__is_windows, _temp_dir, filter=_filter_pattern)
                        for _file in _list_of_files:
                            _paths_to_delete.append(os.path.join(_file_path, _file))
                    else:
                        self.log.warning(f"{_file_path} Does not Exists...")
                else:
                    if _scp_with_ssh.check_dir_to_remote(self.__is_windows, _temp_path):
                        _paths_to_delete.append(_temp_path)
                    else:
                        self.log.warning(f"{_temp_path} Does not Exists...")

            def _check_pattern_match(_content):
                for _pattern in _match_delete_patterns:
                    if re.search(_pattern, _content):
                        return True
                return False

            # get temp files to clear if machted with given patterns
            for _temp_path in _temp_paths_with_pattern:
                if len(_match_delete_patterns) == 1 and _match_delete_patterns[0] == '':
                    self.log.warning(f'"CLEAR_TEMP_KEYWORD" is missing, clear temporary files skipped for "TEMP_PATHS_WITH_PATTERN"')
                    break

                _temp_path = _temp_path.replace('$USERNAME', nodes['USERNAME'])
                if os.path.basename(os.path.normpath(_temp_path)) == '*':
                    _temp_path = os.path.dirname(_temp_path)

                if '*' in _temp_path:
                    _filter_pattern = os.path.basename(os.path.normpath(_temp_path))
                    _file_path = os.path.dirname(_temp_path)
                    if _scp_with_ssh.check_dir_to_remote(self.__is_windows, _file_path):
                        if not _scp_with_ssh.check_empty_dir_from_remote(self.__is_windows, _file_path, _temp_dir, recurse=False, check_files_only=True):
                            _list_of_files = _scp_with_ssh.get_filtered_files_from_remote(_file_path, self.__is_windows, _temp_dir, filter=_filter_pattern)
                            for _file in _list_of_files:
                                _content = _scp_with_ssh.read_file_from_remote(os.path.join(_file_path, _file), self.__is_windows)
                                if _check_pattern_match(_content):
                                    _paths_to_delete.append(os.path.join(_file_path, _file))
                    else:
                        self.log.warning(f"{_file_path} Does not Exists...")
                else:
                    if _scp_with_ssh.check_dir_to_remote(self.__is_windows, _temp_path):
                        if not _scp_with_ssh.check_empty_dir_from_remote(self.__is_windows, _temp_path, _temp_dir, recurse=False, check_files_only=True):
                            _list_of_files = _scp_with_ssh.get_files_from_remote(_temp_path, self.__is_windows, files_only=True)
                            for _file in _list_of_files:
                                _content = _scp_with_ssh.read_file_from_remote(os.path.join(_temp_path, _file), self.__is_windows)
                                if _check_pattern_match(_content):
                                    _paths_to_delete.append(os.path.join(_temp_path, _file))
                    else:
                        self.log.warning(f"{_temp_path} Does not Exists...")

            _paths_to_delete = list(set(_paths_to_delete))
            if len(_paths_to_delete):
                for path in _paths_to_delete:
                    _scp_with_ssh.chmod_remote(path, self.__is_windows)
                result = _scp_with_ssh.remove_multiple_files_to_remote(self.__is_windows, _paths_to_delete, _temp_dir)
            else:
                self.log.info('No Temporary files/directories to clean.')

        except Exception as exp:
            self.log.error(f'Execution Failed - {exp}')
            result = 1
        return result
