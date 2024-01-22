import imp
import inspect
import sys
import os
import importlib
import logging
import re

from corelib.Environment import Environment

from corelib.Loggable import Loggable
from corelib.TCProfilevars import TCProfilevars

class DynamicImporter(Loggable):

    """
    Dynamically imports modules and classes 
    """

    def __init__(self, arguments, extra_args=None):

        super().__init__(__name__)
       
        self._arguments = arguments

        self._extra_args = extra_args
        
        self._print_services = False
        
        if self._extra_args:
            if 'printservice' in self._extra_args and self._extra_args.printservice:
                self._print_services = True
        
        self._environment = None
        
        self._properties = None

        self._update_environment = None

        self._manage_services = None

        self._start_services = None

        self._stop_services = None

        self._security = None
        
        self._keepass = None

        # For python package name
        self._package_info = self.get_package_info()
        
        # For Deployment get the distrbuted package location        
        self._tcpackage_id = self.get_tcpackage_id()

        self._module_name = self.get_module_name()

        self._sub_module_name = self.get_sub_module_name()  

        self._input_file = None

        if 'inputfile' in self._arguments:
            self._input_file = self._arguments.inputfile

        if 'callback' in self._arguments: 
            self._call_back_count = self._arguments.callback
        else:
            self._call_back_count = 1

        self.parallel = False

        if 'parallel' in self._arguments:
            self.parallel = self._arguments.parallel

        self._log_file = None

        self._instances = None     

        self.setup_logger()

        self.read_environment()
        
        if self._module_name.__ne__('RefreshConfig'):
            self._instances = self.get_instances() 
        

    def setup_logger(self):

        config_provider = Loggable.get_config_provider()

        environment = Environment()
        if not self._tcpackage_id:
            log_package_id = self._module_name
        else:
            log_package_id = environment.get_tc_package_info(self._tcpackage_id)

        self._log_file = config_provider.generate_logfilename(self._module_name, self._package_info, log_package_id)
        config_provider.set_log_file(self._log_file)

        if self._arguments.debug:
            config_provider.set_console_log_level(logging.DEBUG)
        else:
            config_provider.set_console_log_level(logging.INFO)

        logger = Loggable(self._arguments.module)

        if not self._print_services: 
            logger.log.info('-----------------------------------------------------------------')


    def read_environment(self):

        environment = Environment() 

        environment.read_system_properties(self._package_info, self._print_services, self._call_back_count)
        self._properties = environment._environment['properties']

        if 'manage_services' in environment._environment:
            self._manage_services = environment._environment['manage_services']

        if 'start_services' in environment._environment:
            self._start_services = environment._environment['start_services']

        if 'stop_services' in environment._environment:
            self._stop_services = environment._environment['stop_services']

        environment.read_environment_properties(self._package_info, self._print_services, self._call_back_count)
        self._environment = environment._environment['environment']
        
        environment.read_security_keepass(self._package_info, self._print_services, self._call_back_count)
        self._keepass = environment._environment['keepass']
       
        if self._package_info.__eq__('deployment') or self._package_info.__eq__('build'):   

            environment.read_security_properties(self._package_info, self._print_services, self._call_back_count)            
            self._security = environment._environment['security']

        if self._update_environment is not None:
            environment._environment['environment'] = self._update_environment
            self._environment = self._update_environment

        self._environment_provider = environment 


    def get_package_info(self):

        return self._arguments.packageinfo
    
    def get_tcpackage_id(self):
        
        if 'packageid' in self._arguments:
            return self._arguments.packageid
        return ''

    def get_module_name(self):

        try:        
            if bool(re.match('^[A-Za-z0-9_-]*$',self._arguments.module)):
                return self._arguments.module.split('_')[0]
            else:
                return self._arguments.module.split('.')[0]     
        except Exception as exp:
            self.log.error(f'Module Input Error: {exp}')


    def get_sub_module_name(self):        
        
        try:
        
            if bool(re.match('^[A-Za-z0-9_-]*$',self._arguments.module)):     
                if len(self._arguments.module.split('_')) > 1:
                    return self._arguments.module.split('_')[1]
                else:
                    return ''
            else:
                if len(self._arguments.module.split('.')) > 1:
                    return (self._arguments.module.split('.'))[1:]
        except Exception as exp:
            self.log.error(f'Module Input Error: {exp}')

    def get_instances(self):

        if self._package_info.__eq__('deployment'):
            if int(self._call_back_count) == 1:
                tcprofilevars = TCProfilevars()
                tcprofilevars.load() 
        
                    
        if self._package_info.__ne__('deployment'):
            try:
                if self._arguments.module.upper() in self._properties:
                    if self._properties[self._arguments.module.upper()] is not None:        
                        return self._properties[self._arguments.module.upper()]['INSTANCES']
                else:                    
                    return self._properties
            except Exception:
                self.log.error("Command not present from the configuration")
                exit()
        return ''

    def get_modules_list(self, package_info: str, module_name: str):

        try:

            path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
            
            for file in os.listdir(os.path.join(path, package_info, 'modules')):
                class_name = file[:-3]
                if class_name.lower() == module_name.lower():
                    return class_name
            
        except Exception as attr:
            self.log.error(f"Modules Not Found {imp}" )
        

    def import_module(self):
        try:
            self._module_name = self.get_modules_list(self._package_info, self._module_name)
            module = importlib.import_module(self._package_info + '.modules.' + self._module_name)
            if inspect.ismodule(module):
                return module
        except Exception as imp:
            self.log.error(f"Module Not Found {imp}" )
            return None
    
    
    def get_class_obj(self, package_info, class_name):
        try:
            return getattr(package_info, class_name) 
        except AttributeError as attr:
            self.log.error(f'{attr}. Please verify the target name!')    

    def execute(self):

        try:
            module = self.import_module()
            if module is not None:
                class_obj = self.get_class_obj(module, self._module_name)

                self._update_environment = self._environment
                self._call_back_count = int(self._call_back_count) + 1
                self.read_environment()              

                if inspect.isclass(class_obj):                
                    if "action" in self._arguments and self._arguments.action:
                        self._arguments.action = self._arguments.action.capitalize()                    
                        method_instance = getattr(class_obj(self), self._arguments.action)
                        if inspect.ismethod(method_instance):                            
                            return method_instance()                  
                    else:
                        if self._package_info.__ne__('deployment') and self._package_info.__ne__('build'):
                            method_instance = self.get_class_obj(class_obj(self), 'default')                    
                        else:                            
                            if self._sub_module_name: 
                                method_instance = getattr(class_obj(self), self._sub_module_name[0])
                            else:
                                method_instance = getattr(class_obj(self), 'default')
                        if inspect.ismethod(method_instance):  
                            
                            return method_instance()
            if not self._print_services:            
                self.log.info('-----------------------------------------------------------------') 
        except AttributeError as attr:
            self.log.error(f'Dynamic Importer AttributeError: {attr}')       

        



        