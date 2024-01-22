"""
PUBLISHER Start and Stop Service
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.Services import WinService
from sbautomation.lib.StartStopUtilities import StartStopUtilities
import os
from corelib.SCP import SCP

class PUBLISHER(Loggable):

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

        """
        Execution Command
        """
        self.__command = None

        self._location = None
        
        
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
        self.__operation = "restart"
        
        return self._build_arguments()   
        
        
    def _build_arguments(self):
        """
        Build the arguments based on the configuration and executing with environment based instances
        """          
        for inscount, instance in enumerate(self.__instances):
                        
            _execute_servers = self.__environment_provider.get_execute_server_details(instance['NODE'])               
            _instance_count = len(_execute_servers)
            
            
            # LOCATION and Command
             
            self._location = instance['LOCATION']
            self.__command = instance['COMMAND']
            if 'SERVICE_LOCATION' in instance:
                self._service_location = instance['SERVICE_LOCATION']
                     
            
            if _instance_count > 0:
                
                for nodecount, nodes in enumerate(_execute_servers):          
                    
                    # Preparing SSH command
                    __ssh_command = self.__environment_provider.get_ssh_command(nodes)
                    
                    self.__is_linux = self.__environment_provider.is_linux(nodes['OS_TYPE'])
                    self.__is_windows = self.__environment_provider.is_windows(nodes['OS_TYPE'])
                    _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(nodes, True))
                    _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(nodes))                   
                    
                    _retry = 1

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
                   
                        # Preparing the execution command
                        command = []

                        command.append(self.__command)
                    
                        # Preparing the remote connection with working directory
                        working_dir = []
                        
                        # set execution location
                        if self._location:
                            working_dir.append(self._location)

                        if self.__is_linux:
                            self.__module_label = instance['SERVICE_NAME']
                            command.append(self.__operation)
                        if self.__is_windows:                            
                            self.__module_label =  self.__command.replace('_',' ')

                        #Execution command
                        if self.__print_services:
                            # Get Service Status with returns print services informations   
                            result = self._execute(command, working_dir, __ssh_command,instance)
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
                            result = self._execute(command, working_dir, __ssh_command,instance)
                            
                        if self.__is_windows and self.__operation == 'stop' and 'SERVICE_LOCATION' in instance:

                            if not _scp_with_ssh.check_dir_to_remote(self.__is_windows,nodes['DEPLOYMENT_CENTER_TEMP_DIR']):
                                _scp_with_ssh.create_dir_to_remote(self.__is_windows,nodes['DEPLOYMENT_CENTER_TEMP_DIR'])

                            handleExecutableFilePath  = os.path.join(os.path.realpath(os.path.dirname(__file__)), os.pardir,'tools', 'handle.exe')
                            handlerResult = _scp_without_ssh.copy_to_remote(handleExecutableFilePath, nodes['DEPLOYMENT_CENTER_TEMP_DIR'])
                            
                            if handlerResult == 0:
                                _dc_services = [self.__command, 'java']                        
                                for dc_service in _dc_services:
                                    self._service_location = self._service_location.replace('/', '\\')
                                    depends_command = [] 
                                    if dc_service == 'java':
                                        depends_command.append(os.path.join('"' + nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + self._service_location + '"'))
                                        self.depends_service(depends_command, working_dir, __ssh_command, dc_service)
                                    else:
                                        depends_command.append(os.path.join('"' + nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + dc_service + '"'))
                                        self.depends_service(depends_command, working_dir, __ssh_command, dc_service)
                            else:
                                self.log.error(f'Unable to copy handle.exe file to {nodes["NODE"]}')
                       
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
        
        path = ' '.join([str(elem) for elem in path])

        services = WinService(command, path, ssh_command)
        # If target server is Linux  
        if self.__is_linux:
            process = Process(command, path, ssh_command)
            process.set_servicename('dc')
            process.set_command_regex(self._location)
           
            process.set_action(self.__action)
    
            self._startstopUtilities = StartStopUtilities(process, self.__action, self.__module_label, self.__is_windows, self.__print_services)
            return self._startstopUtilities._execute_msg()
        # If target server is windows         
        if self.__is_windows:
            
            process = WinService(command, path, ssh_command)
            self._startstopUtilities = StartStopUtilities(process, self.__action, self.__module_label, self.__is_windows, self.__print_services)
            return self._startstopUtilities._execute_msg()



    def depends_service(self, command, path, ssh_command, dc_service):
        """
        Used to get the process id and stop the service if action is Stop
        """        
        command = ' '.join([str(elem) for elem in command])
        path = ':'.join([str(elem) for elem in path])
        process = WinService(command, path, ssh_command)
        process.setQuery('handle')
        process.setServiceName(dc_service+'.exe')
        processID = process.get_process_id()
        if self.__operation == 'stop':
            self.log.debug(f"Dependency Java Services request to Stop PID: {processID}")
            if processID:                
                return process.stop()
        return processID
