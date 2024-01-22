from corelib.Loggable import Loggable
from corelib.Process import Process
import os
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants
from corelib.File import File
from corelib.SCP import SCP
import tempfile
import shutil

class AMRuleTree(Loggable):

    def __init__(self, args):   

        super().__init__(__name__)
        
        """
        Set arguments from DynamicImporter
        """         
        self.__arguments = args
        
        """
        Get the Environment Specific Values from config json
        """        
        self.__environment = args._environment
        """
        Get the Module Specific Values from config json
        """        
        self.__properties = args._properties
        """
        Get the Environment Provider method
        Reusable method derived
        """        
        self.__environment_provider = args._environment_provider
        """
        Module name from user commandline (Only Module (classname))
        """       
        self.__module_name = args._module_name

        self.__module = args._arguments.module
        self.__module_label = self.__module
        """
        Sub Module name from user commandline (Only Sub Module (classname))
        """
        self.__sub_module_name = args._sub_module_name

        """
        Target Teamcenter Package ID get from user commandline
        """        
        self._tcpackage_id = args._tcpackage_id

        """
        Target Instances setup
        """        
        self.__target = None
        """
        Remote Execution.
        """
        self.__remote_execution = False 

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel
        
        """
        Scope and target setup based on configuration
        """ 
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
            
          
    def default(self):
                       
        self._executeTargets()

    def Check(self):
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 
        for index, server_info in enumerate(_execute_servers):

            is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            if is_windows:
                _temp_dir= server_info['DEPLOYMENT_CENTER_TEMP_DIR']
            else:
                _temp_dir ='/tmp'

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):
                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id,self.__properties[self.__target]['location_in_package'])

                _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

                if os.path.exists(_location_in_package):
                    self.__environment_provider.change_execmod(os.path.join(_location_in_package,"bin"))
                    xml_args=[]
                    xml_args.append(os.path.join(_location_in_package,"bin",self.__properties[self.__target]['conversion_command']))
                    xml_args.append('-excel2xml=true')
                    xml_args.append('-xmlFolderPath="'+os.path.join(_location_in_package)+'"')
                    xml_args.append('-excelPath="'+os.path.join(_location_in_package,self.__properties[self.__target]['excel_file'])+'"')
                    xml_args.append('-sheetName="'+os.path.join(self.__properties[self.__target]['sheetName'])+'"')
                    xml_args.append('-mappingSheet="'+os.path.join(self.__properties[self.__target]['mappingSheet'])+'"')
                    xml_args.append('-logFilePath="'+os.path.join(_location_in_package)+'"')
                    conversion_command=' '.join([str(elem) for elem in xml_args])
                    self.log.info(conversion_command)
                    xml_result=self._execute(conversion_command)
                    if xml_result==0:
                        args = []
                        args.append(self.__properties[self.__target]['am_rule_command'])
                        args.append('-u=' + server_info['USERNAME'])
                        args.append('-pf=' + server_info['TC_PWF'])
                        args.append('-g=' + server_info['TC_GROUP'])
                        args.append('-inputFile='+os.path.join(_location_in_package,self.__properties[self.__target]['xml_input']))
                        args.append('-outputDir='+os.path.join(_location_in_package))
                        am_rule_command= ' '.join([str(elem) for elem in args])
                        self.log.info(am_rule_command)
                        am_rule_result=self._execute(am_rule_command, False)
                        if am_rule_result == 0:
                            _xmlTestResultsFolderPath = _scp_with_ssh.get_latest_folder_from_path(_location_in_package, is_windows)
                            _xml_file_output_name = self.__properties[self.__target]['result_xml_output']
                            _copy_result = _scp_with_ssh.copy_remote_to_remote(os.path.join(_location_in_package, _xmlTestResultsFolderPath, _xml_file_output_name), os.path.join(_location_in_package, _xml_file_output_name), self.__environment_provider.get_ssh_command(server_info))
                            if _copy_result == 0:
                                excel_args=[]
                                excel_args.append(os.path.join(_location_in_package,"bin",self.__properties[self.__target]['conversion_command']))
                                excel_args.append('-xml2excel=true')
                                excel_args.append('-xmlFolderPath="' + _location_in_package + '"')
                                excel_args.append('-excelPath="'+os.path.join(_location_in_package,self.__properties[self.__target]['excel_file'])+'"')
                                excel_args.append('-sheetName="'+os.path.join(self.__properties[self.__target]['sheetName'])+'"')
                                excel_args.append('-mappingSheet="'+os.path.join(self.__properties[self.__target]['mappingSheet'])+'"')
                                excel_args.append('-logFilePath="'+os.path.join(_location_in_package)+'"')
                                excel_conversion_command=' '.join([str(elem) for elem in excel_args])
                                self.log.info(excel_conversion_command)
                                excel_conversion_result = self._execute(excel_conversion_command)
                                if excel_conversion_result == 0:
                                    _final_result_file = _scp_with_ssh.get_latest_file_from_path(_location_in_package, _temp_dir, extension='xlsx', is_windows=is_windows)
                                    _final_copy_result = _scp_with_ssh.copy_remote_to_remote(os.path.join(_location_in_package, _final_result_file), os.path.join(_location_in_package, _xmlTestResultsFolderPath), self.__environment_provider.get_ssh_command(server_info))
                                    _final_remove_result = _scp_with_ssh.remove_file_to_remote(is_windows, os.path.join(_location_in_package, _final_result_file))
                                    if _final_copy_result == 0 and _final_remove_result == 0:
                                        self.__console_msg(excel_conversion_result, "AMRuleTree Check")
                                        self._processes.append({'NODE':server_info['NODE'],'process': _final_copy_result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AMRuleCheck"})
                                    else:
                                        _failed_process = _final_copy_result if _final_copy_result == 0 else _final_remove_result
                                        self.log.warning(f"Final result file copy/remove failed!")
                                        self._processes.append({'NODE':server_info['NODE'],'process': _failed_process,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AMRuleCheck"})
                                else:
                                    self.log.warning("ac_rules_xls_frontend XML to Excel Execution failed!")
                                    self._processes.append({'NODE':server_info['NODE'],'process': excel_conversion_result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AMRuleCheck"})
                            else:
                                self.log.warning(f"copy failed! [{_xml_file_output_name}]")
                                self._processes.append({'NODE':server_info['NODE'],'process': _copy_result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AMRuleCheck"})
                        else:
                            self.log.warning("am_rule_test_harness Execution failed!")
                            self._processes.append({'NODE':server_info['NODE'],'process': am_rule_result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AMRuleCheck"})
                    else:
                        self.log.warning("ac_rules_xls_frontend Excel to XML Execution failed!")
                        self._processes.append({'NODE':server_info['NODE'],'process': xml_result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AMRuleCheck"})
                else:
                    self.log.warning(f"{_location_in_package} Package not available")
                    self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AMRuleCheck"})
        return self._processes

    def __console_msg(self, result, action_msg):
        
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')
                

    def _execute(self, command, error_check = True):

        """ Used to process services/command
        """
        process = Process(command)
        process.set_error_check(error_check)
        return process.execute()
