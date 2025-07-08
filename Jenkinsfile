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
                script {
                    echo "Running unit tests..."
                    // Explicitly call pytest from the virtual environment's bin directory
                    sh '''#!/bin/bash -ex
                        ./venv/bin/pytest
                    '''
                }
            }
            post {
                failure {
                    error 'Unit tests failed. Aborting pipeline.'
                }
            }
        }

        stage('SCA - OWASP Dependency-Check') {
            steps {
                script {
                    echo "Running Software Composition Analysis (SCA) with OWASP Dependency-Check..."
                    withCredentials([string(credentialsId: NVD_API_KEY_CREDENTIALS_ID, variable: 'NVD_API_KEY')]) {
                        // The `dependency-check` command-line tool.
                        // Ensure it's installed and in PATH, or specify full path.
                        // `--noupdate` can be used for faster builds if you manage NVD updates separately.
                        // `--format ALL` generates multiple report types.
                        // `--failOnCVSS 7.0` can be added to fail the build on a specific CVSS score.
                        sh "dependency-check " +
                           "--project \"${APP_NAME}\" " +
                           "--scan . " +
                           "--format HTML " +
                           "--out \"dependency-check-report\" " +
                           "--enableNVDData " + // Ensure NVD data is used
                           "--apiKey ${NVD_API_KEY}" // Use the injected API key
                        
                        archiveArtifacts artifacts: 'dependency-check-report/dependency-check-report.html', fingerprint: true
                        archiveArtifacts artifacts: 'dependency-check-report/dependency-check-report.xml', fingerprint: true
                    }
                }
            }
            post {
                failure {
                    echo "OWASP Dependency-Check found vulnerabilities. Review reports."
                    // Optionally, add logic here to fail the build based on report parsing
                }
            }
        }

        stage('SAST - Bandit') {
            steps {
                script {
                    echo "Running Static Application Security Testing (SAST) with Bandit..."
                    // Bandit for Python code.
                    // -r: recursive scan
                    // -f: output format (json, html, csv, txt, xml)
                    // -o: output file
                    // --severity-level: LOW, MEDIUM, HIGH (and above)
                    // --confidence-level: LOW, MEDIUM, HIGH (and above)
                    // --exclude: paths to exclude (e.g., virtual environments)
                    // ./ : Scan current directory
                    sh "bandit -r . -f html -o bandit-report.html --severity-level medium --confidence-level medium"
                    sh "bandit -r . -f json -o bandit-report.json --severity-level medium --confidence-level medium"

                    archiveArtifacts artifacts: 'bandit-report.html, bandit-report.json', fingerprint: true
                }
            }
            post {
                failure {
                    echo "Bandit found potential security issues. Review reports."
                    // You might want to parse the JSON report here and fail the build if critical issues are found.
                    // Example: check if "results" array in bandit-report.json is not empty.
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image for ${APP_NAME}:${env.BUILD_NUMBER}..."
                    // Ensure your Dockerfile is correctly set up for your Python app.
                    // Example: Dockerfile in the root of the project.
                    docker.build("${APP_NAME}:${env.BUILD_NUMBER}", ".")
                    // Optionally tag with 'latest' for main branch
                    if (env.BRANCH_NAME == 'main') {
                        docker.tag("${APP_NAME}:${env.BUILD_NUMBER}", "${APP_NAME}:latest")
                    }
                }
            }
        }

        stage('Publish Docker Image (Optional)') {
            when {
                // Only publish for main branch or on tags, if you have a release strategy
                branch 'main'
                // OR: expression { return env.BRANCH_NAME == 'main' || env.TAG_NAME != null }
            }
            steps {
                script {
                    if (DOCKER_REGISTRY_CREDENTIALS_ID) {
                        echo "Publishing Docker image to ${DOCKER_REGISTRY}..."
                        withCredentials([usernamePassword(credentialsId: DOCKER_REGISTRY_CREDENTIALS_ID, passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                            sh "docker login ${DOCKER_REGISTRY} -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}"
                            sh "docker push ${DOCKER_REGISTRY}/${APP_NAME}:${env.BUILD_NUMBER}"
                            if (env.BRANCH_NAME == 'main') {
                                sh "docker push ${DOCKER_REGISTRY}/${APP_NAME}:latest"
                            }
                            sh "docker logout ${DOCKER_REGISTRY}"
                        }
                    } else {
                        echo "DOCKER_REGISTRY_CREDENTIALS_ID not set. Skipping Docker image publish."
                    }
                }
            }
        }

        stage('Deploy to Staging (for DAST)') {
            steps {
                script {
                    echo "Deploying application to staging environment for DAST..."
                    // **IMPORTANT**: Replace this with your actual deployment logic.
                    // This could be kubectl, ansible, docker-compose, etc.
                    // The goal is to make the application accessible via a URL.

                    // Example: Running with Docker Compose (simplified)
                    // sh 'docker-compose -f docker-compose.staging.yml up -d'
                    // For a real deployment, this would typically involve pushing to a K8s cluster, etc.
                    sh "echo 'Simulating deployment of ${APP_NAME}:${env.BUILD_NUMBER} to staging...'"
                    sh "sleep 30" // Give the application time to start up

                    // **Define the URL ZAP will scan**
                    env.STAGING_APP_URL = "http://localhost:8080" // **CRITICAL: CHANGE THIS TO YOUR ACTUAL STAGING URL**
                    echo "Application deployed to staging URL: ${env.STAGING_APP_URL}"
                }
            }
        }

        stage('DAST - OWASP ZAP Scan') {
            steps {
                script {
                    echo "Running Dynamic Application Security Testing (DAST) with OWASP ZAP..."
                    // Running ZAP via Docker for ease of setup and consistent environment.
                    // Ensure the Jenkins agent can run Docker commands.
                    // The ZAP container needs to access the staging application.
                    // If ZAP is on a different network, ensure network connectivity.
                    // For local development, 'host' network mode or direct IP might be needed.

                    withCredentials([string(credentialsId: ZAP_API_KEY_CREDENTIALS_ID, variable: 'ZAP_API_KEY')]) {
                        // Start ZAP in daemon mode. Using a trusted ZAP container.
                        // Expose ZAP's API port (8080) and optionally a report directory.
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