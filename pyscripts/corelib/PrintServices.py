

from corelib.Loggable import Loggable
import logging
from corelib.Table import Table
from argparse import Namespace
from corelib.DynamicImporter import DynamicImporter
from corelib.Environment import Environment

class PrintServices(Loggable):
    
    
    BOLD = '1;'
    TEXT_BLACK = '30'
    TEXT_BROWN = '33'
    TEXT_GREEN = '32'
    TEXT_RED = '31'
    TEXT_YELLOW = BOLD + TEXT_BROWN
    TEXT_DARK_GRAY = BOLD + TEXT_BLACK
    
    
    def __init__(self, arguments=None, extra_args=None):
        
        super().__init__(__name__)

        self._arguments = arguments
        
        self._dynamicImporter = None
        
        self._results = None     

        # For python package name
        self._package_info = self._arguments.packageinfo

        config_provider = Loggable.get_config_provider()
        self._log_file = config_provider.generate_logfilename('Services')
        config_provider.set_log_file(self._log_file)

        if self._arguments.debug:
            config_provider.set_console_log_level(logging.DEBUG)
        else:
            config_provider.set_console_log_level(logging.INFO)
        
        logger = Loggable('Services')

        self._environment = Environment()

        self._manage_services = None
        
        
    def get_instance(self, args):

        extra_args = Namespace(printservice=True)
        self._dynamicImporter = DynamicImporter(args, extra_args)
        return self._dynamicImporter.execute()       

    def get_services_status(self):
                
        table = Table()
        table.set_column_widths([5, 25, 40, 10, 18, 30, 10, 10])        
        
        self.log.info(f"Environment Name : {self._environment.get_environment_name()}") 

        table.add_row(['S.No', 'Command Name', 'Service Name', 'Status', 'Server Name', 'Hostname' , 'PID', 'Alias Name'])       

        services_list = list(self._environment.read_system_properties(self._package_info, True, 1).keys())
        services_list.remove('ENVIRONMENT')
        services = []
        if 'manage_services' in self._environment._environment:
            self._manage_services = self._environment._environment['manage_services']
            services = self._manage_services
        
            if 'filter' in self._arguments:
                services = list(filter(lambda x: getattr(self._arguments, 'filter').lower() in x.lower(), self._manage_services))
                
        #Get all service from the config.json lists automatically just comment below line.
        services_list = [x for x in services_list if x in services]

        serviceIndexCount = 1
        serviceResults = []
        for servicesIndex, servicesName in enumerate(services_list):
            serviceData = self.get_instance(Namespace(packageinfo='sbautomation', action=None, debug=False, module=servicesName))    

            for index, services in enumerate(serviceData):
                status = self.get_services_status_label(services['pid'])
                pid = self.get_services_pid_label(services['pid'])         
                serviceResults.append({'command': services['command'], 'module': services['module'], 'status':status, 'node': str(services['node']),'hostname': str(services['hostname']),'pid': str(pid), 'aliasname': str(services['aliasname']) }) 
                table.add_row([str(serviceIndexCount), services['command'], services['module'], status, str(services['node']), str(services['hostname']), str(pid), str(services['aliasname'])],self.get_service_status_color(status))
                serviceIndexCount = serviceIndexCount + 1
        # Remove duplicate result based on node and module
        # for index, serviceResult in enumerate(list({(result['node'], result['module']):result for result in serviceResults}.values())): 
        #     table.add_row([str(serviceIndexCount), serviceResult['command'], serviceResult['module'], serviceResult['status'], serviceResult['node'], serviceResult['hostname'], serviceResult['pid']],self.get_service_status_color(serviceResult['status']))
        #     serviceIndexCount = serviceIndexCount + 1
        # table.print()
        return 0
        
        
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