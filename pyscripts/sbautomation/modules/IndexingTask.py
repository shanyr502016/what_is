"""
IndexingTask Start and Stop Service

Service Status Command:
    Step 1: ps -eo pid,ppid,command --width 4000 | grep fts
Service Start Command:
    Step 1: ps -eo pid,ppid,command --width 4000 | grep fts
    Step 2: nohup ./runTcFTSIndexer.sh  -task=objdata:sync -interval=30 &
    Step 3: ps -eo pid,ppid,command --width 4000 | grep fts
Service Stop Command:
    Step 1: ps -eo pid,ppid,command --width 4000 | grep fts
    Step 2: kill -9 2878
    Step 3: ps -eo pid,ppid,command --width 4000 | grep fts
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.Services import WinService
from sbautomation.lib.StartStopUtilities import StartStopUtilities
import os
from corelib.SCP import SCP

class IndexingTask(Loggable):

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
            
            # Location and COMMAND 
            _location = instance['LOCATION']
            _tccs_location = None
            if 'TCCS_LOCATION' in instance:
                _tccs_location = instance['TCCS_LOCATION']            
            self.__command = instance['COMMAND']  

            _retry = 1  
            
                         
            
            if _instance_count > 0:

                for nodecount, nodes in enumerate(_execute_servers):                          
                    
                    # Preparing SSH command
                    __ssh_command = self.__environment_provider.get_ssh_command(nodes)
                    
                    self.__is_linux = self.__environment_provider.is_linux(nodes['OS_TYPE'])
                    self.__is_windows = self.__environment_provider.is_windows(nodes['OS_TYPE'])   

                    _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(nodes, True))  

                    _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(nodes))     
                    
                    if __ssh_command == '':
                        self.__remote_execution = False  
                    else:
                        self.__remote_execution = True 

                    command = []
                    # Preparing the remote connection with working directory
                    working_dir = []
                    
                    if "MAX_RETRIES" in instance:
                        _retry = instance['MAX_RETRIES']
                    
                        
                    if self.__operation == 'status':
                        _retry = 1

                    for retry_count in range(_retry):

                        if retry_count > 0:

                            self.log.info(f"#{retry_count} Reattempting to {self.__operation} the service")
                        
                        # if target is windows
                        if self.__is_windows:
                            command = []
                            working_dir = []
                            handleExecutableFilePath  = os.path.join(os.path.realpath(os.path.dirname(__file__)), os.pardir,'tools', 'handle.exe')

                            if not _scp_with_ssh.check_dir_to_remote(self.__is_windows,nodes['DEPLOYMENT_CENTER_TEMP_DIR']):
                                _scp_with_ssh.create_dir_to_remote(self.__is_windows,nodes['DEPLOYMENT_CENTER_TEMP_DIR'])
       
                            # set execution location
                            working_dir.append('/')
                            if self.__operation == 'status' or self.__operation == 'stop':
                                # Copy the Handle.exe file into Temp Location                    
                                # Get the tools path
                                if self.__operation == 'stop':
                                    self.__checkindexing = False
                                    stop_command = []
                                    stop_command.append(self.__command)
                                    self.schtasks(stop_command, working_dir, __ssh_command, instance)
                                    self.__checkindexing = True

                                handlerResult = _scp_without_ssh.copy_to_remote(handleExecutableFilePath, nodes['DEPLOYMENT_CENTER_TEMP_DIR'])
                                if handlerResult == 0: 
                                    location = _location.replace('/', '\\')
                                    command.append(os.path.join('"' + nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + location + '"'))
                                    # command.append("'"+f'cd {nodes["DEPLOYMENT_CENTER_TEMP_DIR"]} && powershell -Command "'+ os.path.join(nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + r'\"'+location+r'\""'+"'"))
                                    if _tccs_location:
                                        _tccs_location = _tccs_location.replace('/', '\\')
                                        depends_command = []
                                        #powershell_command = "'"+f'cd {nodes["DEPLOYMENT_CENTER_TEMP_DIR"]} && powershell -Command "'+ os.path.join(nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + r'\"'+_tccs_location+r'\""'+"'")
                                        #depends_command.append(powershell_command)
                                        depends_command.append(os.path.join('"' + nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + _tccs_location + '"'))
                                        self.depends_service(depends_command, working_dir, __ssh_command, instance)
                                else:
                                    self.log.error(f'Unable to copy handle.exe file to {nodes["NODE"]}') 
                                    
                            elif self.__operation == 'start':
                                # Preparing the execution command
                                command.append(self.__command)
                                # using schtasks to start the service
                                self.schtasks(command, working_dir, __ssh_command, instance)
                                command = []
                                # Copy the Handle.exe file into Temp Location                    
                                # Get the tools path
                                handlerResult = _scp_without_ssh.copy_to_remote(handleExecutableFilePath, nodes['DEPLOYMENT_CENTER_TEMP_DIR'])
                                if handlerResult == 0:
                                    location = _location.replace('/', '\\')
                                    command.append(os.path.join('"' + nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + location + '"'))
                                    #powershell_command = "'"+f'cd {nodes["DEPLOYMENT_CENTER_TEMP_DIR"]} && powershell -Command "'+ os.path.join(nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + r'\"'+location+r'\""'+"'")
                                    #command.append(powershell_command)
                                    self.__checkindexing = False
                                else:
                                    self.log.error(f'Unable to copy handle.exe file to {nodes["NODE"]}')

                        # if target is linux
                        if self.__is_linux:

                            if self.__remote_execution and self.__is_linux:
                                command.append(__ssh_command)
                                command.append(f'"cd {_location} && {self.__command}"')
                                working_dir.append('/')
                            elif not self.__remote_execution and self.__is_linux:
                                command.append(self.__command)
                                working_dir.append(_location)                     
                        
                        # For Print Message
                        self.__module_label = self.__module
                        if self.__is_windows:
                            self.__module_label =  self.__module
                        # Execution command
                        if self.__print_services: 
                            # Get Service Status with returns print services informations 
                            result = self._execute(command, working_dir, __ssh_command, instance)
                            self.__results.append({
                                'pid': result,
                                'hostname': nodes['HOSTNAME'],
                                'os_type': nodes['OS_TYPE'],
                                'node': instance['NODE'],
                                'module': self.__module_label,
                                'command': self.__module_label,
                                'aliasname': nodes['ALIASNAME']
                            })

                        else:
                            self.log.info(f"Requesting the {__class__.__name__} {self.__action} from {instance['NODE']} [{nodes['HOSTNAME']}]")
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
        
        # If target server is Linux 
        if self.__is_linux:
            if self.__action=='Stop':
                command = 'echo'
            process = Process(command, path, ssh_command)
            process.set_servicename('fts')
            process.set_command_regex(r'java')
            if self.__action=='Start':
                process.set_parallel_execution(True)
            process.set_action(self.__action)
            self._startstopUtilities = StartStopUtilities(process, self.__action, self.__module_label, self.__is_windows, self.__print_services)
            return self._startstopUtilities._execute_msg() 
        # If target server is windows            
        if self.__is_windows:
            process = WinService(command, path, ssh_command)
            if self.__operation == 'status' or self.__operation == 'stop' and self.__checkindexing:
                process.setQuery('handle')
                process.setServiceName('java.exe')            
            elif self.__operation == 'start' and self.__checkindexing:
                process.setQuery('schtasks')
            elif self.__operation == 'start' and not self.__checkindexing:
                process.setQuery('handle')
                process.setServiceName('java.exe')
            elif self.__operation == 'stop' and not self.__checkindexing:
                process.setQuery('schtasks')
            
            
            self._startstopUtilities = StartStopUtilities(process, self.__action, self.__module_label, self.__is_windows, self.__print_services)
            return self._startstopUtilities._execute_msg()



    def schtasks(self, command, path, ssh_command, instance):
        """
        Using schtasks for start and stop the services if target is windows
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
            if processID:
                return process.stop()
        return processID
        
    def depends_service(self, command, path, ssh_command, instance):  
        """
        Used to get the process id and stop the service if action is Stop
        """       
        command = ' '.join([str(elem) for elem in command])
        path = ':'.join([str(elem) for elem in path])
        process = WinService(command, path, ssh_command)
        process.setQuery('handle')
        process.setServiceName('java.exe')
        processID = process.get_process_id()
        if self.__operation == 'stop':
            self.log.debug(f"Dependency FMS Services request to Stop PID: {processID}")
            if processID:                
                return process.stop()
        return processID
        
        
    
        
  