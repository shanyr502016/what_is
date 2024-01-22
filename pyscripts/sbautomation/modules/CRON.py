"""
CRONTAB Start and Stop Service
"""
from corelib.Loggable import Loggable
import os
from corelib.Process import Process
from corelib.Services import WinService
from sbautomation.lib.StartStopUtilities import StartStopUtilities
from corelib.Crontab import Crontab
from corelib.SCP import SCP

class CRON(Loggable):
    

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

            # _location = instance['LOCATION']   
            # _service_name = instance['SERVICE_NAME'] 

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


                    crontab = Crontab()

                    crontab.setSSHCommand(__ssh_command)
                    crontab.setSCPWithOutSSH(_scp_without_ssh)
                    crontab.setSCPWithSSH(_scp_with_ssh)
                    crontab.setAction(self.__operation)

                    # For Print Message
                    self.__module_label = self.__module

                    # Execution command
                    if self.__print_services: 
                        # Get Service Status with returns print services informations                  
                        self.__results.append({
                            'pid': crontab.status(),
                            'hostname': nodes['HOSTNAME'],
                            'os_type': nodes['OS_TYPE'],
                            'node': instance['NODE'],
                            'module': self.__module_label,
                            'command': self.__module_label,
                            'aliasname': nodes['ALIASNAME']
                        })
                    else:
                        self.log.info(f"Requesting the {__class__.__name__} CronJobs {self.__action} from {instance['NODE']} [{nodes['HOSTNAME']}]")
                        if self.__operation == 'start':
                            crontab.start()
                        elif self.__operation == 'stop':
                            crontab.stop()
                            
                        status = crontab.status()
                        if status is None:
                            status = 'Disabled'                            
                        Loggable.log_success(self, f"{self.__module_label} is {status}. ")
                            

            else:
                self.log.info(f"{instance['NODE']} are not avaliable")
        return self.__results
