"""
AWC Start and Stop Service
"""
from argparse import Namespace
from corelib.DynamicImporter import DynamicImporter
from corelib.Environment import Environment
from corelib.Loggable import Loggable
from corelib.Table import Table

class StartStopAll(Loggable):

    BOLD = '1;'
    TEXT_BLACK = '30'
    TEXT_BROWN = '33'
    TEXT_GREEN = '32'
    TEXT_RED = '31'
    TEXT_YELLOW = BOLD + TEXT_BROWN
    TEXT_DARK_GRAY = BOLD + TEXT_BLACK

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
        Get the Start Stop services lists from config json
        """
        self.__start_services = args._start_services

        self.__stop_services = args._stop_services
        
        self.__manage_services = args._manage_services

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

        """
        Check if header is Printed
        """ 
        self.__header_printed = False

        self.__delta = None
        if args._arguments.delta:
            self.__delta = args._arguments.delta.split(',')

        
    def default(self):
        """
        Default method runs when get the print services
        """
        self.log.info("Default")
        self._start_all()


    def Start(self):

        self.log.info("Requesting to Start All Services")        
        self._start_all()


    def Stop(self):

        self.log.info("Requesting to Stop All Services")        
        self._stop_all()
        
    def Status(self):

        self.log.info("Requesting to status All Services")        
        self._status_all()


    def _start_all(self):
    
        self.get_service_status('Start', printservicestatus=False, debugstatus=True)
        self.__environment_provider.wait_execute(15, False)
        self._status_all()


    def _stop_all(self):      

        self.get_service_status('Stop',printservicestatus=False, debugstatus=True)
        self.__environment_provider.wait_execute(15, False)
        self._status_all()
        
    def _status_all(self):
    
        self.get_service_status('Status')
        


    def get_instance(self, args, printservicestatus):

        extra_args = Namespace(printservice=printservicestatus)
        self._dynamicImporter = DynamicImporter(args, extra_args)
        return self._dynamicImporter.execute()

    def get_service_status(self, action, printservicestatus=True, debugstatus=False):


        table = Table()
        table.set_column_widths([5, 25, 40, 10, 18, 30, 10, 10])
        # table.add_row(['S.No', 'Command Name', 'Service Name', 'Status', 'Server Name', 'Hostname' , 'PID', 'Alias Name'])

        services_list = list(self.__properties)
        services_list.remove('ENVIRONMENT')
        services = []
        if action == 'Start':
            services = self.__start_services
            if 'filter' in self.__arguments._arguments:
                services = list(filter(lambda x: getattr(self.__arguments._arguments, 'filter').lower() in x.lower(), self.__start_services))
            if self.__delta:
                services = self.__delta
        elif action == 'Stop':
            services = self.__stop_services
            if 'filter' in self.__arguments._arguments:
                services = list(filter(lambda x: getattr(self.__arguments._arguments, 'filter').lower() in x.lower(), self.__stop_services))
            if self.__delta:
                services = self.__delta
        elif action == 'Status':
            services = self.__manage_services
            if 'filter' in self.__arguments._arguments:
                services = list(filter(lambda x: getattr(self.__arguments._arguments, 'filter').lower() in x.lower(), self.__manage_services))
                
            if self.__delta:
                services = self.__delta

            

        #Get all service from the config.json lists automatically just comment below line.

        # order for JSON
        #services_list = [x for x in services_list if x in services]

        # order for START and STOP Keys
        services_list = [x for x in services if x in services_list]

        serviceIndexCount = 1
        serviceResults = []
        for servicesIndex, servicesName in enumerate(services_list):
            serviceData = self.get_instance(Namespace(packageinfo='sbautomation', action=action, debug=debugstatus, module=servicesName), printservicestatus)                

            for index, services in enumerate(serviceData):
                status = self.get_services_status_label(services['pid'])
                pid = self.get_services_pid_label(services['pid'])         
                serviceResults.append({'command': services['command'], 'module': services['module'], 'status':status, 'node': str(services['node']),'hostname': str(services['hostname']),'pid': str(pid), 'aliasname': str(services['aliasname']) }) 
                
                if not self.__header_printed:
                    table.add_row(['S.No', 'Command Name', 'Service Name', 'Status', 'Server Name', 'Hostname', 'PID', 'Alias Name'])
                    self.__header_printed = True
                
                table.add_row([str(serviceIndexCount), services['command'], services['module'], status, str(services['node']), str(services['hostname']), str(pid), str(services['aliasname'])],self.get_service_status_color(status))
                serviceIndexCount = serviceIndexCount + 1

        # Remove duplicate result based on node and module
        # for index, serviceResult in enumerate(list({(result['node'], result['module']):result for result in serviceResults}.values())): 
        #     table.add_row([str(serviceIndexCount), serviceResult['command'], serviceResult['module'], serviceResult['status'], serviceResult['node'], serviceResult['hostname'], serviceResult['pid']],self.get_service_status_color(serviceResult['status']))
        #     serviceIndexCount = serviceIndexCount + 1
        # table.print()
    
        
        
    def get_services_status_label(self, pid):
        
        if pid:
            return 'RUNNING'
        else:
            return 'STOPPED'
        
    def get_services_pid_label(self, pid):
        if pid:
            return pid
        else:
            return '-'
        
    @classmethod
    def get_service_status_color(cls, status):
        
        if status.__eq__('RUNNING'):
            return cls.TEXT_GREEN
        if status.__eq__('STOPPED'):
            return cls.TEXT_RED

