"""
    __description__     = 'This TCBuild Python Framework is designed to provide a user friendly and easy access of build teamcenter packages for PLM based Teamcenter Modules.'
    __author__          = 'Raghulraj Palanisamy, <raghulraj.palanisamy.ext@siemens.com>'
    __copyright__       = "© Copyright Siemens. All rights reserved"
    __version__         = 0.1
"""

def import_module_check():
    try:        
        import openpyxl
        import pykeepass
        return pykeepass
    except ModuleNotFoundError as e:
        print(f'Warning: The module was {e} not found. Please install it or check the module name.')
        return None  # Return None if module import failed
        
# Attempt to import_module_check
module_check = import_module_check()
if module_check:
    pass
else:
    exit(1)

import logging
import os
import signal
import sys
import threading
import json
import argparse
import importlib
from corelib.Loggable import Loggable
from corelib.DynamicImporter import DynamicImporter
from corelib.Constants import Constants
from corelib.PrintServices import PrintServices


__globals = globals()


def get_modules_list(package_info: str):
    
    for file in os.listdir(os.path.join(os.path.dirname(__file__), package_info, 'modules')):
        class_name = file[:-3]


class DitaEntryPoint(Loggable):

    def __init__(self, arguments, extra_agrs):

        super().__init__(__name__)

        self.arguments = arguments
        self.extra_agrs = extra_agrs

        self.target_name = self.arguments.module

        self.dynamicImporter = DynamicImporter(arguments, extra_agrs)

    def execute(self):
        try:
            result = self.dynamicImporter.execute()
            if result:
                overall_result = []
                sub_targets = []
                for res in result:
                    sub_targets.append(res['module'])
                total_execution = [*set(sub_targets)]
                
                return_code = 0
                self.log.info('Logs Generated: '+ self.dynamicImporter._log_file)
                return return_code
            else:
                return 1
        except Exception as exp:
            print(exp)
            return 1
        
def main():

   
    parser = argparse.ArgumentParser(prog='tool',formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=150, width=500),description="Welcome To Python Framework")
    
    parser.add_argument('--packageinfo', dest="packageinfo", default='build', choices = ['build'], help='Name of the package that should be called')
    
    parser.add_argument('-m', '--module', dest='module', help='Name of the module that should be called')

    parser.add_argument('-a', '--action', dest='action', help='Name of the action that should be perform')
    
    parser.add_argument('-d', '--debug', dest='debug', help='Prints debug messages on the console. By default, they are only written in the logfile.',action='store_true')

    parser.add_argument('-delta', '--delta', dest='delta', help='execute the particular service with actions as per arguments given',default = '')
    
    parser.add_argument('-filter', '--filter', dest='filter', help='execute the particular targets as per arguments given',default = '')
    
    args, extra_args = parser.parse_known_args()
    
    for arg in extra_args:
        if arg.startswith(("-", "--")):
            parser.add_argument(arg.split('=')[0])
            
    args = parser.parse_args()
    
    get_modules_list(args.packageinfo)
    
    try:
        if getattr(args, 'module'):
            manage = DitaEntryPoint(args, extra_args)  
            return_code = manage.execute()
            return return_code
    except KeyboardInterrupt:
        print("\nScript terminated by the user using Ctrl+C.")

if __name__ == "__main__":
    sys.exit(main())