"""
Dispatcher Start and Stop Service
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.SCP import SCP
from corelib.File import Directory
import os
from corelib.Services import WinService
from sbautomation.lib.StartStopUtilities import StartStopUtilities

class Dispatcher(Loggable):
    

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

        self._directory = Directory()
        
        
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
    
    def _build_arguments(self):        
        """
        Build the arguments based on the configuration and executing with environment based instances
        """             
        for inscount, instance in enumerate(self.__instances):   

            _execute_servers = self.__environment_provider.get_execute_server_details(instance['NODE'])           
            _instance_count = len(_execute_servers) 

            # LOCATION , COMMAND and SERVICE NAME
            _location = instance['LOCATION']
            self.__command = instance['COMMAND'] 
            _service_name = instance['SERVICE_NAME']

            _service_type = None
            # If service type is Windows Service 
            if 'SERVICE_TYPE' in instance:
                _service_type = instance['SERVICE_TYPE']
            _command_regex = None
            if 'COMMAND_REGEX' in instance:
                _command_regex = instance['COMMAND_REGEX']
                
            
            node_temp_dir = None
            
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

                    # Preparing the remote connection with working directory                    
                    dispatcher_path = nodes['DISPATCHER_PATH']
                    
                    dispatcher_file_exe_path = os.path.join(_location,self.__command)

                    if "MAX_RETRIES" in instance:
                        _retry = instance['MAX_RETRIES']

                    if self.__operation == 'status':
                        _retry = 1
                    for retry_count in range(_retry):
                        working_dir = []
                        command = []
                        if retry_count >0:
                            self.log.info(f"#{retry_count} Reattempting to {self.__operation} the service")

                        # if target is windows
                        if self.__is_windows:

                            if _service_type == 'WINSERVICE':
                                command.append(self.__command)
                            elif _service_type == 'TASKSCHEDULER' or _service_type == None:
                                # Changing the Task Scheduler status
                                if self.__operation == 'stop':                                
                                    stop_command = []
                                    stop_command.append(_service_name)
                                    self.schtasks(stop_command, working_dir, __ssh_command, instance)
                                elif self.__operation == 'start':
                                    start_command = []
                                    start_command.append(_service_name)
                                    self.schtasks(start_command, working_dir, __ssh_command, instance)
                                # Copy the Handle.exe file into Temp Location                    
                                # Get the tools path
                                node_temp_dir = nodes['DEPLOYMENT_CENTER_TEMP_DIR']

                                if not _scp_with_ssh.check_dir_to_remote(self.__is_windows,node_temp_dir):
                                    _scp_with_ssh.create_dir_to_remote(self.__is_windows,node_temp_dir)

                                handleExecutableFilePath  = os.path.join(os.path.realpath(os.path.dirname(__file__)), os.pardir,'tools', 'handle.exe')
                                working_dir.append('/')

                                handlerResult = _scp_without_ssh.copy_to_remote(handleExecutableFilePath, node_temp_dir)
                                if handlerResult == 0:
                                    # using handle.exe to get the running services
                                    command.append(os.path.join('"' + nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + _location.replace('/', '\\') + '"')) 
                                else:
                                    self.log.error(f'Unable to copy handle.exe file to {nodes["NODE"]}')                            

                        if self.__is_linux:
                        
                            if self.__remote_execution and self.__is_linux:
                                command.append(__ssh_command)
                                command.append(f'"cd {_location} && {self.__command}"')
                                working_dir.append('/')
                            elif not self.__remote_execution and self.__is_linux:
                                command.append(f'nohup {_location}/{self.__command}')
                                working_dir.append(_location)
                                #command.append(os.path.join(_location, self.__command))
                                #working_dir.append(_location)
    
                        self.__module_label = _service_name
                        if self.__is_windows:
                            self.__module_label =  _service_name

                        # Execution command
                        if self.__print_services:
                            # Get Service Status with returns print services informations    
                            result = self._execute(command, working_dir, __ssh_command, _scp_without_ssh, node_temp_dir, dispatcher_file_exe_path, _service_name, _service_type, _command_regex)
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
                            
                            result = self._execute(command, working_dir, __ssh_command, _scp_without_ssh, node_temp_dir, dispatcher_file_exe_path, _service_name, _service_type, _command_regex)
                        
                        if self.__operation == 'start':
                            if result != 0 and result != None and result != False:
                                break
                        elif self.__operation == 'stop':
                            if result == 0 or not result:
                                break

            else:
                self.log.info(f"{instance['NODE']} are not avaliable") 
        return self.__results

    def _execute(self, command, path, ssh_command, scp_without_ssh, node_temp_dir, dispatcher_file_exe_path, _service_name, _service_type, _command_regex):
        """ 
        Used to process services/command
        """
        command = ' '.join([str(elem) for elem in command])
        
        path = ' '.join([str(elem) for elem in path])                
        
        # If target server is Linux  
        if self.__is_linux:
            if self.__action=='Stop':
                command = 'echo'
            process = Process(command, path, ssh_command)
            process.set_action(self.__action)
            process.set_servicename(_service_name)
            if _command_regex:
                process.set_command_regex(_command_regex)  
            if self.__action=='Start':
                process.set_parallel_execution(True)
            self._startstopUtilities = StartStopUtilities(process, self.__action, self.__module_label, self.__is_windows, self.__print_services)
            return self._startstopUtilities._execute_msg()
        # If target server is windows         
        if self.__is_windows:
            process = WinService(command, path, ssh_command)
            if _service_type == 'WINSERVICE':
                self.log.debug('Windows Service')
            elif _service_type == 'TASKSCHEDULER' or _service_type == None:
                process.setQuery('handle')
                process.setServiceName('java.exe')
                process.setSCPWITHOUTSSH(scp_without_ssh)
                process.setNodesTempDIR(node_temp_dir)
                process.setExecfilepath(dispatcher_file_exe_path)
                process.setServiceDisplayName(_service_name)
            self._startstopUtilities = StartStopUtilities(process, self.__action, self.__module_label, self.__is_windows, self.__print_services)
            return self._startstopUtilities._execute_msg()  


            
    def schtasks(self, command, path, ssh_command, instance):
        """
        start and stop the services using schtasks in windows
        """
        command = ' '.join([str(elem) for elem in command])
        
        path = ':'.join([str(elem) for elem in path])
        self.log.debug("SCHTASKS")
        process = WinService(command, path, ssh_command)
        process.setQuery('schtasks')
        processID = process.get_process_id()
        if self.__operation == 'start':
            if not processID:
                return process.start()
        if self.__operation == 'stop':
            #if processID:
            return process.stop()
        return processID