pipeline {
    agent any
    parameters {
        string(name: "dvc_minio_url", defaultValue: "http://172.30.128.1:9000", trim: true, description: "Путь для доступа к S3 Minio Storage для загрузки данных из DVC")
    }
    environment {
        DOCKERHUB_CREDS=credentials('mlops_lab')
        DVC_MINIO_CREDS=credentials('dvc_minio')
        REPO_NAME='mlops_lab1'
        PROJECT_NAME='mlops-lab1'
    }

options {
        timestamps()
        skipDefaultCheckout(true)
	}
    stages {
        stage('Checkout repo dir') {
            steps {
                    sh 'git clone https://github.com/rondi201/${REPO_NAME}.git'
                    sh 'cd ${REPO_NAME} && ls -lash'
                    sh 'whoami'
				}
			}

        stage('Get data files') {
            steps {
                dir("${REPO_NAME}") {
                    sh "dvc remote modify --local minio endpointurl ${params.dvc_minio_url}"
                    sh 'dvc remote modify --local minio access_key_id "${DVC_MINIO_CREDS_USR}"'
                    sh 'dvc remote modify --local minio secret_access_key "${DVC_MINIO_CREDS_PSW}"'
                    sh 'dvc pull'
                    sh 'tree . --filelimit 50'
                }
            }
        }

        stage('Login'){
            steps{
                    sh 'docker login -u ${DOCKERHUB_CREDS_USR} -p ${DOCKERHUB_CREDS_PSW}'
                }
            }

        stage('Create and run docker container') {
            steps {
                script {
                    try {
                            sh 'cd ${REPO_NAME} && docker compose build'
                        }

                    finally {
                            sh 'cd ${REPO_NAME} && docker compose up -d'
                        }
				    }
                }
            }

        stage('Check container healthy') {
            options {
                timeout(time: 180, unit: 'SECONDS')
            }
            steps {
                dir("${REPO_NAME}") {
                    sh '''
                        containerId=$(docker ps -qf "name=^${PROJECT_NAME}-api")
                        until [ "`docker inspect -f {{.State.Health.Status}} $containerId`"=="healthy" ]; do
                            sleep 0.1;
                        done;
                    '''
                }
            }
        }

        stage('Checkout container logs') {
            steps {
                dir("${REPO_NAME}") {
                    script {
                        try {
                            timeout(time: 30, unit: 'SECONDS') {
                                sh '''
                                    containerId=$(docker ps -qf "name=^${PROJECT_NAME}-api")
                                    if [[ -z "$containerId" ]]; then
                                        echo "No container running"
                                    else
                                        docker logs --tail 100 -f "$containerId"
                                    fi
                                '''
                            }
                        }
                        catch (err) {}
                    }
                }
            }
        }

        stage('Checkout coverage report'){
            steps{
                dir("${REPO_NAME}"){
                        sh '''
                        docker compose logs -t --tail 10
                        '''
                }
            }
        }

        stage('Push'){
            steps{
                    sh 'docker push ${DOCKERHUB_CREDS_USR}/${PROJECT_NAME}-api:latest'
            }
        }
	}

    post {
        always {
                sh 'docker logout'
                script {
                    if (fileExists("${REPO_NAME}/docker-compose.yaml")) {
                        sh 'cd ${REPO_NAME} && docker compose down -v'
                    }
                }
                cleanWs()
        }
    }
}