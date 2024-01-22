
def call(config) {

    String DITA_DEPLOY_SCRIPTS = config.DITA_DEPLOY_SCRIPTS
    String PACKAGE_LIST_TO_DEPLOY =  config.PACKAGE_LIST_TO_DEPLOY
    String CUSTOM_BACKUP_FOLDER_NAME = config.BACKUP_FOLDER_NAME
    def parametersConfig =  config.parametersConfig

    def specificCause = currentBuild.getBuildCauses('hudson.model.Cause$UserIdCause')

    echo "Backup Triggered By: ${specificCause.userName}"

    String BACKUP_TIMESTAMP = new Date().format('yyyyMMdd.HHmm', TimeZone.getTimeZone('UTC'))
    echo '[DEBUG INFO] Backup System'
    String Backup_CMD = "${DITA_DEPLOY_SCRIPTS} -m Backup"

    String BACKUP_FOLDER_NAME_WITH_TIMESTAMP = ""

    if (CUSTOM_BACKUP_FOLDER_NAME == null || CUSTOM_BACKUP_FOLDER_NAME == '') {
        if (specificCause.userName[0] == null) {
            BACKUP_FOLDER_NAME_WITH_TIMESTAMP = "Backup_Daily_${BACKUP_TIMESTAMP}"
        } else {
            BACKUP_FOLDER_NAME_WITH_TIMESTAMP = "Backup_${BACKUP_TIMESTAMP}"
        }
    } else {    
        if (specificCause.userName[0] == null) {     
            CUSTOM_BACKUP_FOLDER_NAME = CUSTOM_BACKUP_FOLDER_NAME.replace('TIMESTAMP', "Daily_${BACKUP_TIMESTAMP}")
        } else {
            CUSTOM_BACKUP_FOLDER_NAME = CUSTOM_BACKUP_FOLDER_NAME.replace('TIMESTAMP', BACKUP_TIMESTAMP)    
        }
        
        BACKUP_FOLDER_NAME_WITH_TIMESTAMP = CUSTOM_BACKUP_FOLDER_NAME
    }

    if (params.TARGET_ENVIRONMENT.equals('TCSMOD20') || params.TARGET_ENVIRONMENT.equals('TCSMOQ20')) {       
        Backup_CMD += ".mig -p ${BACKUP_FOLDER_NAME_WITH_TIMESTAMP} -d" 
    }  else  {     
        Backup_CMD += " -p ${BACKUP_FOLDER_NAME_WITH_TIMESTAMP} -d"                            
    }  
    runCommand([command: Backup_CMD]) 
    checkErrorStatus([parametersConfig: parametersConfig, stagename: "Backup_Env"])   
}