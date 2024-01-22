
// def call(config) {

//     // agent {
//     //      label 'demchdc47xx'
//     // }
    

//         stage('Teams Notification') {
//             agent { 
//                 label 'demchdc47xx'
//             }
//             steps {
//                 //script {
//                 echo "[DEBUG INFO] DITA Teams Notification Send"      
//             }
//             //}
//         }

    
    

// }


def runStageWithAgent(label) {
    return {
        agent {
            label 'demchdc47xx'
        }
        stages {
            stage('Example Stage') {
                steps {
                    echo "Running on agent: ${label}"
                    // Other steps here
                }
            }
        }
    }
}