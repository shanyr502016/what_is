
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Encryption import Encryption
from corelib.SCP import SCP
from corelib.File import Directory
from corelib.Constants import Constants
from deployment.lib.DitaReplacements import DitaReplacements
from corelib.DateTime import DateTime

import tempfile
import glob
import os


class Dita(Loggable):
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
        Get the Security Values
        """
        self.__security = args._security
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

        self.__action = None
        
        self._encryption = Encryption()
        
        
        
        """
        Scope and target setup based on configuration
        """ 
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
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

        self._ditaReplacements = DitaReplacements(self.__environment_provider)

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel 
        self._directory = Directory()

    def default(self):        
        return self._executeTargets() 
        
        
    def getkeepass(self):
    
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        
        for index, server_info in enumerate(_execute_servers):
        
            _ssh_command = self.__environment_provider.get_ssh_command(server_info)            
            #print(self.__arguments._keepass)   
        
    
    def generateMountPassword(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        for index, server_info in enumerate(_execute_servers):

            _ssh_command = self.__environment_provider.get_ssh_command(server_info)

            try:
                # _os_password = self.__security['aws2_machinePassword']

                mount_drive_path = server_info['MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH']

                __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
                _create_dest_folder = SCP(self.__environment_provider.get_ssh_command(server_info, False)).create_dir_to_remote(__is_windows,os.path.dirname(mount_drive_path))
                
                
                if (type(self.__security['aws2_machinePassword']) == str):
                   

                    _os_password = self.__security['aws2_machinePassword']
                    self.log.info(server_info['HOSTNAME'])
                    lines = []  
                    lines.append(f'$File = "{mount_drive_path}"')
                    lines.append('[Byte[]] $key = (1..16)')
                    lines.append(f'$Password = "{_os_password}" | ConvertTo-SecureString -AsPlainText -Force')
                    lines.append('$Password | ConvertFrom-SecureString -key $key | Out-File $File')
                    file  = tempfile.NamedTemporaryFile('w+t')
                    passwordFilePath = file.name
                    for line in lines:
                        file.write(line + '\n')
                    file.flush()
                    passwordFileCopyResult = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(passwordFilePath, os.path.join(server_info['DEPLOYMENT_CENTER_TEMP_DIR'],'generateEncryptedPassword.ps1'))
                    if passwordFileCopyResult == 0:
                        args = [_ssh_command]
                        args.append('"cd '+server_info['DEPLOYMENT_CENTER_TEMP_DIR']+' && '+server_info['DEPLOYMENT_CENTER_TEMP_DIR'].split(':')[0]+':'+' && powershell '+server_info['DEPLOYMENT_CENTER_TEMP_DIR']+'/generateEncryptedPassword.ps1"')
                        args = ' '.join([str(elem) for elem in args])
                        result = self._execute(args, '/')
                        temp_path = server_info['DEPLOYMENT_CENTER_TEMP_DIR'].replace('/','\\')
                        if result == 0:
                            del_args = [_ssh_command,'"cd '+server_info['DEPLOYMENT_CENTER_TEMP_DIR']+' && '+'del ' + temp_path + '\\generateEncryptedPassword.ps1"']
                            del_args = ' '.join([str(elem) for elem in del_args])
                            self._execute(del_args)
                            self.log.info(Constants.colorize("Generate Mount Password Successfully!.",Constants.TEXT_GREEN))
                        else:
                            self.log.error("Generate Mount Password Failed.") 

                elif (type(self.__security['aws2_machinePassword']) == list):

                    for security in self.__security['aws2_machinePassword']:

                        if security['machineName'] == server_info['ALIASNAME']:

                            _os_password = security['value']
                
                            self.log.info(security['machineName'])
                            self.log.info(server_info['HOSTNAME'])
                            lines = []  
                            lines.append(f'$File = "{mount_drive_path}"')
                            lines.append('[Byte[]] $key = (1..16)')
                            lines.append(f'$Password = "{_os_password}" | ConvertTo-SecureString -AsPlainText -Force')
                            lines.append('$Password | ConvertFrom-SecureString -key $key | Out-File $File')
                            file  = tempfile.NamedTemporaryFile('w+t')
                            passwordFilePath = file.name
                            for line in lines:
                                file.write(line + '\n')
                            file.flush()
                            passwordFileCopyResult = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(passwordFilePath, os.path.join(server_info['DEPLOYMENT_CENTER_TEMP_DIR'],'generateEncryptedPassword.ps1'))
                            if passwordFileCopyResult == 0:
                                args = [_ssh_command]
                                args.append('"cd '+server_info['DEPLOYMENT_CENTER_TEMP_DIR']+' && '+server_info['DEPLOYMENT_CENTER_TEMP_DIR'].split(':')[0]+':'+' && powershell '+server_info['DEPLOYMENT_CENTER_TEMP_DIR']+'/generateEncryptedPassword.ps1"')
                                args = ' '.join([str(elem) for elem in args])
                                result = self._execute(args, '/')
                                temp_path = server_info['DEPLOYMENT_CENTER_TEMP_DIR'].replace('/','\\')
                                if result == 0:
                                    del_args = [_ssh_command,'"cd '+server_info['DEPLOYMENT_CENTER_TEMP_DIR']+' && '+'del ' + temp_path + '\\generateEncryptedPassword.ps1"']
                                    del_args = ' '.join([str(elem) for elem in del_args])
                                    self._execute(del_args)
                                    self.log.info(Constants.colorize("Generate Mount Password Successfully!.",Constants.TEXT_GREEN))
                                else:
                                    self.log.error("Generate Mount Password Failed.")   
            except Exception as exp:
                self.log.error(f"Encrypted Password not generated {exp}")
    
    def replacement(self):        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 
        for index, server_info in enumerate(_execute_servers):
            self.log.info(f"Replacement Starting...")
            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):
                try:
                    _properties_config_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['properties_config_in_package'])

                    if os.path.exists(os.path.join(_properties_config_in_package, self.__environment_provider.get_environment_name())):

                        _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))

                        _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

                        replacement_foldername = 'deploy_'+self.__environment_provider.get_environment_name().lower()

                        _replacement_path = self.__environment_provider.get_location_in_package(tc_package_id, replacement_foldername)

                        _excludes_extension = self.__properties[self.__target]['excludes_replacements_extension']

                        if os.path.exists(_replacement_path):
                            self._directory.removedirs(_replacement_path)

                        if not os.path.exists(_replacement_path):
                            os.makedirs(_replacement_path)

                        _replacement_properties_path = os.path.join(_properties_config_in_package,self.__environment_provider.get_environment_name())

                        _package_location = self.__environment_provider.get_location_in_package(tc_package_id)
                        
                        for properties_file in os.listdir(_replacement_properties_path):
                            properties_name = ''.join(properties_file.split('.')[:-1]).split('__')
                            if len(properties_name) == 1:
                                os.makedirs(os.path.join(_replacement_path,(''.join(properties_name))))
                                _copytoreplacementdir = SCP('').copy_to_local(os.path.join(_package_location,''.join(properties_name),'*'),os.path.join(_replacement_path,''.join(properties_name)), self._parallel)
                                self.__environment_provider.change_execmod(_replacement_path)
                                self._processes.append({'NODE':server_info['NODE'],'process': _copytoreplacementdir,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - {''.join(properties_name)}"})
                                if _copytoreplacementdir == 0:                                    
                                    self._ditaReplacements._updateProperties(os.path.join(_replacement_properties_path,properties_file), _replacement_path, _excludes_extension)
                                self.__console_msg(_copytoreplacementdir, f"[{tc_package_id}] - [{replacement_foldername}/{''.join(properties_name)}]")
                            else:
                                os.makedirs(os.path.join(_replacement_path,('/'.join(properties_name))))
                                _copytoreplacementdir = SCP('').copy_to_local(os.path.join(_package_location,'/'.join(properties_name), '*'),os.path.join(_replacement_path,'/'.join(properties_name)), self._parallel)
                                self.__environment_provider.change_execmod(_replacement_path)
                                self._processes.append({'NODE':server_info['NODE'],'process': _copytoreplacementdir,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - {''.join(properties_name)}"})
                                if _copytoreplacementdir == 0:
                                    self._ditaReplacements._updateProperties(os.path.join(_replacement_properties_path,properties_file), _replacement_path, _excludes_extension)
                                self.__console_msg(_copytoreplacementdir, f"[{tc_package_id}] - [{replacement_foldername}/{'/'.join(properties_name)}]")
        
                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}]"})
        return self._processes

    def infra(self):
        
        for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

            try:
                location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                env_path = os.path.join(location_in_package,self.__environment_provider.get_environment_name().lower())

                if os.path.exists(env_path):

                    for alias_path in os.listdir(env_path):

                        alias_source_dir = os.path.join(env_path,alias_path)

                        for alias_src in os.listdir(alias_source_dir):

                            alias_src_dir = os.path.join(env_path,alias_path,alias_src)                           

                            alias_path_files = [os.path.join(root, file).split(alias_path,1)[-1] for root, dirs, files in os.walk(alias_src_dir) for file in files]
                            
                            if len(alias_path_files):

                                executionServer = self._getServerNameByAlias(alias_path)

                                if executionServer:

                                    _execute_servers = self.__environment_provider.get_execute_server_details(executionServer)

                                    for index, server_info in enumerate(_execute_servers):

                                        _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info,True))

                                        self.log.info(f'{alias_path} Replacement Started')

                                        if self.__environment_provider.is_linux(server_info['OS_TYPE']):
                                            root_dir  = ''
                                        else:
                                            root_dir  = server_info['TCAPPL_ROOT_DIR']

                                        for infra_file in alias_path_files:

                                            _src_file = root_dir + infra_file
                                            self.log.info(_src_file)
                                            copyfilesresult = _scp_without_ssh.copy_to_remote(os.path.join(env_path,alias_path) + infra_file, _src_file)
                                            self._processes.append({'NODE':server_info['NODE'],'process': copyfilesresult,'module': self.__module_label, 'package_id': '', 'label': f"[Infra update]"})
                                            self.__console_msg(copyfilesresult,f'{alias_path} Infra files Replacement')

                else:
                    self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. {__class__.__name__} Skipped")
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'process': 1,'module': self.__module_label, 'package_id': '', 'label': f"[Infra update]"})
        return self._processes
        

    def infrabackup(self):
            
        
        for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):
            try:

                location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                env_path = os.path.join(location_in_package,self.__environment_provider.get_environment_name().lower())

                timestamp_path = DateTime.get_datetime("%d%m%Y%H%M%S")

                if os.path.exists(env_path): 

                    for alias_path in os.listdir(env_path):

                        alias_source_dir = os.path.join(env_path,alias_path)

                        for alias_src in os.listdir(alias_source_dir):

                            alias_src_dir = os.path.join(env_path,alias_path,alias_src)
                            
                            alias_path_files = [os.path.join(root, file).split(alias_source_dir)[-1] for root, dirs, files in os.walk(alias_src_dir) for file in files]

                            if len(alias_path_files):

                                executionServer = self._getServerNameByAlias(alias_path)

                                if executionServer:

                                    _execute_servers = self.__environment_provider.get_execute_server_details(executionServer)

                                    for index, server_info in enumerate(_execute_servers):

                                        _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

                                        _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info,True))

                                        _target_path = os.path.join(self.__environment_provider.get_share_root_path(),self.__properties[self.__target]['targetPath'])

                                        self.log.info(f'{alias_path} Backup Started')

                                        if self.__environment_provider.is_linux(server_info['OS_TYPE']):

                                            root_dir  = ''

                                            _temp_backup_path = os.path.join(_target_path,self.__environment_provider.get_environment_name()+ '_' + timestamp_path,alias_path)

                                            _scp_with_ssh.create_dir_to_local(self.__environment_provider.is_windows(server_info['OS_TYPE']),_temp_backup_path)

                                        else:
                                            root_dir  = server_info['TCAPPL_ROOT_DIR']

                                            _temp_backup_path = os.path.join(_target_path,self.__environment_provider.get_environment_name()+ '_' + timestamp_path,alias_path)
                                            _scp_with_ssh.create_dir_to_local(False,_temp_backup_path)

                                        for infra_file in alias_path_files:
                                        
                                            _src_file = root_dir + infra_file

                                            head, tail = os.path.split(infra_file)

                                            _scp_with_ssh.create_dir_to_local(False,_temp_backup_path + head)

                                            copyfilesresult = _scp_without_ssh.copy_from_remote(_src_file,_temp_backup_path + head)
                                            self._processes.append({'NODE':server_info['NODE'],'process': copyfilesresult,'module': self.__module_label, 'package_id': '', 'label': f"[Infra update]"})

                                            self.__console_msg(copyfilesresult,f'{alias_path} Infra files Backuped')

                else:
                    self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. {__class__.__name__} Skipped")

            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '', 'label': f"[Infra update]"})
        return self._processes

    def _getServerNameByAlias(self,aliasname):
        for servername, properties in self.__environment.items():            
            if servername != 'ENVIRONMENT':                
                for values in properties:
                    if 'ALIASNAME' in values:                       
                        if values['ALIASNAME'].__ne__('') and values['ALIASNAME'].split('.')[0] == aliasname:
                            self.log.info(servername)
                            return servername


    def _executeTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__module_name).split(',')): 
                    # Execute with multiple targets
                if not self.__sub_module_name:   
                    self.__target = targets  
                    dynamicExecutor = DynamicExecutor(self.__arguments)   
                    dynamicExecutor.set_module_instance(targets) # module instance name
                    # calling the targets one by one
                    if dynamicExecutor.get_sub_module_name():
                        _processesResult = getattr(Dita, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult             
        except Exception as exp:
            self.log.error(exp)              
            
    def _execute(self, command, path=""):
        
        """ Used to process services/command
        """
        process = Process(command)
        process.set_parallel_execution(self._parallel)
        return process.execute() 
     
    def __console_msg(self, result, action_msg):
        
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Copied Failed.")
        self.log.info('..............................................................')