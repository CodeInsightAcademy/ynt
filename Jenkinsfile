/**
 * Jenkinsfile for CI/CD Pipeline with Free Open Source SCA, SAST, DAST
 *
 * Tools:
 * - SCA: OWASP Dependency-Check (for vulnerable dependencies)
 * - SAST: Bandit (for Python code security analysis)
 * - DAST: OWASP ZAP (for runtime web application security testing)
 */

// Define global environment variables
def ZAP_SCAN_TIMEOUT = 600 // seconds
def APP_NAME = "devsecops" // Replace with your application name
def DOCKER_REGISTRY = "your-docker-registry.com" // e.g., docker.io, ghcr.io (optional, for publishing image)
def DOCKER_REGISTRY_CREDENTIALS_ID = "your-docker-registry-credentials" // Jenkins Credentials ID (optional)
def NVD_API_KEY_CREDENTIALS_ID = "nvd-api-key" // Jenkins Secret Text Credential for NVD API Key (highly recommended)
def ZAP_API_KEY_CREDENTIALS_ID = "zap-api-key" // Jenkins Secret Text Credential for ZAP API Key (for ZAP daemon)

pipeline {
    agent any // Use any available agent. For production, consider using a specific label.

    options {
        buildDiscarder(logRotator(numToKeepStr: '10')) // Keep last 10 builds
        timestamps() // Add timestamps to console output
        timeout(time: 1, unit: 'HOURS') // Global pipeline timeout
    }

    stages {
        stage('Checkout SCM') {
            steps {
                script {
                   
                git 'https://github.com/CodeInsightAcademy/ynt.git' // Replace with your repo
            

                }
            }
        }

        
        stage('Install Dependencies & Build') {
            steps {
                script {
                    echo "Installing Python dependencies..."
                    sh '''#!/bin/bash -ex
                        # Create the virtual environment
                        python3 -m venv venv

                        # Explicitly use the pip executable from the virtual environment
                        ./venv/bin/pip install --upgrade pip
                        ./venv/bin/pip install -r requirements.txt
                        
                        
                        # ./venv/bin/pytest
                        
                        # ./venv/bin/python your_app_setup_script.py
                    '''
                }
            }
        }


        stage('Unit Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install -r requirements.txt
                    pytest || true
                '''
            }
            post {
                failure {
                    error 'Unit tests failed. Aborting pipeline.'
                }
            }
        }

        stage('SCA - Dependency Check') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install safety
                    mkdir -p reports/sca
                    safety check --full-report > reports/sca/safety.txt || true
                '''
            }
        }


        stage('SAST - Bandit Scan') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install bandit
                    mkdir -p reports/sast
                    bandit -r . -f html -o reports/sast/bandit.html || true
                '''
            }
        }


        // stage('Build Docker Image') {
        //     steps {
        //         script {
        //             echo "Building Docker image for ${APP_NAME}:${env.BUILD_NUMBER}..."
        //             // Ensure your Dockerfile is correctly set up for your Python app.
        //             // Example: Dockerfile in the root of the project.
        //             docker.build("${APP_NAME}:${env.BUILD_NUMBER}", ".")
        //             // Optionally tag with 'latest' for main branch
        //             if (env.BRANCH_NAME == 'main') {
        //                 docker.tag("${APP_NAME}:${env.BUILD_NUMBER}", "${APP_NAME}:latest")
        //             }
        //         }
        //     }
        // }

        // stage('Publish Docker Image (Optional)') {
        //     when {
        //         // Only publish for main branch or on tags, if you have a release strategy
        //         branch 'main'
        //         // OR: expression { return env.BRANCH_NAME == 'main' || env.TAG_NAME != null }
        //     }
        //     steps {
        //         script {
        //             if (DOCKER_REGISTRY_CREDENTIALS_ID) {
        //                 echo "Publishing Docker image to ${DOCKER_REGISTRY}..."
        //                 withCredentials([usernamePassword(credentialsId: DOCKER_REGISTRY_CREDENTIALS_ID, passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
        //                     sh "docker login ${DOCKER_REGISTRY} -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}"
        //                     sh "docker push ${DOCKER_REGISTRY}/${APP_NAME}:${env.BUILD_NUMBER}"
        //                     if (env.BRANCH_NAME == 'main') {
        //                         sh "docker push ${DOCKER_REGISTRY}/${APP_NAME}:latest"
        //                     }
        //                     sh "docker logout ${DOCKER_REGISTRY}"
        //                 }
        //             } else {
        //                 echo "DOCKER_REGISTRY_CREDENTIALS_ID not set. Skipping Docker image publish."
        //             }
        //         }
        //     }
        // }

        // stage('Deploy to Staging (for DAST)') {
        //     steps {
        //         script {
        //             echo "Deploying application to staging environment for DAST..."
                    
        //             sh "echo 'Simulating deployment of ${APP_NAME}:${env.BUILD_NUMBER} to staging...'"
        //             sh "sleep 30" // Give the application time to start up

        //             // **Define the URL ZAP will scan**
        //             env.STAGING_APP_URL = "http://localhost:5000" // **CRITICAL: CHANGE THIS TO YOUR ACTUAL STAGING URL**
        //             echo "Application deployed to staging URL: ${env.STAGING_APP_URL}"
        //         }
        //     }
        // }

        stage('DAST - OWASP ZAP Scan') {
            steps {
                script {
                    echo "Running Dynamic Application Security Testing (DAST) with OWASP ZAP..."
                   
                    withCredentials([string(credentialsId: ZAP_API_KEY_CREDENTIALS_ID, variable: 'ZAP_API_KEY')]) {
                         sh "docker run --rm -d -p 8080:8080 --name zap -e ZAP_API_KEY=${ZAP_API_KEY} owasp/zap2docker-stable zap.sh -daemon -port 8080 -host 0.0.0.0"

                        sh 'sleep 15' // Give ZAP daemon time to fully start

                        try {
                            // Use zap-cli (often pre-installed in owasp/zap2docker-stable or installable via pip)
                            // -z parameter passes ZAP options.
                            // -l (level): INFO, PASS, WARN, FAIL. ZAP will exit with a non-zero code on FAIL
                            // --spider: perform a spider scan
                            // --active-scan: perform an active scan
                            // --html: generate HTML report
                            // --json: generate JSON report
                            // --output: output file name
                            timeout(time: ZAP_SCAN_TIMEOUT, unit: 'SECONDS') {
                                sh "docker exec zap zap-cli --zap-url http://localhost:8080 --api-key ${ZAP_API_KEY} " +
                                   "quick-scan --spider --active-scan " +
                                   "--self-contained --output-format html --output-file /zap/wrk/zap-report.html " +
                                   "--output-format json --output-file /zap/wrk/zap-report.json " +
                                   "--exit-on-failure --start-url ${env.STAGING_APP_URL}"
                            }

                            // Copy reports from the Docker container to the Jenkins workspace
                            sh "docker cp zap:/zap/wrk/zap-report.html ."
                            sh "docker cp zap:/zap/wrk/zap-report.json ."
                            archiveArtifacts artifacts: 'zap-report.html, zap-report.json', fingerprint: true

                        } catch (error) {
                            echo "OWASP ZAP scan failed: ${error}"
                            // Collect reports even if ZAP exits with an error code
                            sh "docker cp zap:/zap/wrk/zap-report.html ."
                            sh "docker cp zap:/zap/wrk/zap-report.json ."
                            archiveArtifacts artifacts: 'zap-report.html, zap-report.json', fingerprint: true
                            // Re-throw the error to fail the Jenkins build
                            throw error
                        } finally {
                            // Always stop and remove the ZAP container
                            sh "docker stop zap && docker rm zap"
                        }
                    }
                }
            }
            post {
                failure {
                    echo "DAST scan detected vulnerabilities. Review report."
                    // Implement further logic here to parse the JSON report and make a decision.
                    // For example, if critical alerts are found, you could error('Critical DAST issues found.').
                }
            }
        }

        stage('Manual Approval for Production') {
            when {
                branch 'main' // Only require approval for main branch deployments
            }
            steps {
                script {
                    echo "Awaiting manual approval for production deployment."
                    timeout(time: 2, unit: 'HOURS') { // Max time to wait for approval
                        input message: 'Proceed to deploy to Production?', ok: 'Deploy'
                    }
                }
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main' // Only deploy to production for the main branch
            }
            steps {
                script {
                    echo "Deploying application to production environment..."
                    // **IMPORTANT**: Replace this with your actual production deployment logic.
                    // This should be the final, validated deployment.
                    sh "echo 'Deploying ${APP_NAME}:${env.BUILD_NUMBER} to production...'"
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline finished. Cleaning up workspace..."
            deleteDir() // Clean up workspace
        }
        success {
            echo "Pipeline completed successfully!"
            // Add success notifications (e.g., Slack, email)
        }
        failure {
            echo "Pipeline failed!"
            // Add failure notifications with links to build logs/reports
        }
    }
}