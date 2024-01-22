import com.lib.Utilities

def call(config) {

    def utils = new Utilities()

    String DITA_DEPLOY_SCRIPTS = config.DITA_DEPLOY_SCRIPTS
    String DITA_MANAGE_SCRIPTS = config.DITA_MANAGE_SCRIPTS
    String PACKAGE_LIST_TO_DEPLOY =  config.PACKAGE_LIST_TO_DEPLOY
    def SUB_TARGETS_DEPLOYMENT_OPTIONS = config.SUB_TARGETS_DEPLOYMENT_OPTIONS
    def parametersConfig =  config.parametersConfig
    String stagename = config.stagename
    String MAINTENANCE = config.containsKey('MAINTENANCE') ? config.MAINTENANCE: ''

    

    if(stagename == "DC_Export_Env"){
        exportENVQD(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if(stagename == "DC_Generate_Scripts"){
        generateDCScripts(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if(stagename == "DC_ExecuteScripts_Corp"){
        corpDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if(stagename == "DC_ExecuteScripts_CorpAll"){
        corpAllDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if(stagename == "volumesDCDeploy") {
        volumesDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if(stagename == "DC_ExecuteScripts_AWC") {
        awcDCDeploy(utils, parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if(stagename == "DC_ExecuteScripts_AWCSOLR") {
        awcsolrDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if(stagename == "DC_ExecuteScripts_DispatcherWin") {
        dispatcherWinDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if(stagename == "DC_ExecuteScripts_DispatcherLnx") {
        dispatcherLnxDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if(stagename == "DC_ExecuteScripts_AIG") {
        aigDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if(stagename == "DC_ExecuteScripts_Batch") {
        batchDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }

    if (stagename == "DC_ExecuteScripts_RemoteDeployWin") {
        remoteWinDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS, MAINTENANCE)
    }

    if(stagename == "DC_ExecuteScripts_RemoteDeployLnx") {
        remoteLnxDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS, MAINTENANCE)
    }

    if(stagename == "generateMountPassWinDeploy") {
        generateMountPassWinDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS)
    }
}

def exportENVQD(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {                   
        echo '[DEBUG INFO] DC_Export_Env'
        echo "[DEBUG INFO] Packages To Deploy : ${PACKAGE_LIST_TO_DEPLOY}"
        String ExportEnvQD_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.exportENVQD"
        if (params.TARGET_ENVIRONMENT.equals('TCSMOD20') || params.TARGET_ENVIRONMENT.equals('TCSMOQ20')) {
            ExportEnvQD_CMD += ".lnx -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        }
        else
        {
            ExportEnvQD_CMD += ".win -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        }
        runCommand([command: ExportEnvQD_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_Export_Env"])
    } else {
        echo '[DEBUG INFO] DC_Export_Env Empty Package Information'
    }
}

def generateDCScripts(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {  
        echo '[DEBUG INFO] DC_Generate_Scripts'
        echo "[DEBUG INFO] Packages To Deploy : ${PACKAGE_LIST_TO_DEPLOY}"
        String GenerateDC_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.generateDeployScripts"
        if (params.TARGET_ENVIRONMENT.equals('TCSMOD20') || params.TARGET_ENVIRONMENT.equals('TCSMOQ20')) {
            GenerateDC_CMD += ".lnx -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        } else {                       
            //echo '[DEBUG INFO] Prestep for DC Generate Script - Dita Generate Mount Password'
            String GenerateMountPassWinDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m Dita.generateMountPassword -p ${PACKAGE_LIST_TO_DEPLOY} -d"
            // runCommand([command: GenerateMountPassWinDeploy_CMD])
            GenerateDC_CMD += ".win -p ${PACKAGE_LIST_TO_DEPLOY} -d" 
        }
        runCommand([command: GenerateDC_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_Generate_Scripts"])
    } else {
        echo '[DEBUG INFO] DC_Generate_Scripts Empty Package Information'
    }
}

def corpDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {  
        echo '[DEBUG INFO] DC_ExecuteScripts_Corp'
        echo "[DEBUG INFO] Packages To Deploy : ${PACKAGE_LIST_TO_DEPLOY}"
        String CorporateDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.deploy.corp -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        String RemoveDCTrackerFile = ""
        if (params.TARGET_ENVIRONMENT.equals('TCSMOD10')) {
        RemoveDCTrackerFile += "rm -f -- /data/tcsmod10/tc14/DC_DeploymentTaskTracker.xml"
        }
        //if (params.TARGET_ENVIRONMENT.equals('TCSMOQ10')) {
        // RemoveDCTrackerFile += "rm -f -- /data/tcsmoq10/tc14/DC_DeploymentTaskTracker.xml"
        //}
        if (params.TARGET_ENVIRONMENT.equals('TCSMOD50')) {
        RemoveDCTrackerFile += "rm -f -- /data/tcsmod50/tc14/DC_DeploymentTaskTracker.xml"
        }        
        
        if (RemoveDCTrackerFile != "") {
            echo "[DEBUG INFO] Remove ${params.TARGET_ENVIRONMENT} DeploymentTaskTracker"
            runCommand([command: RemoveDCTrackerFile])
        }       
        runCommand([command: CorporateDCDeploy_CMD])


        if (params.TARGET_ENVIRONMENT.equals('TCSMOD30')) {
            String ChangeTCProfilevarsPermission = "chmod -R 0755 /data/tcsmod30/tc_data/tc_profilevars" 
            runCommand([command: ChangeTCProfilevarsPermission])
            String ChangeTCProfilevarsSSOPermission = "chmod -R 0755 /data/tcsmod30/tc_data_sso_lnx64/tc_profilevars" 
            runCommand([command: ChangeTCProfilevarsSSOPermission])
        }
        if (params.TARGET_ENVIRONMENT.equals('TCSMOQ30')) {
            String ChangeTCProfilevarsPermission = "chmod -R 0755 /data/tcsmoq30/tc_data/tc_profilevars" 
            runCommand([command: ChangeTCProfilevarsPermission])
            String ChangeTCProfilevarsSSOPermission = "chmod -R 0755 /data/tcsmoq30/tc_data_sso_lnx64/tc_profilevars" 
            runCommand([command: ChangeTCProfilevarsSSOPermission])
        }
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_Corp"])
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_Corp Empty Package Information'
    }
}

def corpAllDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {  
        echo '[DEBUG INFO] DC_ExecuteScripts_CorpAll'
        echo "[DEBUG INFO] Packages To Deploy : ${PACKAGE_LIST_TO_DEPLOY}"
        String CorporateALLDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.deploy.corp.all -p ${PACKAGE_LIST_TO_DEPLOY} -d"                
        runCommand([command: CorporateALLDCDeploy_CMD])
        if (params.TARGET_ENVIRONMENT.equals('TCSMOD30')) {
            String ChangeTCProfilevarsPermission = "chmod -R 0755 /data/tcsmod30/tc_data/tc_profilevars" 
            runCommand([command: ChangeTCProfilevarsPermission])
            String ChangeTCProfilevarsSSOPermission = "chmod -R 0755 /data/tcsmod30/tc_data_sso_lnx64/tc_profilevars" 
            runCommand([command: ChangeTCProfilevarsSSOPermission])
        }
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_CorpAll"]) 
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_CorpAll Empty Package Information'
    }
}

def volumesDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo '[DEBUG INFO] DC_ExecuteScripts_Volumes'
        echo "[DEBUG INFO] Packages To Deploy : ${PACKAGE_LIST_TO_DEPLOY}"
        String VolumeALLDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.deploy.volumes -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        runCommand([command: VolumeALLDCDeploy_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_Volumes"]) 
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_Volumes Empty Package Information'
    }
}

def generateMountPassWinDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo '[DEBUG INFO] Prestep for DC Generate Script - Dita Generate Mount Password'
        String GenerateMountPassWinDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m Dita.generateMountPassword -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        runCommand([command: GenerateMountPassWinDeploy_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"GenerateMountPassWinDeploy"])  
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_DispatcherWin Empty Package Information'
    }
}

def awcDCDeploy(utils, parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null && PACKAGE_LIST_TO_DEPLOY != '') {

        if ((SUB_TARGETS_DEPLOYMENT_OPTIONS['DC_ExecuteScripts_AWC'].size() != 0)) {

            echo '[DEBUG INFO] DC_ExecuteScripts_AWC'
            echo "[DEBUG INFO] Packages To Deploy : ${PACKAGE_LIST_TO_DEPLOY}"

            def totalTargets = utils.getMapValuesFromKey(parametersConfig['deploymentsubConfig']['deploymentsubtargets'], 'DC_ExecuteScripts_AWC').size()

            if (SUB_TARGETS_DEPLOYMENT_OPTIONS['DC_ExecuteScripts_AWC'].size() == totalTargets) {

                String AWCALLDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.deploy.awc -p ${PACKAGE_LIST_TO_DEPLOY} -d"
                runCommand([command: AWCALLDCDeploy_CMD])
            } else {

                for (dctarget in SUB_TARGETS_DEPLOYMENT_OPTIONS['DC_ExecuteScripts_AWC']) {
                    
                    String AWCALLDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m ${dctarget} -p ${PACKAGE_LIST_TO_DEPLOY} -d"
                    runCommand([command: AWCALLDCDeploy_CMD])
                }
            }
            checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_AWC"]) 
        }
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_AWC Empty Package Information'
    }
}

def awcsolrDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo '[DEBUG INFO] DC_ExecuteScripts_AWCSOLR'
        echo "[DEBUG INFO] Packages To Deploy : ${PACKAGE_LIST_TO_DEPLOY}"
        String AWCSOLRDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.deploy.awcsolr -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        runCommand([command: AWCSOLRDCDeploy_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_AWCSOLR"])
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_AWCSOLR Empty Package Information'
    }
}


def dispatcherWinDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo '[DEBUG INFO] DC_ExecuteScripts_DispatcherWin'
        echo "[DEBUG INFO] Packages To Deploy : ${PACKAGE_LIST_TO_DEPLOY}"
        String DispatcherWinDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.deploy.dispatcher.win -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        runCommand([command: DispatcherWinDCDeploy_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_DispatcherWin"])  
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_DispatcherWin Empty Package Information'
    }
}

def dispatcherLnxDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo '[DEBUG INFO] DC_ExecuteScripts_DispatcherLnx'
        String DispatcherLnxDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.deploy.dispatcher.lnx -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        runCommand([command: DispatcherLnxDCDeploy_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_DispatcherLnx"]) 
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_DispatcherLnx Empty Package Information'
    }
}

def aigDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo '[DEBUG INFO] DC_ExecuteScripts_AIG'
        String AIGDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.deploy.aig -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        runCommand([command: AIGDCDeploy_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_AIG"])
    }  else {
        echo '[DEBUG INFO] DC_ExecuteScripts_AIG Empty Package Information'
    }
}

def batchDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo '[DEBUG INFO] DC_ExecuteScripts_Batch'        
        String BatchDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.deploy.corp.batch -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        runCommand([command: BatchDCDeploy_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_Batch"])
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_Batch Empty Package Information'
    }
}

def remoteWinDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS, MAINTENANCE){
    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo '[DEBUG INFO] DC_ExecuteScripts_RemoteDeployWin'
        String RemoteWinDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.remotedeploy.win -p ${PACKAGE_LIST_TO_DEPLOY} -d -r"
        if (MAINTENANCE != '') {
            RemoteWinDCDeploy_CMD += " --maintenance True"
        }
        runCommand([command: RemoteWinDCDeploy_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_RemoteDeployWin"]) 
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_RemoteDeployWin Empty Package Information'
    }
}

def remoteLnxDCDeploy(parametersConfig, DITA_DEPLOY_SCRIPTS, PACKAGE_LIST_TO_DEPLOY, SUB_TARGETS_DEPLOYMENT_OPTIONS, MAINTENANCE) {
    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo '[DEBUG INFO] DC_ExecuteScripts_RemoteDeployLnx'
        String RemoteLnxDCDeploy_CMD = "${DITA_DEPLOY_SCRIPTS} -m DCScript.remotedeploy.lnx -p ${PACKAGE_LIST_TO_DEPLOY} -d -r"
        if (MAINTENANCE != '') {
            RemoteLnxDCDeploy_CMD += " --maintenance True"
        }
        runCommand([command: RemoteLnxDCDeploy_CMD])
        checkErrorStatus([parametersConfig: parametersConfig,stagename:"DC_ExecuteScripts_RemoteDeployLnx"]) 
    } else {
        echo '[DEBUG INFO] DC_ExecuteScripts_RemoteDeployLnx Empty Package Information'
    }
}