"""
DEAD_PROCESS Start and Stop Service
"""
import os
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.Services import WinService
from sbautomation.lib.StartStopUtilities import StartStopUtilities
from corelib.SCP import SCP
import subprocess

class DeadProcess(Loggable):
    
    def __init__(self, args):       

        super().__init__(__name__)

        """
        Get the Environment Specific Values from config json
        """
        self.__environment = args._environment
        
        self.__arguments = args
        
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
        
        self.log.info("Analyzing the Teamcenter Process...")         
       
        execute_servers = []
        
        if 'server' in self.__arguments._arguments:
        
            # Filtering the server specific filter        
            execute_servers = list(filter(lambda x: x['NODE'] == getattr(self.__arguments._arguments, 'server'), self.__instances))
            
        else:
            
            execute_servers = self.__instances
            
            
        if 'process' in self.__arguments._arguments:
        
            for item in execute_servers:
            
                # Filtering the service specific filter              
                item['FILTERS'] = getattr(self.__arguments._arguments, 'process')        
        
        for inscount, instance in enumerate(execute_servers):
 
            _execute_servers = self.__environment_provider.get_execute_server_details(instance['NODE'])   

            _command = instance['COMMAND']
            _filter_list = instance['FILTERS'].split(',')  

            _instance_count = len(_execute_servers)            
               
            if _instance_count > 0:
                
                for nodecount, nodes in enumerate(_execute_servers):              
                   
                    # Preparing SSH command
                    __ssh_command = self.__environment_provider.get_ssh_command(nodes)

                    scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(nodes,True))
                    _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(nodes))
                    
                    self.__is_linux = self.__environment_provider.is_linux(nodes['OS_TYPE'])
                    self.__is_windows = self.__environment_provider.is_windows(nodes['OS_TYPE'])                     
                    
                    if self.__is_linux:
                        _processes = []
                        for _filter in _filter_list:
                            
                            args = [__ssh_command]
                            args.extend(['ps -eo pid,ppid,command --width 4000 | grep',_filter])
                            command = ' '.join([str(elem) for elem in args])
                            _process_list = self._executes(command,_filter,__ssh_command)
                        
                            for cmd_line in _process_list:
                                if cmd_line.split()[1] == '1':
                                    proc = {}
                                    proc['name'] = _filter
                                    proc['pid'] = int(cmd_line.split()[0])
                                    proc['cmdline'] = cmd_line.split()[2]
                                    _processes.append(proc)                                
                            
                            _processes = list({item['pid']:item for item in _processes}.values())                            
                                    
                        for _proc in _processes:
                            if not self.__print_services:                                        
                                self.log.info(f"Searching the PID: {str(_proc['pid'])} ({str(_proc['name'])})")
                            if self.__operation == 'stop':
                                
                                process = Process('','',__ssh_command)
                                process.killPID(str(_proc['pid']))

                    if self.__is_windows:
                        

                        if not _scp_with_ssh.check_dir_to_remote(self.__is_windows,nodes['DEPLOYMENT_CENTER_TEMP_DIR']):
                            _scp_with_ssh.create_dir_to_remote(self.__is_windows,nodes['DEPLOYMENT_CENTER_TEMP_DIR'])
                        
                        handleExecutableFilePath  = os.path.join(os.path.realpath(os.path.dirname(__file__)), os.pardir,'tools', 'handle.exe')
                        copy_result = scp_without_ssh.copy_to_remote(handleExecutableFilePath, nodes['DEPLOYMENT_CENTER_TEMP_DIR'])
                        if copy_result == 0:                            
                            _processes = []
                            for _filter in _filter_list:
                                depends_command = []
                                depends_command.append(os.path.join('"' + nodes['DEPLOYMENT_CENTER_TEMP_DIR'], 'handle.exe -v ' + _filter + '"'))
                                args = ' '.join([str(elem) for elem in depends_command])                               
                                
                                lines = self._execute(args, __ssh_command)                                
                                for line in lines:
                                    if '.exe' in line:
                                        proc = {}
                                        proc['name'] = line.split(',')[0]
                                        proc['pid'] = int(line.split(',')[1])
                                        proc['cmdline'] = line.split(',')[4]
                                        _processes.append(proc)                                
                                _processes = list({item['pid']:item for item in _processes}.values())                    
                                
                            for _proc in _processes:
                                
                                if 'svchost' not in _proc['name']:

                                    if not self.__print_services:
                                        self.log.info(f"Searching the PID: {str(_proc['pid'])} ({str(_proc['name'])})")
                                    if self.__operation == 'stop':
                                        
                                        process = WinService('', '', __ssh_command)
                                        process.setQuery('taskkill')
                                        process.setKillPID(str(_proc['pid']))
                                        process.stop()
                                        if 'explorer' in _proc['name']:
                                            explorer_command = []
                                            explorer_command.append(os.path.join('"explorer.exe"'))
                                            args = ' '.join([str(elem) for elem in explorer_command])
                                            explorer_refresh = WinService(args, '', __ssh_command)
                                            explorer_refresh.setQuery('handle')
                                            explorer_refresh.execute_with_parallel()
                        else:
                            self.log.error(f'Unable to copy handle.exe file to {nodes["NODE"]}')
            else:
                self.log.info(f"{instance['NODE']} are not avaliable")
        self.log.info("DeadProcess Analyzing Completed!")
        return self.__results

    def _executes(self,command,_filter,ssh_command, stderr = True):
        _result = []
        if self.__is_linux:
            process = Process(command,'',ssh_command)
            process.set_stderr(stderr)
            process.hide_output()
            process.collect_output()
            process.ignore_errors()
            process.execute()
            return process.get_out_lines()
        return _result
    
    def depends_service(self, command, path, ssh_command, service_name):        
        process = WinService(command, path, ssh_command)
        process.setQuery('handle')
        process.setServiceName(service_name+'.exe')
        processID = process.get_process_id()
        return {'PID':processID,'SERVICE':service_name}
        
        
    def _execute(self, command, _ssh_command, path='', stderr = True, ignoreerror=False):
        if self.__is_linux:
            process = Process(command, path, _ssh_command)
            process.set_stderr(stderr)
            return process.execute()
        if self.__is_windows:
            process = WinService(command, path, _ssh_command)
            process.setQuery('handle')
            return process.execute()