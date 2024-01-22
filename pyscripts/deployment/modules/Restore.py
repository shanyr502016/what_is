"""
Restore deployment activities
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
import os
from corelib.BackupUtilities import BackupUtilities
from corelib.DateTime import DateTime
from corelib.SCP import SCP


class Restore(Loggable):
    
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
        Resume State Skip
        """
        self._resumestate = args._arguments.resumestate
        
        """
        Scope and target setup based on configuration
        """   
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
            
        self._backupUtilities = BackupUtilities(self.__environment_provider)
        
        self._processes = []
        self._parallel = False
        self._overallrestore = False
        self._processesLabel = []

    
    def default(self):
                
        self.log.info("Restore All")
        self._parallel = True
        self._overallrestore = True
        self._executeTargets() 
        self._execute_process()  



    def web(self):

        self.log.info("web Restore Executed...")

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
        
        for index, server_info in enumerate(_execute_servers):

            _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

            if 'WEB_PATH' in server_info and (server_info['WEB_PATH'] and server_info['WEB_PATH'].strip()): 

                _target_dir = server_info['WEB_PATH']

                self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
            else:
                self.log.warning('web Backup Directory is not present in environment configuration! Restore Skipped.')


    def warcreationsetup(self):

        self.log.info("WEBSETUP Restore Executed...")

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
        
        for index, server_info in enumerate(_execute_servers):

            _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

            if 'WEBSETUP' in server_info and (server_info['WEBSETUP'] and server_info['WEBSETUP'].strip()): 

                _target_dir = server_info['WEBSETUP']

                self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
            else:
                self.log.warning('WEBSETUP Restore Directory is not present in environment configuration! Restore Skipped.')



    def tcdata(self):  

        self.log.info("tcdata Restore Executed...")

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
        
        for index, server_info in enumerate(_execute_servers):

            _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

            if 'TC_DATA' in server_info and (server_info['TC_DATA'] and server_info['TC_DATA'].strip()): 

                _target_dir = server_info['TC_DATA']

                self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
            else:
                self.log.warning('tc_data Backup Directory is not present in environment configuration! Restore Skipped.')
        

    def tcprofilevars(self): 

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])    
        
        for index, server_info in enumerate(_execute_servers):

            _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())
            
            if 'TC_DATA' in server_info:

                _target_dir = server_info['TC_DATA']

                _is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])

                _ssh_command = self.__environment_provider.get_ssh_command(server_info)

                for tc_profilevars_file in os.listdir(_backup_source_path):

                    if tc_profilevars_file.startswith('tc_profilevars'):

                        _rename_file_name = SCP(_ssh_command).rename_file_to_remote(_is_windows,os.path.join(_target_dir,tc_profilevars_file))

                        _copytoresult = SCP('').copy_to_local(os.path.join(_backup_source_path,tc_profilevars_file), _target_dir, self._parallel)

                        self._processes.append({'NODE':server_info['NODE'],'process':_copytoresult,'module':self.__target, 'label': f"{server_info['HOSTNAME']} - tcprofilevars - {self.__target}"})

                        self._processesLabel.append('TC_Profilevars Restore')

                        if not self._parallel:
                            self.__console_msg( _copytoresult, 'TC_Profilevars Restore')

            else:
                self.log.warning('TC_DATA not present in environment configuration! Restore Skipped.')    
                

    def tcroot(self):

        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else: 
            self.log.info("tcroot Restore Executed...")

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
            
            for index, server_info in enumerate(_execute_servers):

                _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

                if 'TC_ROOT' in server_info and (server_info['TC_ROOT'] and server_info['TC_ROOT'].strip()): 

                    _target_dir = server_info['TC_ROOT']

                    self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
                else:
                    self.log.warning('tcroot Backup Directory is not present in environment configuration! Restore Skipped.')


            
    def volumes_dba(self):   
                
        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else:  
            self.log.info("volumes_dba Restore Executed...")

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
            
            for index, server_info in enumerate(_execute_servers):

                _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

                if 'VOLUMES_DBA' in server_info and (server_info['VOLUMES_DBA'] and server_info['VOLUMES_DBA'].strip()): 

                    _target_dir = server_info['VOLUMES_DBA']

                    self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
                else:
                    self.log.warning('Volumes DBA Backup Directory is not present in environment configuration! Restore Skipped.')
 


    def volumes_all(self):

        self.log.info("volumes_all Restore Executed...")

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
        
        for index, server_info in enumerate(_execute_servers):

            _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

            if 'VOLUMES' in server_info and (server_info['VOLUMES'] and server_info['VOLUMES'].strip()): 

                _target_dir = server_info['VOLUMES']

                self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
            else:
                self.log.warning('volumes_all Backup Directory is not present in environment configuration! Restore Skipped.')
 
                
            
    def deploymentcenter(self):

        self.log.info("dispatcherroot Restore Executed...")

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
        
        for index, server_info in enumerate(_execute_servers):

            _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

            if 'DEPLOYMENT_CENTER_PATH' in server_info and (server_info['DEPLOYMENT_CENTER_PATH'] and server_info['DEPLOYMENT_CENTER_PATH'].strip()): 

                _target_dir = server_info['DEPLOYMENT_CENTER_PATH']

                self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
            else:
                self.log.warning('Deployment Center Backup Directory is not present in environment configuration! Restore Skipped.')



    def dc(self):

        self.log.info("dispatcherroot Restore Executed...")

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
        
        for index, server_info in enumerate(_execute_servers):

            _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

            if 'DEPLOYMENT_CENTER_DC_PATH' in server_info and (server_info['DEPLOYMENT_CENTER_DC_PATH'] and server_info['DEPLOYMENT_CENTER_DC_PATH'].strip()): 

                _target_dir = server_info['DEPLOYMENT_CENTER_DC_PATH']

                self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
            else:
                self.log.warning('DC Backup Directory is not present in environment configuration! Restore Skipped.')



    def dispatcherdata(self):                
        
        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else: 

            self.log.info("dispatcherdata Restore Executed...")

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
            
            for index, server_info in enumerate(_execute_servers):

                _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

                if 'DISPATCHER_DATA_PATH' in server_info and (server_info['DISPATCHER_DATA_PATH'] and server_info['DISPATCHER_DATA_PATH'].strip()): 

                    _target_dir = server_info['DISPATCHER_DATA_PATH']

                    self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
                else:
                    self.log.warning('DISPATCHER_DATA Directory is not present in environment configuration! Restore Skipped.')

              

    def dispatcher(self):

        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else:

            self.log.info("dispatcher Restore Executed...")

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
            
            for index, server_info in enumerate(_execute_servers):

                _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

                if 'DISPATCHER_PATH' in server_info and (server_info['DISPATCHER_PATH'] and server_info['DISPATCHER_PATH'].strip()): 

                    _target_dir = server_info['DISPATCHER_PATH']

                    self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
                else:
                    self.log.warning('DISPATCHER Directory is not present in environment configuration! Restore Skipped.')
            
 


    def dispatcherroot(self):
                      
        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else: 
            self.log.info("dispatcherroot Restore Executed...")

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
            
            for index, server_info in enumerate(_execute_servers):

                _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

                if 'DISPATCHER_ROOT_PATH' in server_info and (server_info['DISPATCHER_ROOT_PATH'] and server_info['DISPATCHER_ROOT_PATH'].strip()): 

                    _target_dir = server_info['DISPATCHER_ROOT_PATH']

                    self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
                else:
                    self.log.warning('DISPATCHER_ROOT Directory is not present in environment configuration! Restore Skipped.')


    def awc(self):
        
        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else: 
            self.log.info("awc Restore Executed...")

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
            
            for index, server_info in enumerate(_execute_servers):

                _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

                if 'AWC_PATH' in server_info and (server_info['AWC_PATH'] and server_info['AWC_PATH'].strip()): 

                    _target_dir = server_info['AWC_PATH']

                    self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
                else:
                    self.log.warning('AWC Backup Directory is not present in environment configuration! Restore Skipped.')

            
            
    def T4S(self):   

        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else: 
            self.log.info("T4S Restore Executed...") 

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
            
            for index, server_info in enumerate(_execute_servers):

                _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

                if 'T4S' in server_info and (server_info['T4S'] and server_info['T4S'].strip()): 

                    _target_dir = server_info['T4S']

                    self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
                else:
                    self.log.warning('T4S Backup Directory is not present in environment configuration! Restore Skipped.')


            
            
    def SSO_WebTier(self):

        self.log.info("SSO_WebTier Restore Executed...") 

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
        
        for index, server_info in enumerate(_execute_servers):

            _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

            if 'SSO_WEBTIER' in server_info and (server_info['SSO_WEBTIER'] and server_info['SSO_WEBTIER'].strip()): 

                _target_dir = server_info['SSO_WEBTIER']

                self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
            else:
                self.log.warning('SSO_WEBTIER Directory is not present in environment configuration! Restore Skipped.')

            
    def cpm(self):                
        
        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else: 
            self.log.info("cpm Restore Executed...")

            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
            
            for index, server_info in enumerate(_execute_servers):

                _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())

                if 'CPM' in server_info and (server_info['CPM'] and server_info['CPM'].strip()): 

                    _target_dir = server_info['CPM']

                    self._build_arguments(_backup_source_path,os.path.basename(_target_dir),_target_dir,server_info,self.__target)
                else:
                    self.log.warning('cpm Backup Directory is not present in environment configuration! Restore Skipped.')

    def adminData(self):
        '''
        admin_data_import -u=*** -p=*** -g=dba -inputPackage= -adminDataTypes=Organization -dryrun
        '''
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        for index, server_info in enumerate(_execute_servers):
            try:
                __ssh_command = self.__environment_provider.get_ssh_command(server_info)

                if 'command' in self.__properties[self.__target]:
                    _command = self.__properties[self.__target]['command']
                    _backup_source_path = os.path.join(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'].lower())
                    if __ssh_command == '':
                        args = []
                    else:
                        args = [__ssh_command]
                    args.extend([_command])
                    args.extend(['-u=' + server_info['TC_USER']])
                    args.extend(['-pf=' + server_info['TC_PWF'] ])
                    args.extend(['-g=' + server_info['TC_GROUP']])
                    args.extend(['-inputPackage='+ os.path.join(_backup_source_path,'adminData.zip')])
                    args.extend(['-adminDataTypes=Organization'])
                    args.extend(['-dryrun'])
                    args = ' '.join([str(elem) for elem in args])
                    if self._parallel:
                        result = self._execute(args, _backup_source_path)
                        self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__target, 'label': f"{server_info['HOSTNAME']} - admin_data_import - {self.__target}"})
                        self._processesLabel.append('Admin Data import')
                    else:
                        self.log.info("Please wait while taking few minutes...")
                        result = self._execute(args, _backup_source_path)
                        self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__target, 'label': f"{server_info['HOSTNAME']} - admin_data_import - {self.__target}"})
                        self.__console_msg(result, 'Admin Data import')
                else:
                    self.log.warning(f"Command is not present in Properties configuration! AdminData Restore Skipped.")

            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__target, 'label': f"{server_info['HOSTNAME']} - admin_data_import - {self.__target}"})

    def infodba(self):
        self.log.info("Calling infodba...")
  

    def pooldb(self):
        self.log.info("Calling pooldb...")
        

    def Preferences(self): 
        self.log.info("Calling Preferences...")


    def nosso(self):
        self.log.info("NoSSO Server Restore")
        self._parallel = True
        self._overallrestore = True
        self._executeCombineTargets() 
        self._execute_process()  

    def mig(self):
        self.log.info("Migration Server Restore")
        self._parallel = True
        self._overallrestore = True
        self._executeCombineTargets()
        self._execute_process()  

    def corp(self):
        self.log.info("Corporate Server Restore")
        self._parallel = True
        self._overallrestore = True
        self._executeCombineTargets()
        self._execute_process()  

    def db(self):
        self._parallel = False
        self.log.info("Database Restore")
        try:
            self.log.info('DB ')
        except Exception as exp:
            self.log.error(exp)

            
    def _getServerNameByAlias(self,aliasname):
        for servername, properties in self.__environment.items():            
            if servername != 'ENVIRONMENT':                
                for values in properties:
                    if 'ALIASNAME' in values:                       
                        if values['ALIASNAME'].__ne__('') and values['ALIASNAME'].split('.')[0] == aliasname:
                            self.log.info(servername)
                            return servername

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
        

    def _build_arguments(self,source_path,zip_file,dest_path,server_info,module_name):

        is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])

        _ssh_command = self.__environment_provider.get_ssh_command(server_info)

        _lisf_of_files = SCP(_ssh_command).get_files_from_remote(source_path,is_windows)

        if _ssh_command == '':
            args = []
        else:
            args = [_ssh_command]

        if len(_lisf_of_files) and (zip_file in [i.split('.')[0] for i in _lisf_of_files]):

            _rename_folder_name = SCP(_ssh_command).rename_dir_to_remote(is_windows,dest_path,dest_path+'_'+DateTime.get_datetime("%d%m%Y%H%M%S"))

            _create_dest_folder = SCP(_ssh_command).create_dir_to_remote(is_windows,dest_path)

            file_name = _lisf_of_files[[i.split('.')[0] for i in _lisf_of_files].index(zip_file)]

            if file_name.startswith(zip_file):
                if is_windows :
                    _src_file = os.path.join(source_path,file_name)
                    args.append(f'{server_info["7ZIP_PATH"]} x -aoa {_src_file} -o{dest_path}/..')
                else:
                    _src_file = os.path.join(source_path,file_name)
                    _extension = file_name.split('.')[-1]
                    if _extension == 'gz':
                        args.append(f'tar -zxf  {_src_file} -C {dest_path}')

                    elif _extension == 'zip':
                        args.append(f'unzip -o {_src_file} -d {dest_path}')
                args = ' '.join([str(elem) for elem in args])
                if self._parallel:
                    result = self._execute(args, dest_path)
                    self._processes.append({'NODE':server_info['NODE'],'process':result,'module':module_name, 'label': f"{server_info['HOSTNAME']} - {dest_path} - {module_name}"})
                    self._processesLabel.append(zip_file)
                else:
                    self.log.info("Please wait while taking 10 to 15 minutes...")
                    result = self._execute(args, dest_path)
                    self._processes.append({'NODE':server_info['NODE'],'process':result,'module':module_name, 'label': f"{server_info['HOSTNAME']} - {dest_path} - {module_name}"})
                    self.__console_msg(result, zip_file)   

        else:
            self.log.warning(f'{source_path} is not contains {zip_file} zip file')
            self._processes.append({'NODE':server_info['NODE'],'process':1,'module':module_name, 'label': f"{server_info['HOSTNAME']} - {dest_path} - {module_name}"})


    def _executeCombineTargets(self):
        try:
            if self._overallrestore:
                _targetList = self.__environment_provider.resume_state_execution_read(self._tcpackage_id,self.__target,self._resumestate)
            else:
                _targetList = self.__environment_provider.get_execute_targets(self.__target).split(',')

            for threadcount, targets in enumerate(_targetList):
                if self._overallrestore:
                    server_info = self.__environment_provider.update_serverinfo_data(_targetList[targets],self.__arguments)                    
                    if 'executionServer' in self.__arguments._properties[targets]:
                        self.__arguments._environment[self.__arguments._properties[targets]['executionServer']] = server_info

                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_environment(self.__arguments._environment)
                dynamicExecutor.set_module_instance(targets) # module instance name
                if dynamicExecutor.get_sub_module_name():    
                    getattr(Restore, dynamicExecutor.get_sub_module_name())(self)
                else:
                    dynamicExecutor.run_module() 

            if self._parallel and not self._overallrestore:
                self.log.info("Please wait while taking 10 to 15 minutes...")
                output = [self.__environment_provider._verbose_result(p['process'],True) for p in self._processes]  
                for resultindex, result in enumerate(output):
                    self.__console_msg(result, self._processes[resultindex]['label'])
        except Exception as exp:
            self.log.error(exp)


        
    def _executeTargets(self):

        try:
            _targetList = self.__environment_provider.resume_state_execution_read(self._tcpackage_id,self.__module_name,self._resumestate)
            
            for threadcount, targets in enumerate(_targetList): 
                server_info = self.__environment_provider.update_serverinfo_data(_targetList[targets],self.__arguments)
                if 'executionServer' in self.__arguments._properties[targets]:
                    self.__arguments._environment[self.__arguments._properties[targets]['executionServer']] = server_info
                # Execute with multiple targets
                if not self.__sub_module_name:
                    self.__target = targets
                    dynamicExecutor = DynamicExecutor(self.__arguments)   
                    dynamicExecutor.set_environment(self.__arguments._environment)
                    dynamicExecutor.set_module_instance(targets) # module instance name                    
                    if dynamicExecutor.get_sub_module_name():                        
                        getattr(Restore, dynamicExecutor.get_sub_module_name())(self)
                    else:
                        dynamicExecutor.run_module()                     
        except Exception as exp:
            self.log.error(exp)

    def _execute_process(self):

        self.log.info("Please wait while taking 10 to 15 minutes...")

        def _parallel_result(process, action_msg):
            if len(self.__sub_module_name):
                module_name = self.__module_name +'.'+ '.'.join(self.__sub_module_name)
                result = self.__environment_provider.resume_state_execution_write(self._tcpackage_id,module_name,process['module'],[process])
            else:
                result = self.__environment_provider.resume_state_execution_write(self._tcpackage_id,self.__module_name,process['module'],[process])
            self.__console_msg(result,action_msg)

        process = Process('')
        process.thread_execute(self._processes, _parallel_result)
           
    def _execute(self, command, path='', stderr = True,stdout = False):
        """
         Used to process services/command
        """
        process = Process(command)
        process.set_parallel_execution(self._parallel)
        process.set_stderr(stderr)
        return process.execute()


    def __console_msg(self, result, action_msg):
        if result == 0:
            Loggable.log_success(self, f"{action_msg} Successfully.")
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')
