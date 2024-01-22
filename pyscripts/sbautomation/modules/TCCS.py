"""
TCCS Start and Stop Service
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.Services import WinService
from sbautomation.lib.StartStopUtilities import StartStopUtilities
from corelib.Constants import Constants
import os
from corelib.SCP import SCP

class TCCS(Loggable):

    def __init__(self, args):       

        super().__init__(__name__)

        """
        Get the Environment Specific Values from config json
        """
        self.__environment = args._environment
        
        """
        Get the Module Specific Values from config json
        """
        self.__properties = args._properties
        
        """
        Action from user commandline (Status, Start, Stop)
        """
        self.__action = args._arguments.action
        
        """
        Module name with submodule from user commandline (full name)
        """
        self.__module = args._arguments.module
        self.__module_label = self.__module
        
        """
        Get the Environment Provider method
        Reusable method derived
        """
        self.__environment_provider = args._environment_provider 

        """
        Module name from user commandline (Only Module (classname))
        """
        self.__module_name = args._module_name
        """
        Sub Module name from user commandline (Only Sub Module (classname))
        """
        self.__sub_module_name = args._sub_module_name
        
        
        """
        Get Instances from config json, based on that the module will execute
        """
        self.__instances = args._instances
        
        """
        Operation of command like (start, status, stop)
        """
        self.__operation = None
        
        """
        Print Services information when triggered the dita command without module
        """
        self.__print_services = args._print_services
        
        """
        Print Services Results are stored into results
        """
        self.__results = []
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

        self.__checkindexing = True

        """
        Execution Command
        """
        self.__command = None

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
        self.__operation = 'status'      
        
        return self._build_arguments() 
    
    def Start(self):
        """
        Start the Service
        """
        self.__operation = 'start'       

        return self._build_arguments()
    
    def Stop(self):
        """
        Stop the Service
        """
        self.__operation = 'stop'

        return self._build_arguments()

    def _build_arguments(self):
        """
        Build the arguments based on the configuration and executing with environment based instances
        """         
        for inscount, instance in enumerate(self.__instances):           

            _execute_servers = self.__environment_provider.get_execute_server_details(instance['NODE'])  
            _instance_count = len(_execute_servers)
            
            _tccs_location = None
            _service_name = None
            if 'LOCATION' in instance:
                _tccs_location = instance['LOCATION']  

            if 'SERVICE_NAME' in instance:
                _service_name = instance['SERVICE_NAME']         
                
            
            if _instance_count > 0:

                for nodecount, nodes in enumerate(_execute_servers):                          
                    
                    # Preparing SSH command
                    __ssh_command = self.__environment_provider.get_ssh_command(nodes)
                    
                    self.__is_windows = self.__environment_provider.is_windows(nodes['OS_TYPE'])   

                    _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(nodes, True))
                
                    _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(nodes))       
                    
                    _retry=1
                    
                    if __ssh_command == '':
                        self.__remote_execution = False  
                    else:
                        self.__remote_execution = True 

                    if "MAX_RETRIES" in instance:
                        _retry = instance['MAX_RETRIES']
                    
                    if self.__operation == 'status':
                        _retry=1

                    for retry_count in range(_retry):
                        if retry_count >0:
                            self.log.info(f"#{retry_count} Reattempting to {self.__operation} the service")

                        command = []
                        # Preparing the remote connection with working directory
                        working_dir = []

                        if self.__is_windows:
                            
                            if not _scp_with_ssh.check_dir_to_remote(self.__is_windows,nodes['DEPLOYMENT_CENTER_TEMP_DIR']):
                                _scp_with_ssh.create_dir_to_remote(self.__is_windows,nodes['DEPLOYMENT_CENTER_TEMP_DIR'])

                            handleExecutableFilePath  = os.path.join(os.path.realpath(os.path.dirname(__file__)), os.pardir,'tools', 'handle.exe')
                            
                            # set execution location
                            working_dir.append('/')
                            if self.__operation == 'status' or self.__operation == 'stop' or self.__operation == 'start':
                                # Copy the Handle.exe file into Temp Location                    
                                # Get the tools path
                                #if self.__operation == 'stop':  
                                handlerResult = _scp_without_ssh.copy_to_remote(handleExecutableFilePath, nodes['DEPLOYMENT_CENTER_TEMP_DIR'])
                                if handlerResult == 0: 
                                    _tccs_location = _tccs_location.replace('/', '\\')
                                    command.append(os.path.join('"' + nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + _tccs_location + '"'))
                                else:
                                    self.log.error(f'Unable to copy handle.exe file to {nodes["NODE"]}')
                                        
                        # For Print Message
                        self.__module_label = self.__module
                        if self.__is_windows:
                            self.__module_label =  self.__module
                        _command_display_name = self.__module_label
                        if _service_name:
                            _command_display_name = _service_name
                        else:
                            _command_display_name = self.__module_label

                        if self.__print_services: 
                            # Get Service Status with returns print services informations 
                            result = self._execute(command, working_dir, __ssh_command, instance)
                            self.__results.append({
                                'pid': result,
                                'hostname': nodes['HOSTNAME'],
                                'os_type': nodes['OS_TYPE'],
                                'node': instance['NODE'],
                                'module': self.__module_label,
                                'command': _command_display_name,
                                'aliasname': nodes['ALIASNAME']
                            })
                        else:
                            self.log.info(f"Requesting the {_command_display_name} {self.__action} from {instance['NODE']} [{nodes['HOSTNAME']}]")
                            result = self._execute(command, working_dir, __ssh_command, instance)
                        
                        # Checking the service result to move reattempting
                        if self.__operation == 'start':
                            if result != 0 and result != None and result != False:
                                break
                        elif self.__operation == 'stop':
                            if result == 0 or not result:
                                break

            else:
                self.log.info(f"{instance['NODE']} are not avaliable") 
        return self.__results


    def _execute(self, command, path, ssh_command, instance):
        """ 
        Used to process services/command
        """
        command = ' '.join([str(elem) for elem in command])
        
        path = ':'.join([str(elem) for elem in path]) 
                   
        if self.__is_windows:
            process = WinService(command, path, ssh_command)
            process.setQuery('handle')
            process.setServiceName('java.exe')
            processID = process.get_process_id()
            if self.__operation == 'start':
                self.log.debug(f"{self.__module_label} Not Configured")
                return processID
            if self.__operation == 'status':
                if not self.__print_services:
                    if processID:     
                        self.log.info(Constants.colorize(f"{self.__module_label} is Running Successfully!. {f'PID: {processID}' if type(processID) is int else ''}",Constants.TEXT_GREEN))
                    else:
                        self.log.info(Constants.colorize(f"{self.__module_label} not running.",Constants.TEXT_RED))
                return processID
            if self.__operation == 'stop':
                if not self.__print_services:
                    self.log.debug(f"TCCS Services request to Stop PID: {processID}")
                if processID:                
                    return process.stop()
            return processID
        return 0
