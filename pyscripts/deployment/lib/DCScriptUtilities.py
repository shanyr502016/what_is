
from corelib.Loggable import Loggable
from corelib.Process import Process
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import glob
import zipfile
import json
from corelib.SCP import SCP

class DCScriptUtilities(Loggable):
    
    def __init__(self, environment_provider): 
        
        super().__init__(__name__)

        self._environment_provider = environment_provider


    def getDCCommand(self, _server_info, _dcScriptsPath, _command):
        """
        Get Deployment Center Command With SSH or Non SSH
        """
        __ssh_command = self._environment_provider.get_ssh_command(_server_info)

        if __ssh_command == '':
            args = []
        else:
            args = [__ssh_command]
        # Build DC Command
        _dc_command = os.path.join(_dcScriptsPath, _command)

        args.append(_dc_command)

        return ' '.join([str(elem) for elem in args])
    
    def getDCExportENVCommand(self, server_info, dcCommand, exportFileName):
        """
        Preparing Export Environment File from Deployment Center Command
        """
        args = [dcCommand]    

        args.append('-dcurl='+ server_info['DEPLOYMENT_CENTER_URI'])

        args.append('-mode=export')

        args.append('-environment='+ server_info['EXPORT_ENVIRONMENT_NAME'])

        args.append('-exportType=Full')

        args.append('-exportfile=' + self.getExportFileNameWithPath(self._environment_provider, server_info['EXPORT_FILE_PATH'], exportFileName, server_info['OS_TYPE']))
        
        # DCUsername and DCPassword
        args = self.getDCCrenditals(server_info, args)

        return ' '.join([str(elem) for elem in args])
    

    def getDCCrenditals(self, server_info, args):
        """
        Returns DC_Username and DC_Password
        """
        args.append('-dcusername=' + server_info['DC_USERNAME'])

        args.append('-dcpassword=' + server_info['DC_PASSWORD'])

        return args
   
        
    def getBMIDEInfo(self, _location_in_package):
        
        _bmidelocation = os.listdir(_location_in_package)
        _bmideInfo = dict()

        if _bmidelocation:  
            mediaFilename = os.path.join(_location_in_package,_bmidelocation[0])
            
            for file in os.listdir(mediaFilename):
                
                if file.startswith('media_teamcenter_') and file.endswith('.xml'):
                    
                    _xmlfile = os.path.join(mediaFilename, file)
                    rootElement = ET.parse(_xmlfile).getroot()
                    
                    if rootElement.find('application_id') is not None:                        
                        _bmideInfo['BMIDEProjectName'] = rootElement.find('application_id').text
                        self.log.debug('BMIDEProjectName: '+ _bmideInfo['BMIDEProjectName'])
                        
                    if rootElement.find('version') is not None:                        
                        _bmideInfo['BMIDEVersion'] = (rootElement.find('version').text)
                        self.log.debug('BMIDEVersion: '+ _bmideInfo['BMIDEVersion'])
            return _bmideInfo
        
    def createQuickDeployXML(self, exportfilepath, exportFileName, security, tc_package_id, bmide_location):
    
        try:
        
            root = ET.Element('quickDeployConfig', configName=self._environment_provider.get_environment_name(), version='1.0')
            arch = ET.SubElement(root, 'archType' , types='J2EE')
            
            quickDeploySoftware = ET.SubElement(root, 'quickDeploySoftware')
        
            for tc_package_id in self._environment_provider.getTCPackageID(tc_package_id):
            
                _location_in_package = self._environment_provider.get_location_in_package(tc_package_id, bmide_location)
                _bmideInfo = self.getBMIDEInfo(_location_in_package)

                software = ET.SubElement(quickDeploySoftware, 'software', id=_bmideInfo['BMIDEProjectName'], version=_bmideInfo['BMIDEVersion'])

            tree = ET.ElementTree(root)
            xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent=" ")
            xmlstr = xmlstr.replace('<?xml version="1.0" ?>', "<?xml version='1.0' encoding='UTF-8'?>")
            with open(os.path.join(exportfilepath, exportFileName), "w") as f:
                f.write(xmlstr)
                
            return True      
        except ET.ParseError as exp:
            self.log.error(f"Security Credentials Updation: {exp}")
            return False
            

    def updateSecurityCredentials(self, exportfilepath, exportFileName, security, tc_package_id, bmide_location):        

        try:
            xmlTree = ET.parse(os.path.join(exportfilepath, exportFileName))
            rootElement = xmlTree.getroot()

            for tc_package_id in self._environment_provider.getTCPackageID(tc_package_id):

                _location_in_package = self._environment_provider.get_location_in_package(tc_package_id, bmide_location)
                _bmideInfo = self.getBMIDEInfo(_location_in_package)

                self.log.info(f"BMIDE Project Name: {_bmideInfo['BMIDEProjectName']}")
                self.log.info(f"BMIDE Version: {_bmideInfo['BMIDEVersion']}")

                for element in rootElement.findall("quickDeploySoftware/software"):
                    if element.get('id') == _bmideInfo['BMIDEProjectName']:
                        element.attrib['version'] = _bmideInfo['BMIDEVersion']

                for securitykey in security.keys():
                    # Updating the Security Credentials 
                    if (type(security[securitykey]) == str):
                        for element in rootElement.findall('quickDeployComponents/component/property'):
                            if element.get('id') in security:
                                if element.get('id') == securitykey:
                                    element.attrib['value'] = security[securitykey]
                                    element.attrib['encrypted'] = 'false'                            
                    elif (type(security[securitykey]) == list):
                        
                        for components in security[securitykey]:
                            for elements in rootElement.findall('quickDeployComponents/component'):                                
                                if components['machineName'] == elements.get('machineName'):
                                    for element in elements.findall('property'):                                        
                                        if securitykey == element.get('id'):
                                            element.attrib['value'] = components['value']
                                            
                                        
                for element in rootElement.findall('quickDeployProperties/property'):
                
                    if element.get('id') in security:
                        element.attrib['value'] = security[element.get('id')]
                        element.attrib['encrypted'] = 'false'              

            xmlTree.write(os.path.join(exportfilepath, exportFileName), encoding='UTF-8',xml_declaration=True)
            self.log.info(f'Updated Environment XML File values {os.path.join(exportfilepath, exportFileName)}')

            return self.search_replacetxt(os.path.join(exportfilepath, exportFileName), 'REPLACEME')
        except ET.ParseError as exp:
            self.log.error(f"Security Credentials Updation: {exp}")
            return False
        
    def search_replacetxt(self, filepath, searchkeyword):

        """
        Search Replaceme key present after update the security credentials. if stop the deployment
        """

        searchedlines = []

        with open(filepath, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.find(searchkeyword) != -1:
                    searchedlines.append(line.strip())
                    self.log.warning(f'Credentials Update is missing on this line:  {line.strip()}.')
            
            if len(searchedlines) == 0:
                return True
            else:
                return False


    def copySoftwareRepoPackageRemote(self, tc_package_ids, properties, target, share_software_repo_targetpath, __ssh_command,_scp_without_ssh, __is_windows, server_info):

        _copyshareSoftwareRepoResult = 1

        self._processes = []

        for tc_package_id in self._environment_provider.getTCPackageID(tc_package_ids):

            _location_in_package = self._environment_provider.get_location_in_package(tc_package_id, properties[target]['location_in_package'])
            if os.path.exists(_location_in_package):

                _tcpackage_with_packageid_targetpath = os.path.join(share_software_repo_targetpath,_location_in_package[_location_in_package.find('Siemens_deployments'):])

                self.log.info('Copy Deploy Package into Software Repository')
                _create_dest_folder = SCP(__ssh_command).create_dir_to_remote(__is_windows,_tcpackage_with_packageid_targetpath)
                if _create_dest_folder == 0:
                    _copyshareSoftwareRepoResult = _scp_without_ssh.copy_to_remote(_location_in_package + '/*', _tcpackage_with_packageid_targetpath)
                    # changing the Permission
                    if _copyshareSoftwareRepoResult == 0:
                        if __ssh_command == '':
                            self._environment_provider.change_execmod(_tcpackage_with_packageid_targetpath)
                        else:
                            _chmod = SCP(__ssh_command).chmod_remote(_tcpackage_with_packageid_targetpath, __is_windows)
                    if _copyshareSoftwareRepoResult == 1:
                        self.log.error(f"DCScript Package not copied into Software Repository {tc_package_id}. DCScript Deployment is Failure")
                        self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"}) 
                        return self._processes
            else:
                self.log.warning(f"Required Package Folder not Present from this location [{tc_package_id}]. DCScript Deployment Skipped")
                _copyshareSoftwareRepoResult = 1
                
        return _copyshareSoftwareRepoResult

    def copySoftwareRepoPackages(self, tc_package_ids, properties, target, share_software_repo_targetpath, server_info):

        _copyshareSoftwareRepoResult = 1

        self._processes = []

        for tc_package_id in self._environment_provider.getTCPackageID(tc_package_ids):

            _location_in_package = self._environment_provider.get_location_in_package(tc_package_id, properties[target]['location_in_package'])
            _tcpackage_with_packageid_targetpath = os.path.join(share_software_repo_targetpath,_location_in_package[_location_in_package.find('Siemens_deployments'):])

            self.log.info('Copy Deploy Package into Software Repository')

            if os.path.exists(_tcpackage_with_packageid_targetpath):

                self.log.warning(f'BMIDE Packages {tc_package_id} already are available in Software Repo')
                _copyshareSoftwareRepoResult = 0   
  
            else:
                os.makedirs(_tcpackage_with_packageid_targetpath)

                _copyshareSoftwareRepoResult = SCP('').copy_to_remote(_location_in_package + '/*', _tcpackage_with_packageid_targetpath)

                # changing the Permission
                if _copyshareSoftwareRepoResult == 0:
                    self._environment_provider.change_execmod(_tcpackage_with_packageid_targetpath)
                if _copyshareSoftwareRepoResult == 1:
                    self.log.error(f"DCScript Package not copied into Software Repository {tc_package_id}. DCScript Deployment is Failure")
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '','label': f"DCScript generateDeployScripts"}) 
                    return self._processes
        return _copyshareSoftwareRepoResult




    def getGenerateDeployScriptCommand(self, server_info, dcCommand, exportFileName):

        args = [dcCommand]

        args.append('-dcurl='+ server_info['DEPLOYMENT_CENTER_URI'])

        args.append('-environment='+ server_info['EXPORT_ENVIRONMENT_NAME'])

        args.append('-platform=' + server_info['EXPORT_PLATFROM'])

        args.append('-inputFile=' + os.path.join(server_info['EXPORT_FILE_PATH'], exportFileName))

        # DCUsername and DCPassword
        args = self.getDCCrenditals(server_info, args)

        return ' '.join([str(elem) for elem in args])


    def getExportFileNameWithPath(self, environment_provider, exportFilePath, exportFileName, os_type):

        self.__is_linux = environment_provider.is_linux(os_type)
        self.__is_windows = environment_provider.is_windows(os_type) 

        if self.__is_linux:
            return os.path.join(exportFilePath, exportFileName)
        if self.__is_windows:
            return exportFilePath + '/' + exportFileName

    def getEncryptedPasswordArgs(self, server_info, _dcCommand):
        """
        Generate Encrypted Passsword from Deployment Center command
        Command: dc_quick_deploy -encrypt=clear_text_password
        """
        args = [_dcCommand] 
        args.append('-encrypt=' + server_info['DC_CLEAR_PASSWORD'])

        encryptPasswordCommand = ' '.join([str(elem) for elem in args])

        self.log.debug('Encrypted Command: '+ encryptPasswordCommand)

        process = Process(encryptPasswordCommand)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        process.execute()

        out_lines = list(filter(None, process.get_out_lines()))

        __dcencryptedPassword = out_lines[0].replace('Encrypted Password : ','')
        self.log.info('Encrypted Password: '+ __dcencryptedPassword)
        return __dcencryptedPassword


    def getdeployScriptGeneratedPath(self, path, __ssh_command = '', is_windows = False):           
        
        if __ssh_command == '':
            args = []
        else:
            args = [__ssh_command]

        if is_windows:
            args.append('"cd')    
            args.append(path)  
            args.append('&& '+ path.split(':')[0] +':')
            args.append('&& dir /b /OD"') 
        else:
            args.append('cd')    
            args.append(path)  
            args.append("&& ls -td -- */ | head -n 1 | cut -d'/' -f1") 
        
        args = ' '.join([str(elem) for elem in args])
        
        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        result = process.execute()        
        
        listoffoldernames = process.get_out_lines()
        
        dcpath = os.path.join(path, listoffoldernames[len(listoffoldernames) - 1])
        self.log.debug('Get DeployScript path: ' + dcpath)
        
        return listoffoldernames[len(listoffoldernames) - 1]
    
    def configureDeployScriptFiles(self, _dcscript_config_file, _deploy_script_path, _server_name):
        try:
            _config_data = []
            with open(_dcscript_config_file, 'r') as fin:
                _config_data = json.load(fin)
            if not _config_data.get(_server_name, None):
                self.log.warning(f"No configuration found for '{_server_name}' in {_dcscript_config_file}")
                return
            _file_object_count = len(_config_data.get(_server_name))
            _file_skipped_count = 0

            for _file_object in _config_data.get(_server_name):
                _file_name = list(_file_object.keys())[0]
                _file_path = os.path.join(_deploy_script_path, _file_name)
                if not os.path.exists(_file_path):
                    raise Exception(f"File not found '{_file_path}' [{_server_name}]")

                _replacement_map = _file_object[_file_name]
                if not _replacement_map:
                    self.log.warning(f"No replace configuration found for '{_file_name}' [{_server_name}]")
                    _file_skipped_count += 1
                    continue

                _result = self.__replace_string_in_file(_file_path, _replacement_map)
                if _result != 0:
                    raise Exception(f"Replace content failed for '{_file_name}' [{_server_name}]")

            if _file_object_count == _file_skipped_count:
                return
            return 0
        except Exception as e:
            self.log.error(f'Deploy script configuration failed! - {e}')
            return 1
    
    def __replace_string_in_file(self, _file_path, _replacement_map):
        try:
            self.log.info(f"DCScript Configuration Replace Starting....")
            _filedata = None
            with open(_file_path, 'r') as fin:
                _filedata = fin.read()
                fin.close()

            with open(_file_path, 'w') as fout:
                for contains_string in _replacement_map.keys():
                    self.log.info(f"DCScript Configuration update contains {contains_string} into {_replacement_map[contains_string]} Replaced")
                    _filedata = _filedata.replace(contains_string, _replacement_map[contains_string])
                fout.write(_filedata)
                fout.close()
            return 0
        except Exception as e:
            self.log.error(e)
            return 1
        
        
    def extractDeployScripts(self, _deployScriptZipPath, filename):

        self.log.info(f'Extract DC Scripts into Share Location: {_deployScriptZipPath}') 

        _extractFolderPath = os.path.join(_deployScriptZipPath,filename)

        for file in glob.glob(os.path.join(_deployScriptZipPath, filename + '.zip')):
            self.log.info(f'DC Scripts File: {file}')
            with zipfile.ZipFile(file) as zip_file:
                zip_file.extractall(path=_extractFolderPath)
                self.__console_msg(0, 'Extract DC Scripts')
                return _extractFolderPath
        self.__console_msg(1, 'Extract DC Scripts')
        return 1
    
    def extractZIPFile(self, __ssh_command, zipfilepath, filename, windows, SevenzipPath = ''):

        self.log.info(f'ZIP File Path : {zipfilepath}') 

        _extractFolderPath = os.path.join(zipfilepath,filename)

        if windows:
            if __ssh_command == '':
                unzip_args = []
            else:
                unzip_args = [__ssh_command]
            unzip_args.extend([SevenzipPath, 'x'])
            unzip_args.extend([os.path.join(zipfilepath, filename + '.zip')])
            unzip_args.extend(['-o'+os.path.join(zipfilepath, filename)])
            unzip_args.extend(['-y'])
            unzip_args = ' '.join([str(elem) for elem in unzip_args])

            process = Process(unzip_args)
            process.hide_output()
            process.collect_output()
            process.ignore_errors()
            status = process.execute()
            self.__console_msg(status, 'Extract DC Scripts')
            return status
        else:
            if __ssh_command == '':
                unzip = args = []
                for file in glob.glob(os.path.join(zipfilepath, filename + '.zip')):
                    self.log.info(f'DC Scripts File: {file}')
                    with zipfile.ZipFile(file) as zip_file:
                        zip_file.extractall(path=_extractFolderPath)
                        self.__console_msg(0, 'Extract DC Scripts')
                        return _extractFolderPath
                self.__console_msg(1, 'Extract DC Scripts')
                return 1
            else:
                unzip_args = [__ssh_command]
                unzip_args.extend(['unzip -o'])
                unzip_args.extend([os.path.join(zipfilepath, filename + '.zip'), '-d'])
                unzip_args.extend([os.path.join(zipfilepath, filename)])

                unzip_args = ' '.join([str(elem) for elem in unzip_args])

                process = Process(unzip_args)
                process.hide_output()
                process.collect_output()
                process.ignore_errors()
                status = process.execute()
                self.__console_msg(status, 'Extract DC Scripts')
                return status


    def __console_msg(self, result, action_msg):
        if result == 0:
            Loggable.log_success(self, f"{action_msg.capitalize()} Successfully.")
        else:
            self.log.error(f"{action_msg.capitalize()} Failed.")
        self.log.info('..............................................................')
    
    