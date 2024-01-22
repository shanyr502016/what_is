from corelib.Loggable import Loggable
from corelib.Process import Process
import os
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants
from corelib.File import File
from corelib.SCP import SCP
import tempfile
import shutil

class AWC(Loggable):
    
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

    def copy(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 
        
        for index, server_info in enumerate(_execute_servers):

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                if os.path.exists(_location_in_package):

                    _scp = SCP(self.__environment_provider.get_ssh_command(server_info, True))

                    if self.__environment_provider.get_property_validation('AWC_STAGE_PATH', server_info):
                        _awc_path = server_info['AWC_STAGE_PATH']                   

                    _copysrc = _scp.copy_to_remote(os.path.join(_location_in_package, '*'),_awc_path)
                    
                    self._processes.append({'NODE':server_info['NODE'],'process': _copysrc,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - AWC Copied"})
                    if not self._parallel:
                        self.__console_msg(_copysrc, "AWC Copied")                       
                else:
                    self.log.warning(f"Required Package Folder not Present from this location [{tc_package_id}]. AWC Copied Skipped")
        return self._processes        

    def build(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 
        
        for index, server_info in enumerate(_execute_servers):
        

            self.log.info("Requesting to Starting the Teamcenter Process Manager")
            self.servicestart('AWC_Micro', server_info['NODE'])

            _scp = SCP(self.__environment_provider.get_ssh_command(server_info, True))

            if self.__environment_provider.get_property_validation('AWC_STAGE_PATH', server_info):
                _awc_path = server_info['AWC_STAGE_PATH']                   
            else:
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"AWC Build"})
                return self._processes

            __ssh_command = self.__environment_provider.get_ssh_command(server_info)    

            args = [__ssh_command]

            args.append(os.path.join(_awc_path, 'awbuild.cmd'))    

            args = ' '.join([str(elem) for elem in args])                    

            result = self._execute(args)                        

            _result = 1                        

            for index, line in enumerate(result):
                
                if "Finished 'build'" in line:
                    self.log.info("Build Finished")
                    _result = 0

            for index, line in enumerate(result):
                self.log.debug(line)
                if "out\darsi.zip uploaded" in line or "out\site.zip uploaded" in line:
                    self.log.info("Build Finished")
                    _result = 0

            for index, line in enumerate(result):
                if "No gateway available" in line:
                    self.log.info("No Gateway Available")
                    _result = 1                     

            if _result == 0:
                self.log.info("Requesting to Stop the Teamcenter Process Manager")
                self.servicestop('AWC_Micro', server_info['NODE'])

                if 'temp_paths' in self.__properties[self.__target]:

                    temp_path_list = self.__properties[self.__target]['temp_paths']

                    clear_tempdir_result = self.clear_temp_dirs(temp_path_list,server_info)

                    if clear_tempdir_result == 0:
                        self.log.info("Requesting to Start the Teamcenter Process Manager")
                        # self.servicestart('AWC_Micro', server_info['NODE'])
                        if not self._parallel:
                            self.__console_msg(clear_tempdir_result, "AWC Build")  
                        self._processes.append({'NODE':server_info['NODE'],'process': clear_tempdir_result,'module': self.__module_label, 'package_id': '','label': f"AWC Build"})

                    else:
                        self.log.error('Temp Directories Delete - Failed.')
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"AWC Build"})
                
                else:
                    self.log.warning('Temp Directories not configured in deploy targets!')
                    self.log.info("Requesting to Start the Teamcenter Process Manager")
                    # self.servicestart('AWC_Micro', server_info['NODE'])
                    if not self._parallel:
                        self.__console_msg(_result, "AWC Build")                    
                    self._processes.append({'NODE':server_info['NODE'],'process': _result,'module': self.__module_label, 'package_id': '','label': f"AWC Build"})

            else:
                self.__console_msg(_result, "AWC Build")
                self._processes.append({'NODE':server_info['NODE'],'process': _result,'module': self.__module_label, 'package_id': '','label': f"AWC Build"})
            
        return self._processes
    


    def copyFileRepo(self, server_info, driveletter, rootpath, sourcedir, destination,backup_path, zip_dir, target_server, unzip = False):

        lines = []

        lines.append('Write-Host "DiagnosticCheck Started"')
        lines.append('[Byte[]] $key = (1..16)\n')
        lines.append('$encrypted = Get-Content '+server_info['MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH']+' | ConvertTo-SecureString -Key $key')
        lines.append('$credential = New-Object System.Management.Automation.PsCredential("'+server_info['DOMAIN']+'\\'+server_info['USERNAME']+'", $encrypted)')
        lines.append('New-PSDrive -name "'+ driveletter +'" -PSProvider FileSystem -Root "'+ rootpath +'" -Persist -Credential $credential')
        lines.append('Set-Location -Path '+ sourcedir +' ')
        if not unzip:
            lines.append('& "'+zip_dir+'" a -t7z -m0=lzma2 -mx=5 -mfb=64 -md=32m -ms=on "'+os.path.join(destination,target_server['HOSTNAME'])+'/'+ os.path.basename(target_server['FILE_REPO'])+'.7z'+'" "'+sourcedir+'/*'+'" -mx0 ')
        else:
            
            lines.append('ROBOCOPY "'+ os.path.join(sourcedir,target_server['HOSTNAME']) + '" "'+backup_path+'" "'+os.path.basename(target_server['FILE_REPO'])+'.7z"'+' /IS /NJS')
            lines.append('& "'+zip_dir+'" x "'+backup_path+'\\'+os.path.basename(target_server['FILE_REPO'])+'.7z'+'" -o"'+destination+'" -aoa ')            
        
        file  = tempfile.NamedTemporaryFile('w+t')
        filepath = file.name
        for line in lines:
            self.log.debug(line)
            file.write(line + '\n')
        file.flush()
        _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True)) 
        result = _scp_without_ssh.copy_to_remote(filepath, os.path.join(server_info['DEPLOYMENT_CENTER_TEMP_DIR'],'awcfilerepocopy.ps1'))
        return result
    

    def _zipFileRepo(self, build_server):

        args = []

        __ssh_command = self.__environment_provider.get_ssh_command(build_server)

        _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(build_server))

        is_windows = self.__environment_provider.is_windows(build_server['OS_TYPE'])

        _zip_path = build_server['FILE_REPO']+'.7z'

        if _scp_with_ssh.check_dir_to_remote(self.__environment_provider.is_windows(build_server['OS_TYPE']), _zip_path):

            _delete_status = _scp_with_ssh.remove_file_to_remote(is_windows,_zip_path,False) 

            self.log.info(f"Removed Previous backuped file {_zip_path}")  

        args = [__ssh_command]

        args.extend([build_server['7ZIP_PATH'], 'a', '-t7z', '-m0=lzma2', '-mx=5', '-mfb=64', '-md=32m', '-ms=on'])
        args.extend([_zip_path])
        args.extend([build_server['FILE_REPO']]) 

        args = ' '.join([str(elem) for elem in args])

        self.log.info(f"FileRepo Zipping Started....")

        result = self._executefilerepo(args)

        self.__console_msg(result, f'{build_server["HOSTNAME"]} AWC FileRepo Zipped {_zip_path}')
        
        return result
        

    def fileRepoCopy(self):

        if 'executeTargets' in self.__properties[self.__target]:

            return self._executeCombineTargets()

        else:

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 

            if len(_execute_servers) == 0:
            
                self.log.info("AWC FileRepo Copy Skipped")
                
                return self._processes     

            _build_server = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['buildServer'])

            for index, build_server_info in enumerate(_build_server):
                    
                __ssh_command = self.__environment_provider.get_ssh_command(build_server_info)
                
                self.log.info("Requesting to Stop the Process Manager")  
                self.servicestop('AWC_Micro', build_server_info['NODE'])

                _zip_status = self._zipFileRepo(build_server_info)
                
                
                if _zip_status == 0:                   

                    """ File Reposistory zip"""
                  
                    for index, server_info in enumerate(_execute_servers):
                    
                        _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(build_server_info,True))
                
                        _driveletter = server_info['AWCTRANSIT_PATH'].split(':')[0]
                        
                        _rootpath = server_info['SMO_SHARE_ROOT_PATH']
                        
                        _sourcepath = build_server_info['FILE_REPO'].split(os.sep)                        
                        _sourcepath.remove(os.path.basename(build_server_info['FILE_REPO']))                        
                        _sourcepath = os.path.normpath(os.path.join(*_sourcepath)) 

                        self._parallel = True
                        
                        self.log.info(f"FileRepo Copying into {server_info['AWCTRANSIT_PATH']}")
                        
                        result = _scp_without_ssh.copy_to_mount_win(_sourcepath, os.path.join(server_info['AWCTRANSIT_PATH'], self.__environment_provider.get_environment_name(), server_info['ALIASNAME']), os.path.basename(build_server_info['FILE_REPO'])+'.7z', _driveletter, _rootpath, build_server_info['MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH'],server_info['DOMAIN'] ,server_info['USERNAME'] , build_server_info['FILE_REPO'], server_info, True)

                        self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__module_name, 'label': f'{server_info["ALIASNAME"]} FileRepo Copy'})
                        
                    
                    if self._parallel:
                        output = [p['process'].wait() for p in self._processes]
                        for resultindex, result in enumerate(output):
                            self.__console_msg(result, self._processes[resultindex]['label'])
                    
                    """ Share location into File Reposistory location"""
                    self._processes = []
                    for index, server_info in enumerate(_execute_servers):
                    
                        _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info,True))
                    
                        self._parallel = True
                    
                        self.log.info(f"{os.path.join(server_info['AWCTRANSIT_PATH'], self.__environment_provider.get_environment_name(), server_info['ALIASNAME'])} into {server_info['FILE_REPO']}")
                    
                        _sourcepath = os.path.join(server_info['AWCTRANSIT_PATH'], self.__environment_provider.get_environment_name(), server_info['ALIASNAME'])
                        
                        _driveletter = server_info['AWCTRANSIT_PATH'].split(':')[0]
                        
                        _rootpath = server_info['SMO_SHARE_ROOT_PATH']
                        
                        _targetpath = server_info['FILE_REPO'].split(os.sep)                        
                        _targetpath.remove(os.path.basename(server_info['FILE_REPO']))                        
                        _targetpath = os.path.normpath(os.path.join(*_targetpath)) 
                        
                        result = _scp_without_ssh.copy_to_mount_win(_sourcepath, _targetpath, os.path.basename(server_info['FILE_REPO'])+'.7z', _driveletter, _rootpath, server_info['MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH'],server_info['DOMAIN'] ,server_info['USERNAME'],_sourcepath, server_info, True)
                        
                        self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__module_name, 'label': f'{_sourcepath} FileRepo Copy into {_targetpath}'})
                        
                    if self._parallel:
                        output = [p['process'].wait() for p in self._processes]
                        for resultindex, result in enumerate(output):
                            self.__console_msg(result, self._processes[resultindex]['label'])
                    
                    """ Extract zip file"""
                    self._processes = []
                    for index, server_info in enumerate(_execute_servers):
                    
                        _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info,True))
                    
                        self._parallel = True
                    
                        self.log.info(f"Extracting {os.path.basename(server_info['FILE_REPO'])+'.7z'} into {server_info['FILE_REPO']}")
                    
                        _sourcepath = server_info['FILE_REPO'].split(os.sep)
                        _sourcepath.remove(os.path.basename(server_info['FILE_REPO']))
                        _targetpath = os.path.normpath(os.path.join(*_sourcepath))
                        
                        _sourcepath = os.path.normpath(os.path.join(*_sourcepath))
                        
                        _driveletter = server_info['AWCTRANSIT_PATH'].split(':')[0]
                        
                        _rootpath = server_info['SMO_SHARE_ROOT_PATH']                       
                         
                        
                        result = _scp_without_ssh.unzip_to_mount_win(_sourcepath, _targetpath, os.path.basename(server_info['FILE_REPO'])+'.7z', _driveletter, _rootpath, server_info['MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH'],server_info['DOMAIN'] ,server_info['USERNAME'],_sourcepath, server_info, True)
                        
                        self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__module_name, 'label': f'{server_info["ALIASNAME"]} FileRepo Copy'})
                        
                    if self._parallel:
                        output = [p['process'].wait() for p in self._processes]
                        for resultindex, result in enumerate(output):
                            self.__console_msg(result, self._processes[resultindex]['label'])
                    self._processes = []        
                    for index, server_info in enumerate(_execute_servers):        
                        self.log.info("Requesting to Stop the Teamcenter Process Manager")
                        self.servicestop('AWC_REMOTE', server_info['NODE'])
                        if 'temp_paths' in self.__properties[self.__target]:
                            temp_path_list = self.__properties[self.__target]['temp_paths']
                            
                            clean_temp_result = self.clear_temp_dirs(temp_path_list,server_info)
                            
                            if clean_temp_result == 0:
                                self.log.info('Temporary Directories are deleted successfully.')
                                
                            self._processes.append({'NODE':server_info['NODE'],'process': clean_temp_result,'module': self.__module_label, 'package_id': '', 'label': f"Temp Directories Delete"})
                            self.__console_msg(clean_temp_result, f'AWC {server_info["AWCTRANSIT_PATH"]} to {server_info["FILE_REPO"]}')
                                
                        else:
                            self.log.warning('Temporary path not configured in deploy targets')
                            self.__console_msg(0, f'AWC {server_info["AWCTRANSIT_PATH"]} to {server_info["FILE_REPO"]}')
                            self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': '', 'label': f"Temp Directories Delete"})

            return self._processes    
            

    def deltaindex(self):

        """Command : awindexerutil -u=infodba -p=infodba -g=dba -delta"""
        
        self.log.info(f"AWSolrIndexing deltaindex")

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        for index, server_info in enumerate(_execute_servers): 

            __ssh_command = self.__environment_provider.get_ssh_command(server_info)

            self.log.info("Requesting to Stop the Services")
            self.__console_msg(self.servicestop('SOLR'),'Solr Stopped')

            args = [__ssh_command]
            args.append('cd '+os.path.join(server_info['TC_ROOT'],server_info['SOLR_VERSION'])+' && '+'./TcSchemaToSolrSchemaTransform.sh')
            args = ' '.join([str(elem) for elem in args])
            result = self._execute(args)

            if result == 0:
                self.log.info(f"Requesting to Start the Services")
                self.__console_msg(self.servicestart('SOLR'),'Solr Started')
                        
            command = self.__build_arguments(server_info)

            self.log.info(f"Execution Command: {command}")
            result = self._execute(command)
            self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': '', 'label': "AWSolrIndexing Utility"})
            
            if not self._parallel:
                self.__console_msg(result, "AWSolrIndexing")
            
            else:
                self.log.error(f"{self.__target} Failed to execute. Please check utiity configuration file.")
        
        return self._processes

    def fullindex(self):

        """Command : awindexerutil -u=infodba -p=infodba -g=dba -delta"""
        
        self.log.info(f"AWSolrIndexing fullindex")

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        for index, server_info in enumerate(_execute_servers): 

            __ssh_command = self.__environment_provider.get_ssh_command(server_info)


            self.log.info("Requesting to Stop the Services")

            self.__console_msg(self.servicestop('SOLR'),'Solr Stopped')

            args = [__ssh_command]
            args.append('cd '+os.path.join(server_info['TC_ROOT'],server_info['SOLR_VERSION'])+' && '+'./TcSchemaToSolrSchemaTransform.sh')
            args = ' '.join([str(elem) for elem in args])
            result = self._execute(args)

            if result==0:
                self.log.info(f"Requesting to Start the Services")
                self.__console_msg(self.servicestart('SOLR'),'Solr Started')
                        
            command = self.__build_arguments(server_info)

            self.log.info(f"Execution Command: {command}")
            result = self._execute(command)

            self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': '', 'label': "AWSolrIndexing Utility"})
            
            if not self._parallel:
                self.__console_msg(result, "AWSolrIndexing")
            
            else:
                self.log.error(f"{self.__target} Failed to execute. Please check utiity configuration file.")
        
        return self._processes


    def __build_arguments(self, server_info):
            
        __ssh_command = self.__environment_provider.get_ssh_command(server_info)
        
        if __ssh_command == '':
            self.__remote_execution = False  
        else:
            self.__remote_execution = True

        if self.__remote_execution:
            args = [__ssh_command]
            
        else:
            args = []
        if self.__environment_provider.get_property_validation('command', self.__properties[self.__target]):
            args.append(self.__properties[self.__target]['command'])
            
        # Get Infodba Credentials
        args.extend(self.__environment_provider.get_infodba_credentials(server_info))

        # Get Group Name
        args.extend(self.__environment_provider.get_group(server_info))
          
        args.append('-delta')

        return ' '.join([str(elem) for elem in args])

    def deploy(self):
        return self._executeCombineTargets()

    def _executeCombineTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__target).split(',')):
                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name
                if dynamicExecutor.get_sub_module_name():    
                    _processesResult = getattr(AWC, dynamicExecutor.get_sub_module_name())(self)
                else:
                    _processesResult = dynamicExecutor.run_module()
                self._processesResult = self._processesResult + _processesResult  
            return self._processesResult
        except Exception as exp:
            self.log.error(exp)

    def servicestop(self, action, execute_server=''):
        dynamicExecutor = DynamicExecutor(self.__arguments)
        for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Stop', action, execute_server):
            if not serviceData['pid']:
                self.log.info(f"{serviceData['module']} - Stopped")
            else:
                self.log.error(f"{serviceData['module']} not Stopped. Please Check the Teamcenter Process Manager")
                exit()
    def servicestart(self, action, execute_server=''):
        dynamicExecutor = DynamicExecutor(self.__arguments)
        for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Start', action, execute_server):
            if serviceData['pid']:
                self.log.info(f"{serviceData['module']} - Started")
            else:
                self.log.error(f"{serviceData['module']} not Started. Please Check the Teamcenter Process Manager")
                exit()

    def clear_temp_dirs(self, location_list:list, server_info):
        try:
            _result = 1
            self.log.info('Temporary Directories Delete - Started')
            _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True)) 
            _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info)) 
            __ssh_command = self.__environment_provider.get_ssh_command(server_info)
            _is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            lines = []
            for temp_dir in location_list:
                temp_dir = temp_dir.replace('$USERNAME',server_info['USERNAME'])
                check_path_exists = _scp_with_ssh.check_dir_to_remote(_is_windows,temp_dir)
                if check_path_exists:
                    lines.append(f'Remove-Item -Path "{temp_dir}" -Recurse -Force -ErrorAction SilentlyContinue -ErrorVariable +Errors;if ($Errors) {{ Write-Host {temp_dir} }}')
                else:
                    self.log.warning(f'{temp_dir} Directory does not exists to delete')
            if len(lines):
                file  = tempfile.NamedTemporaryFile('w+t')
                filepath = file.name
                for line in lines:
                    self.log.debug(line)
                    file.write(line + '\n')
                file.flush()
                resultshare = _scp_without_ssh.copy_to_remote(filepath, os.path.join(server_info['DEPLOYMENT_CENTER_TEMP_DIR'],'removetempfiles.ps1'))
                if resultshare == 0:
                    args = [__ssh_command]
                    args.append('"cd '+server_info['DEPLOYMENT_CENTER_TEMP_DIR']+' && '+server_info['DEPLOYMENT_CENTER_TEMP_DIR'].split(':')[0]+':'+' && powershell '+server_info['DEPLOYMENT_CENTER_TEMP_DIR']+'/removetempfiles.ps1"')
                    args = ' '.join([str(elem) for elem in args])
                    output_result = self._execute(args)
                    output_result = [res for res in output_result if res != '']
                    if len(output_result):
                        for undeleted_path in output_result:
                            self.log.warning(f'{undeleted_path} is Not deleted...! May be the file or Directory is in Use')
                    _result = 0
                else:
                    _result = 1
            else:
                _result = 0
                self.log.warning(f'Directories does not exists to delete')
        except Exception as exp:
            self.log.error(exp)
            _result = 1
        return _result


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
                        _processesResult = getattr(AWC, dynamicExecutor.get_sub_module_name())(self)
                    else:
                        _processesResult = dynamicExecutor.run_module()   
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult             
        except Exception as exp:
            self.log.error(exp)
            
   
    def __console_msg(self, result, action_msg):
        
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')
                

    def _execute(self, command):
        """
         Used to process services/command
        """
        process = Process(command)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        process.execute()
        return process.get_out_lines()
    
    def _executefilerepo(self, command, path=''):
        """
         Used to process services/command
        """
        process = Process(command, path)
        process.set_stderr(False)
        return process.execute()
