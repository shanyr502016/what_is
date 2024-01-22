

def call(config) {

    // Perform Access Check Executions

    String DITA_DEPLOY_SCRIPTS = config.DITA_DEPLOY_SCRIPTS
    String DITA_MANAGE_SCRIPTS = config.DITA_MANAGE_SCRIPTS
    String PACKAGE_LIST_TO_DEPLOY =  config.PACKAGE_LIST_TO_DEPLOY
    String CMN_PACKAGE_LOCATION = config.CMN_PACKAGE_LOCATION
    String RI_PACKAGE_LOCATION = config.RI_PACKAGE_LOCATION
    def parametersConfig =  config.parametersConfig

    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo "[DEBUG INFO] Packages To Deploy : ${PACKAGE_LIST_TO_DEPLOY}"
        String StartStopAll_CMD = "${DITA_MANAGE_SCRIPTS} -m startstopall -a start -d"
        String AccessCheck_CMD = "${DITA_DEPLOY_SCRIPTS} -m AMRuleTree.Check -p ${PACKAGE_LIST_TO_DEPLOY} -d"
        try {
            runCommand([command: StartStopAll_CMD])           
            runCommand([command: AccessCheck_CMD])
            def directoryPath = RI_PACKAGE_LOCATION + '/12_smoke_test/access_checks'
            def latestOutputDirectory = sh(script: "ls -td ${directoryPath}/*/ | head -1", returnStdout: true).trim()         
            def attachmentFilePath = directoryPath + "/r1_authoringtools_access_checks_*_TestResults.xlsx"

            // emailext body: 'Please find the attached *TestResult.xlsx file.',
            //                      subject: 'Test Results',
            //                      to: 'raghulraj.palanisamy.ext@siemens.com',
            //                      attachments: "${attachmentFilePath}"

             //def attachmentFilePath = '/path/to/your/file/TestResult.xlsx'
                    // def mailBody = 'Please find the attached *TestResult.xlsx file.'
                    // def subject = 'Test Results'
                    // def recipient = 'raghulraj.palanisamy.ext@siemens.com'


                    // emailext (mimeType: 'text/html',
                    //     to: recipient,
                    //     subject: subject,
                    //     body: mailBody,
                    //     attachmentsPattern: attachmentFilePath
                    // ) 

        }
        catch (Exception e) {
            println 'Error is ---> ' + e.getMessage()
            return e
        }
        // checkErrorStatus([parametersConfig: parametersConfig,stagename: "Perform_Acess_Check"])   
    }  
}