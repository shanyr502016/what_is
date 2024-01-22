"""
DCScript deployment activities
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from deployment.lib.DCScriptUtilities import DCScriptUtilities
from corelib.Encryption import Encryption
from corelib.SCP import SCP
from corelib.File import File, Directory
import os
from corelib.Constants import Constants
import time
import sys




class DCScript(Loggable):
    
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
        """
        Resume State Skip
        """
        self._resumestate = args._arguments.resumestate

        self.__dcencryptedPassword = None

        self.__exportFile = self.__environment_provider.get_environment_name() + '_quick_deploy.xml'

        self.__share_do_not_modify_dir = os.path.join(self.__environment_provider.get_share_root_path(), 'dita_share_do_not_modify')
        
        self._dcscriptUtilities = DCScriptUtilities(self.__environment_provider)
        
        self._bmideInfo = None
        
        self._encryption = Encryption()

        self._directory = Directory()

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel 


    def default(self):
                
        self.log.info("Starting DCScript Deployment")

        return self._executeTargets()  

    def encryption(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        _dc_quick_deploy_command = self.__properties[self.__target]['dc_quick_deploy_command']

        for index, server_info in enumerate(_execute_servers):

            _dcScriptsPath = server_info['DEPLOYMENT_CENTER_QUICKDEPLOY_PATH']

            self.log.info(f"Exporting ENVXML from Deployment Center [{server_info['HOSTNAME']}]")

            dcCommand = self._dcscriptUtilities.getDCCommand(server_info, _dcScriptsPath, _dc_quick_deploy_command)

            self._dcscriptUtilities.getEncryptedPasswordArgs(server_info, dcCommand)

    def generateENVQD(self):
                    
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
            
        for index, server_info in enumerate(_execute_servers):   
            try:                
                if self._dcscriptUtilities.createQuickDeployXML(self.__share_do_not_modify_dir, self.__exportFile, self.__security, self._tcpackage_id, self.__properties[self.__target]['location_in_package']):
                    self.__console_msg(0, 'Create QuickDeploy XML')
                    _copyENVXMLtoDCLocationResult = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(os.path.join(self.__share_do_not_modify_dir,self.__exportFile), os.path.join(server_info['EXPORT_FILE_PATH'], self.__exportFile) )
                            
                    if _copyENVXMLtoDCLocationResult == 0:
                        self.__console_msg(_copyENVXMLtoDCLocationResult, f"Replaced the Environment XML into Deployment center location {server_info['EXPORT_FILE_PATH']}")
                        self._processes.append({'NODE':server_info['NODE'],'process': _copyENVXMLtoDCLocationResult,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
                    else:
                        self.log.error("Copy Updated Environment File into Deployment center location. DCScript Deployment is Failure")
                        self._processes.append({'NODE':server_info['NODE'],'process': _copyENVXMLtoDCLocationResult,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"}) 
                else:
                    self.log.error('Credentials Updates Failed. DCScript Deployment is Failure')
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"}) 
            
            except Exception as exp:        
                self.log.error(f'ExportENVQD Error: {exp}')
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"})
        return self._processes
    
    def exportENVQD(self):
                    
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
            
        for index, server_info in enumerate(_execute_servers):   
            try:                
                if self._dcscriptUtilities.createQuickDeployXML(self.__share_do_not_modify_dir, self.__exportFile, self.__security, self._tcpackage_id, self.__properties[self.__target]['location_in_package']):
                    self.__console_msg(0, 'Create QuickDeploy XML')
                    _copyENVXMLtoDCLocationResult = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(os.path.join(self.__share_do_not_modify_dir,self.__exportFile), os.path.join(server_info['EXPORT_FILE_PATH'], self.__exportFile) )
                            
                    if _copyENVXMLtoDCLocationResult == 0:
                        self.__console_msg(_copyENVXMLtoDCLocationResult, f"Replaced the Environment XML into Deployment center location {server_info['EXPORT_FILE_PATH']}")
                        self._processes.append({'NODE':server_info['NODE'],'process': _copyENVXMLtoDCLocationResult,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
                    else:
                        self.log.error("Copy Updated Environment File into Deployment center location. DCScript Deployment is Failure")
                        self._processes.append({'NODE':server_info['NODE'],'process': _copyENVXMLtoDCLocationResult,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"}) 
                else:
                    self.log.error('Credentials Updates Failed. DCScript Deployment is Failure')
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"}) 
            
            except Exception as exp:        
                self.log.error(f'ExportENVQD Error: {exp}')
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"})
        return self._processes
        


    def exportENVXML(self):
                    
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        # deployment center quick deploy from deploy_targets.json
        _dc_quick_deploy_command = self.__properties[self.__target]['dc_quick_deploy_command']

        # self._dcscriptUtilities.getEncryptedPasswordArgs(server_info, dcCommand)
            
        for index, server_info in enumerate(_execute_servers):
            try:
                _dcScriptsPath = server_info['DEPLOYMENT_CENTER_QUICKDEPLOY_PATH']

                self.log.info(f"Exporting ENVXML from Deployment Center [{server_info['HOSTNAME']}]")

                dcCommand = self._dcscriptUtilities.getDCCommand(server_info, _dcScriptsPath, _dc_quick_deploy_command)  

                exportenvCommand = self._dcscriptUtilities.getDCExportENVCommand(server_info, dcCommand, self.__exportFile)


                self.log.info("Requesting to Start the DC Service")
                dynamicExecutor = DynamicExecutor(self.__arguments)
                for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Start', 'DC_ALL'):
                    if serviceData['pid']:
                        self.log.info(f"{serviceData['module']} - Started")
                    else:
                        self.log.error(f"{serviceData['module']} not Started. Please Check the DC Service")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"}) 
                        return self._processes
                self.__environment_provider.wait_execute(180)

                # Execute the Exported the ENV XML File 
                result = self._execute(exportenvCommand, _dcScriptsPath) 

                self.__console_msg(result, f"Deployment Center is exported the Environment File into {os.path.join(server_info['EXPORT_FILE_PATH'], self.__exportFile)}") 

                if result == 0:
    
                    self.log.info(f'Copy the Environment XML File into SHARE Location {self.__share_do_not_modify_dir}')

                    _copyExportedXMLToShareResult = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_local(os.path.join(server_info['EXPORT_FILE_PATH'],self.__exportFile ), self.__share_do_not_modify_dir)    
                    
                    if _copyExportedXMLToShareResult == 0:

                        self.__console_msg(_copyExportedXMLToShareResult, 'Copied Environment File')

                        # Take the Exported ENVXML into Share location for Updated Values Purpose
                        if self._dcscriptUtilities.updateSecurityCredentials(self.__share_do_not_modify_dir, self.__exportFile, self.__security, self._tcpackage_id, self.__properties[self.__target]['location_in_package']):
                            self.__console_msg(0, 'Updated the Credentials')
                            
                            _copyENVXMLtoDCLocationResult = SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(os.path.join(self.__share_do_not_modify_dir,self.__exportFile), os.path.join(server_info['EXPORT_FILE_PATH'], self.__exportFile) )
                            
                            if _copyENVXMLtoDCLocationResult == 0:
                                self.__console_msg(_copyENVXMLtoDCLocationResult, f"Replaced the Environment XML into Deployment center location {server_info['EXPORT_FILE_PATH']}")
                                self._processes.append({'NODE':server_info['NODE'],'process': _copyENVXMLtoDCLocationResult,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
                            else:
                                self.log.error("Copy Updated Environment File into Deployment center location. DCScript Deployment is Failure")
                                self._processes.append({'NODE':server_info['NODE'],'process': _copyENVXMLtoDCLocationResult,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"}) 
                        else:
                            self.log.error('Credentials Updates Failed. DCScript Deployment is Failure')
                            self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"}) 
                    else:
                        self.log.error("System can't Copy Exported XML into Share Location. DCScript Deployment is Failure")
                        self._processes.append({'NODE':server_info['NODE'],'process': _copyExportedXMLToShareResult,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"})

                else:
                    self.log.warning("Please check status of Deployment Center Services")
                    self.log.error("Deployment Center Export Enviroment is Failed. DCScript Deployment is Failure")
                    self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"})
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript ExportENVXML"})
        return self._processes

    

    def generateDeployScripts(self):
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])  

        _dc_quick_deploy_command = self.__properties[self.__target]['dc_quick_deploy_command']
        for index, server_info in enumerate(_execute_servers):
            try:
                _dcScriptsPath = server_info['DEPLOYMENT_CENTER_QUICKDEPLOY_PATH']

                _share_software_repo_targetpath = server_info['SMO_SHARE_SOFTWARE_REPO_TARGET_PATH']


                try:
                    _location_in_package_status = 0
                    for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):                                    
                        package_full_path = self.__environment_provider.get_location_in_package(tc_package_id)
                        config_file = File(package_full_path, self.__environment_provider.get_environment_name() + '_DCPackage_Generate.txt')                                    
                        config_file.write("-")
                        
                        _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                        
                        if os.path.exists(_location_in_package):

                            _location_in_package_status = _location_in_package_status + 0
                        else:
                            _location_in_package_status = _location_in_package_status + 1
                    if _location_in_package_status > 0:
                        self.log.debug(f"There is no BMIDE Package on this Deployment")
                        self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"}) 
                        return self._processes

                except Exception as e:
                    self.log.error(e)

                _copyshareSoftwareRepoResult = 1  

                self.log.info("Requesting to Stop the DC Service")                
                dynamicExecutor = DynamicExecutor(self.__arguments)
                for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Stop', 'DC'):
                    if not serviceData['pid']:
                        self.log.info(f"{serviceData['module']} - Stopped")
                    else:
                        self.log.error(f"{serviceData['module']} not Stopped. Please Check the DC Service")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"}) 
                        return self._processes
                    

                for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Stop', 'PUBLISHER'):
                    if not serviceData['pid']:
                        self.log.info(f"{serviceData['module']} - Stopped")
                    else:
                        self.log.error(f"{serviceData['module']} not Stopped. Please Check the DC Repo PUBLISHER Service")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"}) 
                        return self._processes
                    

                for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Stop', 'REPO'):
                    if not serviceData['pid']:
                        self.log.info(f"{serviceData['module']} - Stopped")
                    else:
                        self.log.error(f"{serviceData['module']} not Stopped. Please Check the DC REPO Service")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"}) 
                        return self._processes
                
                # remove lastScannedMedia.json file from Repotool location
                _lastscannnedMediaFile = os.path.join(server_info['DEPLOYMENT_CENTER_REPOTOOL_PATH'], 'lastScannedMedia.json') 

                _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))   

                _check_repo_path = _scp_with_ssh.check_dir_to_remote(self.__environment_provider.is_windows(server_info['OS_TYPE']), server_info['DEPLOYMENT_CENTER_REPOTOOL_PATH'])  
                
                if _check_repo_path:                    
                    removefile = _scp_with_ssh.rename_file_to_remote(self.__environment_provider.is_windows(server_info['OS_TYPE']),_lastscannnedMediaFile)                 
                
                # Copy Package to Software Repository
                _copyshareSoftwareRepoResult = self._dcscriptUtilities.copySoftwareRepoPackages(self._tcpackage_id, self.__properties, self.__target, _share_software_repo_targetpath, server_info)

                if _copyshareSoftwareRepoResult == 0:
                    self.log.info("Requesting to Start the DC Service")
                    for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Start', 'DC_ALL'):
                        if serviceData['pid']:
                            self.log.info(f"{serviceData['module']} - Started")
                        else:
                            self.log.error(f"{serviceData['module']} not Started. Please Check the DC Service")
                            self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"}) 
                            return self._processes


                    self.__console_msg(_copyshareSoftwareRepoResult, 'Copy the BMIDE Package into Software Repository')

                    self.log.info('Deployment Center Repo Scanning...... Please wait while')

                    self.__environment_provider.wait_execute(360)

                    self.log.info(f"Generate Deploy Scripts from Deployment Center [{server_info['HOSTNAME']}]")

                    dcCommand = self._dcscriptUtilities.getDCCommand(server_info, _dcScriptsPath, _dc_quick_deploy_command)  

                    _generateScriptsCommand = self._dcscriptUtilities.getGenerateDeployScriptCommand(server_info, dcCommand, self.__exportFile)

                    _generateScriptsResult = self._execute(_generateScriptsCommand)  

                    if _generateScriptsResult == 0:

                        _deployScriptGeneratedFolder = self._dcscriptUtilities.getdeployScriptGeneratedPath(server_info['DEPLOYMENT_CENTER_DEPLOY_SCRIPT_PATH'], self.__environment_provider.get_ssh_command(server_info), self.__environment_provider.is_windows(server_info['OS_TYPE']))
                        
                        _deployScriptGeneratedPath = os.path.join(server_info['DEPLOYMENT_CENTER_DEPLOY_SCRIPT_PATH'], _deployScriptGeneratedFolder)
                        self.__console_msg(_generateScriptsResult, f'Generated DeployScript in {_deployScriptGeneratedPath}')

                        _deployScriptGeneratedDestinationPath = os.path.join(self.__share_do_not_modify_dir, 'deploy_scripts', self.__environment_provider.get_environment_name(),_deployScriptGeneratedFolder)

                        if os.path.exists(_deployScriptGeneratedDestinationPath):
                            self._directory.removedirs(_deployScriptGeneratedDestinationPath)
                        
                        os.makedirs(_deployScriptGeneratedDestinationPath)

                        _copydeployscriptstosharelocationResult =  SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_local(_deployScriptGeneratedPath+'/*', os.path.join(self.__share_do_not_modify_dir, 'deploy_scripts' ,self.__environment_provider.get_environment_name(),_deployScriptGeneratedFolder))

                        if _copydeployscriptstosharelocationResult == 0:                           

                            try:
                                for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):                                    
                                    package_full_path = self.__environment_provider.get_location_in_package(tc_package_id)
                                    config_file = File(package_full_path, self.__environment_provider.get_environment_name() + '_DCPackage_Generate.txt')                                    
                                    config_file.write(_deployScriptGeneratedFolder)
                                    self.log.debug(f"{config_file.path} Updated")
                            except Exception as e:
                                self.log.error(e)

                            self.__console_msg(_copydeployscriptstosharelocationResult, "Copy Deploy Scripts into SHARE location Successfully! Ready to deploy the Package")
                            self._processes.append({'NODE':server_info['NODE'],'process': _copydeployscriptstosharelocationResult,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
                        else:
                            self.log.error("Copy Deploy Scripts into SHARE location Failed. Generate DCScript is Failure")
                            self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
                    else:
                        self.log.error("Generate DeployScripts Failed from Deployment Center. Generate DCScript is Failure")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})           
                else:
                    self.log.error("BMIDE Package not copied into Software Repository. Generate DCScript is Failure")
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
            
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
        return self._processes


    def PackageTransfer(self):
    
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])  
        for index, server_info in enumerate(_execute_servers):
            try:
                
                if 'foldername' in self.__arguments._arguments:                    
                    _deployScriptGeneratedFolder = self.__arguments._arguments.foldername
                else:
                    _deployScriptGeneratedFolder = self._dcscriptUtilities.getdeployScriptGeneratedPath(server_info['DEPLOYMENT_CENTER_DEPLOY_SCRIPT_PATH'], self.__environment_provider.get_ssh_command(server_info), self.__environment_provider.is_windows(server_info['OS_TYPE']))               
                _deployScriptGeneratedPath = os.path.join(server_info['DEPLOYMENT_CENTER_DEPLOY_SCRIPT_PATH'], _deployScriptGeneratedFolder)             
                _deployScriptGeneratedDestinationPath = os.path.join(self.__share_do_not_modify_dir, 'deploy_scripts', self.__environment_provider.get_environment_name(),_deployScriptGeneratedFolder)
                _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))
                _check_repo_path = _scp_with_ssh.check_dir_to_remote(self.__environment_provider.is_windows(server_info['OS_TYPE']), _deployScriptGeneratedPath) 
                
                if _check_repo_path:
                    self.__console_msg(0, f'Generated DeployScript location found in {_deployScriptGeneratedPath}')
                    if os.path.exists(_deployScriptGeneratedDestinationPath):
                        self._directory.removedirs(_deployScriptGeneratedDestinationPath)
                    os.makedirs(_deployScriptGeneratedDestinationPath)
                    _copydeployscriptstosharelocationResult =  SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_local(_deployScriptGeneratedPath+'/*', os.path.join(self.__share_do_not_modify_dir, 'deploy_scripts' ,self.__environment_provider.get_environment_name(),_deployScriptGeneratedFolder))
                    if _copydeployscriptstosharelocationResult == 0:
                        self.__console_msg(_copydeployscriptstosharelocationResult, "Copy Deploy Scripts into SHARE location Successfully! Ready to deploy the Package")
                        self._processes.append({'NODE':server_info['NODE'],'process': _copydeployscriptstosharelocationResult,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
                    else:
                        self.log.error("Copy Deploy Scripts into SHARE location Failed. Generate DCScript is Failure")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
                else: 
                    self.log.error("Deploy Scripts location is incorrect. Please enter the valid foldername")
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
                
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"})
        return self._processes
    
        

    def remotedeploy(self):
        
        self.log.debug('Remote Deploy Scripts Execution')

        _resume_state_read = self.__environment_provider.resume_state_execution_read(self._tcpackage_id,self.__target,self._resumestate)

        if not _resume_state_read:
            self._processes.append({'NODE':'','process': 0,'module': self.__module_label, 'package_id': '','label': f"DCScript Not available"})
            return self._processes

        _execute_servers = [] 
        for executionServer in _resume_state_read[self.__target]:
            _execute_servers.extend(self.__environment_provider.get_execute_server_details(executionServer))

        _command = self.__properties[self.__target]['command']

        for index, server_info in enumerate(_execute_servers):
            try:
                self.log.info("Requesting to Start the FSC_DCSCRIPT Service")
                dynamicExecutor = DynamicExecutor(self.__arguments)

                for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Start', 'DC_ALL'):
                    if serviceData['pid']:
                        self.log.info(f"{serviceData['module']} - Start")                        
                    else:
                        self.log.error(f"{serviceData['module']} not Started. Please Check the DC_ALL Service")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript Start"})
                        return self._processes


                for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Start', 'FSC_DCSCRIPT'):
                    if serviceData['pid']:
                        self.log.info(f"{serviceData['module']} - Started")
                    else:
                        self.log.error(f"{serviceData['module']} not Stopped. Please Check the FSC_DCSCRIPT Service")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript FSC Script"})
                        return self._processes                 
                

                _ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))

                # Get the share location path
                _deployScriptSRC = os.path.join(self.__share_do_not_modify_dir,'deploy_scripts', self.__environment_provider.get_environment_name())

                # Get the latest folder using timestamp
                _deployScriptGeneratedFolder = self._dcscriptUtilities.getdeployScriptGeneratedPath(_deployScriptSRC)

                 # Automation deployment with delta feature need to validate the deployment center package output folder
                try:
                    for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):                                                           
                        package_full_path = self.__environment_provider.get_location_in_package(tc_package_id)
                        self.log.debug(f'Checking the {tc_package_id} DCPackage Timestamp {_deployScriptGeneratedFolder}')
                        if os.path.exists(os.path.join(package_full_path, self.__environment_provider.get_environment_name() + '_DCPackage_Generate.txt')):
                            config_file = File(package_full_path, self.__environment_provider.get_environment_name() + '_DCPackage_Generate.txt')                                    
                            
                            deployment_center_package_folder = config_file.read_content('utf-8')

                            if deployment_center_package_folder == _deployScriptGeneratedFolder:
                                self.log.debug(f"From Generated File {deployment_center_package_folder} and Folder name {_deployScriptGeneratedFolder} is Valid. Deployment starting...")
                            else:
                                self.log.debug(f"From Generated File {deployment_center_package_folder} and Folder name {_deployScriptGeneratedFolder} is Not Valid. Deployment Skipped...")
                                self.log.warning(f"{server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME']} not available on DCScripts. Skipped Deployment")
                                self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': '','label': f"DCScript not available"})
                                return self._processes    
                                                
                except Exception as e:
                    self.log.error(e)

                if not os.path.exists(os.path.join(_deployScriptSRC, _deployScriptGeneratedFolder, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME']+'.zip')):
                    self.log.warning(f"{server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME']} not available on DCScripts. Skipped Deployment")
                    self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': '','label': f"DCScript not available"})
                    
                else:
                    self.log.info(f"DCScript FileName: {server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME']}")
                    self.__environment_provider.wait_execute(90)

                        # Copy the dc package 
                    _deploy_script_file_with_path = os.path.join(_deployScriptSRC, _deployScriptGeneratedFolder, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME'] + '.zip')

                    _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info, True))
                    _softwareLocation = os.path.join(server_info['SMO_SHARE_SOFTWARE_REPO_TARGET_PATH'])

                    _deployScriptTarget = os.path.join(server_info['DEPLOY_SCRIPT_TARGET_PATH'], _deployScriptGeneratedFolder)

                    __ssh_command = self.__environment_provider.get_ssh_command(server_info)
                    __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])

                    # Create the target folder to remote server
                    _create_dest_folder = SCP(__ssh_command).create_dir_to_remote(__is_windows,_deployScriptTarget)

                    if _create_dest_folder == 0:
                        # Copy DCScript into Remote Server
                        _copydeployscriptslocationResult = _ssh.copy_to_remote(_deploy_script_file_with_path, os.path.join(_deployScriptTarget,server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME'] + '.zip')) 

                        _share_software_repo_targetpath = server_info['SMO_SHARE_SOFTWARE_REPO_TARGET_PATH']

                        if _copydeployscriptslocationResult == 0:

                            _chmod = SCP(__ssh_command).chmod_remote(_deployScriptTarget, __is_windows)

                            _maintenance = False
                            if 'maintenance' in self.__arguments._arguments:
                                _maintenance = getattr(self.__arguments._arguments, 'maintenance')
                                _maintenance = True

                            if _maintenance:
                                _copyshareSoftwareRepoResult = 0

                            else:
                                _copyshareSoftwareRepoResult = self._dcscriptUtilities.copySoftwareRepoPackageRemote(self._tcpackage_id, self.__properties, self.__target, _share_software_repo_targetpath, __ssh_command, _scp_without_ssh, __is_windows, server_info)

                                self.__console_msg(_copyshareSoftwareRepoResult, 'Copy the BMIDE Package into Software Repository')
                                
                            if _copyshareSoftwareRepoResult == 0:
                                # package copied
                                self.log.info(f'DCScript Package Copied Successfully!')

                                _deployScriptPath =  os.path.join(_deployScriptTarget, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME']) 

                                if __is_windows:
                                    self.log.info(f"Executing on Windows Environment")
                                    # Extract the package
                                    self._dcscriptUtilities.extractZIPFile(__ssh_command,_deployScriptTarget, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME'], __is_windows, server_info['7ZIP_PATH'])

                                    # Prepare the Deploy Execution Argument for Windows
                                    wnxscriptcaller = []
                                    wnxscriptcaller.append(os.path.join(_deployScriptPath, _command))
                                    wnxscriptcaller.append('-softwareLocation=' + _softwareLocation)
                                    wnxscriptcaller = self._dcscriptUtilities.getDCCrenditals(server_info, wnxscriptcaller)
                                    wnxscriptcaller = ' '.join([str(elem) for elem in wnxscriptcaller])

                                    diagnosticCheck = wnxscriptcaller + ' -diagnosticChecks'

                                    result = self._execute(__ssh_command +' "' +diagnosticCheck+ '"' , '/')
                                    self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': '','label': f"DCScript RemoteDeploy"})
                                    self.__console_msg(result, 'DiagnosticCheck DCScript Remote')
                                    if result == 0:
                                        deployResult = self._execute(__ssh_command +' "' +wnxscriptcaller+'"', '/')
                                        self.__console_msg(deployResult, 'DCScript Remote Deployed')
                                        self._processes.append({'NODE':server_info['NODE'],'process': deployResult,'module': self.__module_label, 'package_id': '','label': f"DCScript RemoteDeploy"})
                                    

                                else:
                                    self.log.info(f"Executing on LNX Environment")
                                    # Extract the Package    
                                    self._dcscriptUtilities.extractZIPFile(__ssh_command,_deployScriptTarget, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME'], __is_windows) 

                                    # Prepare the Deploy Execution Argument for Linux
                                    lnxscriptcaller = []  
                                    lnxscriptcaller.append('cd '+_deployScriptPath + ' &&')
                                    lnxscriptcaller.append('./'+_command)
                                    lnxscriptcaller.append('-softwareLocation=' + _softwareLocation)
                                    lnxscriptcaller = self._dcscriptUtilities.getDCCrenditals(server_info, lnxscriptcaller)
                                    lnxscriptcaller = ' '.join([str(elem) for elem in lnxscriptcaller])

                                    diagnosticCheck = lnxscriptcaller + ' -diagnosticChecks'

                                    if __ssh_command == '':
                                        result = self._execute(diagnosticCheck, '/')
                                    else:
                                        diagnosticCheck = '"'+diagnosticCheck + '"'
                                        result = self._execute(__ssh_command +' ' +diagnosticCheck, '/')
                                    self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': '','label': f"DCScript RemoteDeploy"})
                                    self.__console_msg(result, 'DiagnosticCheck DCScript Remote')
                                    if result == 0:
                                        if __ssh_command == '':
                                            deployResult = self._execute(lnxscriptcaller, '/')
                                        else:
                                            lnxscriptcaller = '"'+lnxscriptcaller + '"'
                                            deployResult = self._execute(__ssh_command +' ' +lnxscriptcaller, '/')
                                        self.__console_msg(deployResult, 'DCScript Remote Deployed')
                                        self._processes.append({'NODE':server_info['NODE'],'process': deployResult,'module': self.__module_label, 'package_id': '','label': f"DCScript RemoteDeploy"})
                                    else:
                                        self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': '','label': f"DCScript RemoteDeploy"})
                            else:
                                self.log.error(f'Copy the BMIDE Package into Software Repository Failed!')
                                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})
                        
                        else:
                            self.log.error(f'Copy DCScript into Remote Server Failed!')
                            self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})
                            
                    else:
                        self.log.error(f'DCScript Create the target folder to remote server Failed!')
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})


            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})

            _processesResult = [_process for _process in self._processes if _process['NODE'] == server_info['NODE']]

            if len(_processesResult):
                self.__environment_provider.resume_state_execution_write(self._tcpackage_id,self.__target,self.__target,_processesResult) # Resume State Execution Write File
      
        return self._processes      

    def deploy(self):

        self.log.debug('Deploy Scripts Execution')

        _resume_state_read = self.__environment_provider.resume_state_execution_read(self._tcpackage_id,self.__target,self._resumestate)

        if not _resume_state_read:
            self._processes.append({'NODE':'','process': 0,'module': self.__module_label, 'package_id': '','label': f"DCScript Not available"})
            return self._processes

        _execute_servers = [] 
        for executionServer in _resume_state_read[self.__target]:
            _execute_servers.extend(self.__environment_provider.get_execute_server_details(executionServer))

        _command = self.__properties[self.__target]['command']

        for index, server_info in enumerate(_execute_servers):
            
            try:
                self.log.info("Requesting to Start the DC_ALL Service")
                dynamicExecutor = DynamicExecutor(self.__arguments)
                for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Start', 'DC_ALL'):
                    if serviceData['pid']:
                        self.log.info(f"{serviceData['module']} - Start")
                    else:
                        self.log.error(f"{serviceData['module']} not Started. Please Check the DC_ALL Service")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript"})
                        return self._processes
                    
                self.log.info("Requesting to Start the FSC_DCSCRIPT Service")
                for serviceData in dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Start', 'FSC_DCSCRIPT'):
                    if serviceData['pid']:
                        self.log.info(f"{serviceData['module']} - Started")
                    else:
                        self.log.error(f"{serviceData['module']} not Started. Please Check the FSC_DCSCRIPT Service")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript"})
                        return self._processes                  

                # Get the share location path
                _deployScriptTarget = os.path.join(self.__share_do_not_modify_dir,'deploy_scripts', self.__environment_provider.get_environment_name())

                # Get the latest folder using timestamp
                _deployScriptGeneratedFolder = self._dcscriptUtilities.getdeployScriptGeneratedPath(_deployScriptTarget)               
                
                # Automation deployment with delta feature need to validate the deployment center package output folder
                try:
                    for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):                                                           
                        package_full_path = self.__environment_provider.get_location_in_package(tc_package_id)
                        self.log.debug(f'Checking the {tc_package_id} DCPackage Timestamp {_deployScriptGeneratedFolder}')
                        if os.path.exists(os.path.join(package_full_path, self.__environment_provider.get_environment_name() + '_DCPackage_Generate.txt')):
                            config_file = File(package_full_path, self.__environment_provider.get_environment_name() + '_DCPackage_Generate.txt')                                    
                            
                            deployment_center_package_folder = config_file.read_content('utf-8')

                            if deployment_center_package_folder == _deployScriptGeneratedFolder:
                                self.log.debug(f"From Generated File {deployment_center_package_folder} and Folder name {_deployScriptGeneratedFolder} is available. Deployment starting...")
                            else:
                                self.log.debug(f"From Generated File {deployment_center_package_folder} and Folder name {_deployScriptGeneratedFolder} is not available. Deployment Skipped...")
                                self.log.warning(f"{server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME']} not available on DCScripts. Skipped Deployment")
                                self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': '','label': f"DCScript not available"})
                                return self._processes    
                                                
                except Exception as e:
                    self.log.error(e)

                if not os.path.exists(os.path.join(_deployScriptTarget, _deployScriptGeneratedFolder, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME']+'.zip')):
                    self.log.warning(f"{server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME']} not available on DCScripts. Skipped Deployment")
                    self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': '','label': f"DCScript not available"})
                else:
                    self.log.info(f"DCScript FileName: {server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME']}")
                    self.__environment_provider.wait_execute(90)

                    _deployScriptPath =  os.path.join(_deployScriptTarget, _deployScriptGeneratedFolder, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME']) 
                
                    if not os.path.exists(_deployScriptPath):
                        # Extract the Deploy scripts package respective servers
                        self._dcscriptUtilities.extractDeployScripts(os.path.join(_deployScriptTarget, _deployScriptGeneratedFolder), server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME'])
                    
                    self.__environment_provider.change_execmod(_deployScriptPath)

                    # Update the DCScript file if any changes present in the .config/DCScript Folder

                    _dcscript_config_file = self.__environment_provider.get_dcscript_file()

                    if not os.path.exists(_dcscript_config_file):
                        self.log.debug(f"DCScript Configuration file not found! '{_dcscript_config_file}'. Skipped Configuration Replace")
                    else:
                        _configure_result = self._dcscriptUtilities.configureDeployScriptFiles(_dcscript_config_file, _deployScriptPath, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME'])

                        if _configure_result == 0:
                            self._processes.append({'NODE':server_info['NODE'], 'process': _configure_result, 'module': self.__module_label, 'package_id': '', 'label': f"DCScript Deploy"})
                            self.__console_msg(_configure_result, 'DCScript Configuration')
                        elif _configure_result == 1:
                            self._processes.append({'NODE':server_info['NODE'], 'process': _configure_result, 'module': self.__module_label, 'package_id': '', 'label': f"DCScript Deploy"})
                            self.__console_msg(_configure_result, 'DCScript Configuration')
                            return self._processes
                        else:
                            self.log.warning('No Updates in DCScript; therefore, it was skipped.')

                    _softwareLocation = server_info['SOFTWARE_REPO_TARGET_PATH']
                    
                    __ssh_command = self.__environment_provider.get_ssh_command(server_info)
                    __is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])

                    if __is_windows:
                        winscriptcaller = []

                        winscriptcallerFilePath = os.path.join(_deployScriptTarget, _deployScriptGeneratedFolder, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME'],'deployscriptwin.ps1')
                        _deployScriptWinPath = os.path.join(_softwareLocation.split(':')[0] + ':','dita_share_do_not_modify','deploy_scripts', self.__environment_provider.get_environment_name(), _deployScriptGeneratedFolder, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME'])
                        
                        winscriptcaller.append(os.path.join(_deployScriptWinPath,_command))
                        winscriptcaller.append('-softwareLocation=' + _softwareLocation)
                        winscriptcaller = self._dcscriptUtilities.getDCCrenditals(server_info, winscriptcaller)
                        winscriptcaller = ' '.join([str(elem) for elem in winscriptcaller])
                        diagnosticCheck = winscriptcaller + ' -diagnosticChecks'

                        with open(winscriptcallerFilePath,"w") as file:
                            file.write('Write-Host "DiagnosticCheck Started"\n')
                            file.write('[Byte[]] $key = (1..16)\n')
                            file.write('$encrypted = Get-Content '+server_info['MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH']+' | ConvertTo-SecureString -Key $key\n')  
                            file.write('$credential = New-Object System.Management.Automation.PsCredential("'+server_info['DOMAIN']+'\\'+server_info['USERNAME']+'", $encrypted)\n')
                            file.write('New-PSDrive -name "'+_softwareLocation.split(':')[0]+'" -PSProvider FileSystem -Root "'+self.__environment_provider.get_share_root_win_path()+'" -Persist -Credential $credential\n')
                            file.write('Set-Location -Path '+_deployScriptWinPath+'\n')
                            file.write('& '+diagnosticCheck+'\n')

                        _winscriptcallerCopyResult =  SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(winscriptcallerFilePath, os.path.join(server_info['DEPLOYMENT_CENTER_TEMP_DIR'],'deployscriptwin.ps1'))
                        if _winscriptcallerCopyResult == 0:
                            args = [__ssh_command]
                            args.append('"cd '+server_info['DEPLOYMENT_CENTER_TEMP_DIR']+' && '+server_info['DEPLOYMENT_CENTER_TEMP_DIR'].split(':')[0]+':'+' && powershell '+server_info['DEPLOYMENT_CENTER_TEMP_DIR']+'/deployscriptwin.ps1"')
                            args = ' '.join([str(elem) for elem in args])
                            
                            self.__environment_provider.change_execmod(os.path.join(_deployScriptTarget, _deployScriptGeneratedFolder, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME'],'deployscriptwin.ps1'))
                            result = self._execute(args, '/')
                            self.__console_msg(result, 'DiagnosticCheck DCScript')
                            if result == 0:
                                with open(winscriptcallerFilePath,"w") as file:
                                    file.write('Write-Host "Deployment Started"\n')
                                    file.write('[Byte[]] $key = (1..16)\n')
                                    file.write('$encrypted = Get-Content '+server_info['MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH']+' | ConvertTo-SecureString -Key $key\n')  
                                    file.write('$credential = New-Object System.Management.Automation.PsCredential("'+server_info['DOMAIN']+'\\'+server_info['USERNAME']+'", $encrypted)\n')
                                    file.write('New-PSDrive -name "'+_softwareLocation.split(':')[0]+'" -PSProvider FileSystem -Root "'+self.__environment_provider.get_share_root_win_path()+'" -Persist -Credential $credential\n')
                                    file.write('Set-Location -Path '+_deployScriptWinPath+'\n')
                                    file.write('& '+winscriptcaller+'\n')
                                self.__environment_provider.change_execmod(os.path.join(_deployScriptTarget, _deployScriptGeneratedFolder, server_info['DEPLOYMENT_CENTER_SERVER_DEPLOY_SCRIPT_FILENAME'],'deployscriptwin.ps1'))
                                _winscriptcallerCopyResult =  SCP(self.__environment_provider.get_ssh_command(server_info, True)).copy_to_remote(winscriptcallerFilePath, os.path.join(server_info['DEPLOYMENT_CENTER_TEMP_DIR'],'deployscriptwin.ps1'))
                                if _winscriptcallerCopyResult == 0:                            
                                    deployResult = self._execute(args, '/')
                                    self.__console_msg(deployResult, 'DCScript Deployed')
                                    self._processes.append({'NODE':server_info['NODE'],'process': deployResult,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"}) 
                                else:
                                    self.__console_msg(_winscriptcallerCopyResult, 'DCScript Deployed')
                                    self._processes.append({'NODE':server_info['NODE'],'process': _winscriptcallerCopyResult,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})  
                            else:
                                self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})
                                self.__console_msg(result, 'DCScript Deployed')
                        else:
                            self._processes.append({'NODE':server_info['NODE'],'process': _winscriptcallerCopyResult,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})
                            self.__console_msg(_winscriptcallerCopyResult, 'DCScript DiagnosticCheck')
                        
                    else:
                        
                        lnxscriptcaller = []  
                        lnxscriptcaller.append('cd '+_deployScriptPath + ' &&')
                        lnxscriptcaller.append('./'+_command)
                        lnxscriptcaller.append('-softwareLocation=' + _softwareLocation)
                        lnxscriptcaller = self._dcscriptUtilities.getDCCrenditals(server_info, lnxscriptcaller)
                        lnxscriptcaller = ' '.join([str(elem) for elem in lnxscriptcaller]) 
                            
                        
                        diagnosticCheck = lnxscriptcaller + ' -diagnosticChecks'

                        self.log.info(diagnosticCheck)
                        if __ssh_command == '':
                            result = self._execute(diagnosticCheck, '/')
                        else:
                            diagnosticCheck = '"'+diagnosticCheck + '"'
                            result = self._execute(__ssh_command +' ' +diagnosticCheck, '/')
                        self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})
                        self.__console_msg(result, 'DiagnosticCheck DCScript')
                        if result == 0:
                            if __ssh_command == '':
                                deployResult = self._execute(lnxscriptcaller, '/')
                            else:
                                lnxscriptcaller = '"'+lnxscriptcaller + '"'
                                deployResult = self._execute(__ssh_command +' ' +lnxscriptcaller, '/')
                            self.__console_msg(deployResult, 'DCScript Deployed')
                            self._processes.append({'NODE':server_info['NODE'],'process': deployResult,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})

                        else:
                            self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})
            
            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript Deploy"})

            _processesResult = [_process for _process in self._processes if _process['NODE'] == server_info['NODE']]

            if len(_processesResult):
                self.__environment_provider.resume_state_execution_write(self._tcpackage_id,self.__target,self.__target,_processesResult) # Resume State Execution Write File

        return self._processes        



    def win(self):
        return self._executeCombineTargets()

    def lnx(self):
        return self._executeCombineTargets()

    def _executeCombineTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__target).split(',')):
                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name
                if dynamicExecutor.get_sub_module_name():    
                    _processesResult = getattr(DCScript, dynamicExecutor.get_sub_module_name())(self)
                else:
                    _processesResult = dynamicExecutor.run_module()
                self._processesResult = self._processesResult + _processesResult  
            return self._processesResult
        except Exception as exp:
            self.log.error(exp)

    def _executeTargets(self):

        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__module_name).split(',')): 
                # Execute with multiple targets
                if not self.__sub_module_name:
                    self.__target = targets
                    dynamicExecutor = DynamicExecutor(self.__arguments)   
                    dynamicExecutor.set_module_instance(targets) # module instance name
                    if dynamicExecutor.get_sub_module_name():
                        _processesResult = getattr(DCScript, dynamicExecutor.get_sub_module_name())(self)
                    else:
                        _processesResult = dynamicExecutor.run_module() 
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult               
        except Exception as exp:
            self.log.error(exp)


    def _execute(self, command, path='', stderr = True):
        """
         Used to process services/command
        """
        process = Process(command)
        process.set_stderr(stderr)
        return process.execute()


    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')