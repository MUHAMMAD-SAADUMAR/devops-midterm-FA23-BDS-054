pipeline {
    agent any

    triggers {
        githubPush()
    }

    options {
        skipDefaultCheckout()
        disableConcurrentBuilds()
        timeout(time: 10, unit: 'MINUTES')
    }

    environment {
        STUDENT_ID = 'FA23-BDS-054'
        IMAGE      = 'midterm-fa23-bds-054'
        CONTAINER  = 'midterm-api'
        APP_PORT   = '8000'
        PUBLIC_URL = 'http://52.220.47.207:8000'
        MAIL_FROM  = 'gondalmuhammadsaadumar2@gmail.com'
        MAIL_BCC   = 'gondalmuhammadsaadumar2@gmail.com'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                }
                sh 'echo "Commit: $GIT_COMMIT"; wc -l dataset/train.csv'
            }
        }

        stage('Train') {
            agent {
                docker {
                    image 'python:3.12-slim'
                    reuseNode true
                }
            }
            environment {
                HOME = "${env.WORKSPACE}"
            }
            steps {
                sh '''
                    .venv/bin/python -c "import sys" 2>/dev/null || python -m venv .venv
                    .venv/bin/pip install -q --disable-pip-version-check -r requirements-dev.txt
                    rm -rf artifacts
                    .venv/bin/python train.py
                '''
            }
        }

        stage('Test') {
            agent {
                docker {
                    image 'python:3.12-slim'
                    reuseNode true
                }
            }
            environment {
                HOME = "${env.WORKSPACE}"
            }
            steps {
                sh '.venv/bin/python -m pytest -q tests'
            }
        }

        stage('Build image') {
            steps {
                sh 'docker build -t $IMAGE:$BUILD_NUMBER -t $IMAGE:latest .'
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker rm -f $CONTAINER 2>/dev/null || true
                    docker run -d --name $CONTAINER --restart unless-stopped \
                        -p $APP_PORT:8000 $IMAGE:$BUILD_NUMBER
                '''
            }
        }

        stage('Smoke test') {
            steps {
                sh '''
                    for i in $(seq 1 20); do
                        if curl -fs http://localhost:$APP_PORT/metrics | grep -q "$GIT_COMMIT"; then
                            curl -s http://localhost:$APP_PORT/metrics; echo
                            echo "New model is live on port $APP_PORT"
                            exit 0
                        fi
                        sleep 3
                    done
                    echo "Deployed container did not serve the new model"
                    docker logs --tail 50 $CONTAINER
                    exit 1
                '''
                // keep only the 3 newest numbered images
                sh '''
                    docker images $IMAGE --format '{{.Tag}}' | grep -E '^[0-9]+$' | sort -n | head -n -3 \
                        | xargs -r -I{} docker rmi $IMAGE:{} || true
                '''
            }
        }
    }

    post {
        always {
            script {
                def metrics = fileExists('artifacts/metrics.json') ? readFile('artifacts/metrics.json') : 'metrics.json was not produced'
                def authorEmail = ''
                def authorName = ''
                if (fileExists('.git')) {
                    authorEmail = sh(script: "git log -1 --pretty=format:'%ae'", returnStdout: true).trim()
                    authorName  = sh(script: "git log -1 --pretty=format:'%an'", returnStdout: true).trim()
                }
                // Mail whoever made the commit; I always get a blind copy.
                def recipients = authorEmail ? "${authorEmail}, bcc:${env.MAIL_BCC}" : env.MAIL_BCC
                emailext(
                    to: recipients,
                    from: env.MAIL_FROM,
                    subject: "[${env.STUDENT_ID}] MIDTERM-${env.STUDENT_ID} build #${env.BUILD_NUMBER}: ${currentBuild.currentResult}",
                    mimeType: 'text/plain',
                    body: """Student Reg No: ${env.STUDENT_ID}
Job: ${env.JOB_NAME} #${env.BUILD_NUMBER}
Result: ${currentBuild.currentResult}
Commit: ${env.GIT_COMMIT} by ${authorName} <${authorEmail}>

Metrics:
${metrics}

Live metrics: ${env.PUBLIC_URL}/metrics
Console log: ${env.BUILD_URL}console
"""
                )
            }
        }
    }
}
