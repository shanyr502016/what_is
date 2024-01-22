

def call(config) {

    def stagename = config.stagename
    def parametersConfig = config.parametersConfig
    def profile = config.containsKey('profile') ? config.profile: 'SystemAdmin'

    def successfulStages = 'Successful Stages \n'
    def failedStages = 'Failed Stages \n'

    checkErrorStatus(parametersConfig, successfulStages, failedStages, stagename, profile)
}


def checkErrorStatus(parametersConfig, successfulStages, failedStages, stagename, profile) {
    
    echo '[DEBUG INFO] : Started  checkErrorStatus for stage ' + stagename
    def logsToCheck = currentBuild.rawBuild.getLog(50)
    echo '[DEBUG INFO] : Received the logstocheck'
    Boolean buildStatus = true

    String failureMessage = "<b>Failure Detected for ${stagename}</b> Stage from Jenkins</br>"

    for (int i = 0; i < logsToCheck.size(); i++) {

        String logStringtoCheck = logsToCheck[i]

        if ((logStringtoCheck.contains('ERROR') || logStringtoCheck.contains('Failed'))) {
            if (logStringtoCheck.contains('[WARN] - Failed to execute Interoperability.')) {
                echo '[DEBUG INFO] Ignoring known failure for corp servers'
                break
            }
            else if (logStringtoCheck.contains('/ERRORREPORT:QUEUE')){
                echo '[DEBUG INFO] Ignoring known /ERRORREPORT:QUEUE BMIDE Build Message'
                break
            }
            else
            {
                buildStatus = false
                echo "[DEBUG INFO] Failure Detected for ${stagename} at line  ${logStringtoCheck}"
                
                failureMessage += '<p style="color: red;">' + logStringtoCheck + '</p>'                
                
                if (stagename.equals('Check_Properties') || stagename.equals('Stop_System') || stagename.equals('Backup_Env') ||stagename.equals('DC_Export_Env') || stagename.equals('DC_Generate_Scripts') || stagename.equals('DC_ExecuteScripts_Corp')) {
                    failedStages += stagename + '\n'                    

                    error "${params.TARGET_ENVIRONMENT} - ${stagename} FAILED- #${env.BUILD_NUMBER}"
                    return [
                        'status': buildStatus,
                        'subject': "${params.TARGET_ENVIRONMENT} - ${stagename} FAILED- #${env.BUILD_NUMBER}"
                    ]                     
                }
                else
                {
                    failedStages += stagename + '\n'
                }
            }
        }
    }
    if (buildStatus.equals(false)){
        notifications([parametersConfig: parametersConfig,'subject': "${params.TARGET_ENVIRONMENT} - ${env.STAGE_NAME} FAILED- #${env.BUILD_NUMBER}", body:failureMessage,  profile: profile, options: 'system_error'])
    }
    successfulStages += stagename + '\n'
    echo '[DEBUG INFO] : completed checkErrorStatus'
    return buildStatus
}