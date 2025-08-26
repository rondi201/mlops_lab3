pipeline {
    agent any
    parameters {
        string(
            name: 'dvc_minio_url',
            defaultValue: 'http://172.17.0.1:9000',
            trim: true,
            description: 'Путь для доступа к S3 Minio Storage для загрузки данных из DVC'
        )
    }
    environment {
        DOCKERHUB_CREDS = credentials('dockerhub')
        DVC_MINIO_CREDS = credentials('dvc_minio')
        DB_CREDS = credentials('mlops_lab_database')
        REPO_NAME = 'mlops_lab2'
        PROJECT_NAME = 'mlops-lab2'
        // Настройки внутри docker-container
        // Префикс в собираемых образах docker (если не master ветка - добавим префикс для исключения перезаписи образов)
        IMAGE_PREFIX = "${env.BRANCH_NAME == 'master' ? '' : env.BRANCH_NAME}"
        // Зададим COMPOSE_PROJECT_NAME в зависимости от ветки, чтобы контейнеры не пересекались внутри агента
        COMPOSE_PROJECT_NAME = "${PROJECT_NAME}_${env.BRANCH_NAME}"
    }

    options {
        timestamps()
        skipDefaultCheckout(true)
    }
    stages {
        stage('Checkout repo dir') {
            steps {
                    // Склонируем репозиторий и перейдём в него
                    sh "git clone https://github.com/rondi201/${REPO_NAME}.git"
                    // Сменим ветку на текущую (доступно при создании multibranch pipeline)
                    sh "cd ${REPO_NAME} && git checkout ${env.BRANCH_NAME}"
                    sh "cd ${REPO_NAME} && ls -lash"
                    sh 'whoami'
            }
        }

        stage('Get data files from DVC') {
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

        stage('Login') {
            steps {
                    sh 'docker login -u ${DOCKERHUB_CREDS_USR} -p ${DOCKERHUB_CREDS_PSW}'
            }
        }

        stage('Build docker container') {
            steps {
                script {
                    dir("${REPO_NAME}") {
                        sh 'docker compose build'
                    }
                }
            }
        }

        stage('Check auto tests') {
            steps {
                script {
                    dir("${REPO_NAME}") {
                        // Поднимем контейнеры для автотестов и завершим работу после их прохождения
                        sh 'docker compose -f docker-compose.autotest.yaml --env-file .env.autotest up \
                            --abort-on-container-exit \
                            --exit-code-from api-autotest'
                        // удалим контейнеры автотестов
                        sh 'docker compose -f docker-compose.autotest.yaml --env-file .env.autotest down -v'
                    }
                }
            }
        }

        stage('Run docker container') {
            steps {
                script {
                    dir("${REPO_NAME}") {
                        sh 'docker compose up -d \
                            -e DB_USER=${DB_CREDS_USR} \
                            -e DB_PASSWORD=${DB_CREDS_PSW}'
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
                        catch (err) { }
                    }
                }
            }
        }

        // stage('Checkout coverage report'){
        //     steps{
        //         dir("${REPO_NAME}"){
        //                 sh '''
        //                 docker compose logs -t --tail 25
        //                 '''
        //         }
        //     }
        // }

        stage('Push') {
            // Отправим образ только при сборке release версии из ветки master
            when{
                branch master
            }
            steps {
                    sh 'docker push ${DOCKERHUB_CREDS_USR}/${PROJECT_NAME}-api:latest'
            }
        }
    }

    post {
        always {
                // Выйдем из docker
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
