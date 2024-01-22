"""
    __description__     = 'This Deployment Python Framework is designed to provide a user friendly and easy access of build and deployment for PLM based Teamcenter Modules.'
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


__globals = globals()

def get_modules_list(package_info: str):
    
    for file in os.listdir(os.path.join(os.path.dirname(__file__), package_info)):
        class_name = file[:-3]


class DitaEntryPoint(Loggable):

    def __init__(self, arguments, extra_agrs):

        super().__init__(__name__)

        self.arguments = arguments
        self.extra_agrs = extra_agrs

        self.target_name = self.arguments.module

        self.dynamicImporter = DynamicImporter(arguments, extra_agrs)

    def execute(self):

        result = self.dynamicImporter.execute()
        
        if result:
            overall_result = []
            sub_targets = []
            for res in result:
                sub_targets.append(res['module'])
            total_execution = [*set(sub_targets)]
            for total_exec in total_execution:
                _return_code_status = []
                _name = ''
                for res in result:
                    if res['module'] == total_exec:    
                        _name = res['module']
                        _return_code_status.append(res['process'])
                overall_result.append({'sub_target_name': _name, 'return_code': sum(_return_code_status)})
            sub_target_status = ''
            target_success_result = 0
            target_failure_result = 0
            return_code = 0
            for subtarget_result in overall_result:
                return_code = return_code + subtarget_result['return_code']
                colorcode = Constants.TEXT_WHITE
                if bool(subtarget_result['return_code']):
                    colorcode = Constants.TEXT_RED
                    target_failure_result = target_failure_result + 1
                else:
                    colorcode = Constants.TEXT_GREEN
                    target_success_result = target_success_result + 1
                if sub_target_status.__eq__(''):
                    sub_target_status = Constants.colorize(subtarget_result['sub_target_name'], colorcode)
                else:
                    sub_target_status = sub_target_status + ',' + Constants.colorize(subtarget_result['sub_target_name'], colorcode)
            self.log.info(Constants.colorize('------------------------------------ Overall Status ---------------------------------------------------\n', Constants.TEXT_WHITE))
            if self.target_name == subtarget_result['sub_target_name']:
                self.log.info(Constants.colorize(f'{Constants.TAB}Target Name: {self.target_name}{Constants.TAB}TargetResults:' , Constants.TEXT_WHITE) + f' {sub_target_status} \n')
            else:
                self.log.info(Constants.colorize(f'{Constants.TAB}Target Name: {self.target_name}{Constants.TAB}SubTargets:' , Constants.TEXT_WHITE) + f' {sub_target_status} \n')
            self.log.info(Constants.colorize(f'{Constants.TAB}Total Execution: {len(total_execution)}{Constants.TAB}Success: {target_success_result}{Constants.TAB}Failure: {target_failure_result}\n', Constants.TEXT_WHITE))
            self.log.info(Constants.colorize('-------------------------------------------------------------------------------------------------------', Constants.TEXT_WHITE))
            self.log.info('Logs Generated: '+ self.dynamicImporter._log_file)
            return return_code
        else:
            return 1

def main():
    
    parser = argparse.ArgumentParser(prog='tool',formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=550, width=500),description="Welcome To Deployment Framework")
    
    parser.add_argument('--packageinfo', dest="packageinfo", default='deployment', choices = ['deployment'], help='Name of the python package that should be called')
    
    parser.add_argument('-m', '--module', dest='module', help='Name of the module that should be called')

    parser.add_argument('-p', '--packageid', dest='packageid', help='Location that should be perform')

    parser.add_argument('-i', '--inputfile', dest='inputfile',help='Input files' ,default='')
    
    parser.add_argument('-d', '--debug', dest='debug', help='Prints debug messages on the console. By default, they are only written in the logfile.',action='store_true')

    parser.add_argument('-c', '--callback', dest='callback', default='1', help='Callback count initialise')

    parser.add_argument('-r', '--resume-skip', dest='resumestate', help='Resume Targets',action='store_true')

    parser.add_argument('-delta', '--delta', dest='delta', help='execute the particular targets as per arguments given',default = '')

    parser.add_argument('-delta-exclude', '--delta-exclude', dest='delta-exclude', help='execute the exclude particular targets as per arguments given',default = '')
    
    args, extra_args = parser.parse_known_args()  
    
    for arg in extra_args:
        if arg.startswith(("-", "--")):
            parser.add_argument(arg.split('=')[0])
            
    args = parser.parse_args()    
    get_modules_list(args.packageinfo)
    
    try:
    
        if len(sys.argv) > 1:  
            deploy = DitaEntryPoint(args, extra_args)  
            return_code = deploy.execute()
            return return_code
        else:
            symbol = "-"
            message = "Welcome to DITA!"
            print(symbol * len(message))
            print("\033[1;32;40m" + message + "\033[0m")
            print(symbol * len(message))
            print('DITA Deploy Commands Lists with Options:')
            print('----------------------------------------')
            
            print('\033[1;32;40m--delta SUB_TARGET_NAME\033[0m Example: --delta Backup.tcroot.lnx,Backup.tcroot.win \nThis options based on Group already configured in deploy_targets\n')
            
            print('\033[1;32;40m--server SERVER_NAME\033[0m Example: --server AWC_MLF \nThis options based on Group already configured in deploy_targets\n')
            
            exectuion_shell_command = './dita_deploy.sh'
            with open(os.path.join(os.pardir,'.config/Deploy/deploy_targets.json')) as modules_list:
                modules = json.load(modules_list)
                #modules = {key: modules[key] for key in sorted(modules)}
                unique_target_names = set(item.split('.')[0] for item in modules if '.' in item)
                print('COMMANDS:')
                for main_targets in unique_target_names:                    
                    subtargets = set(module for module in modules if module.startswith(main_targets))
                    print('\n\033[1;32;40m['+ main_targets +']\033[0m')
                    for subtarget in subtargets:
                        print(exectuion_shell_command + ' -m ' +subtarget + ' -p PackageName -d')
                    print('-----------------------------------------------------------------------')
    except KeyboardInterrupt:
        print("\nScript terminated by the user using Ctrl+C.")

if __name__ == "__main__":    
    sys.exit(main())