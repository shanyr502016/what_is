
"""
Refresh Configuration from Git
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
import os


class RefreshConfig(Loggable):

    def __init__(self, args):

        super().__init__(__name__)

        self.__environment = args._environment
        
        self.__properties = args._properties
        
        self.__action = args._arguments.action
        
        self.__environment_provider = args._environment_provider 

        self.__module_name = args._module_name

        self.__sub_module_name = args._sub_module_name

        self.__instances = args._instances
        
        self.__operation = None

        self.__branch = None

        self.__repoURL = None

    def default(self):
        self.log.info("Refresh Configuration from Git Repository")
        self.get_repoUrl()
        self.get_branch()
        self.git_pull()
        
        return True
    
    def get_repoUrl(self):

        args = 'git config --get remote.origin.url'
        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        process.execute()
        result = process.get_out_lines()
        self.__repoURL = str(result[0])
         
    
    def get_branch(self):

        args = 'git branch --show-current'
        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        process.execute()
        result = process.get_out_lines()
        self.__branch = str(result[0])

    def git_pull(self):
        args = 'git reset --hard && git pull'
        process = Process(args)
        result = process.execute()
        self.log.info('https://code.siemens.com/a-pe/emea/siemens-mobility/plm_mo_ri/smo_ci-cd.git')
        self.__console_msg(result, 'Updated the latest configuration from branch ['+ self.__branch+'*]' )  


    def __console_msg(self, result, action_msg):
        if result == 0:
            Loggable.log_success(self, f"{action_msg.capitalize()} Successfully.")
        else:
            Loggable.log_success(self, f"{action_msg.capitalize()} Failed.")
        self.log.info('..............................................................')