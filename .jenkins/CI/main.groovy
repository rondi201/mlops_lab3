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
        REPO_NAME = 'mlops_lab3'
        PROJECT_NAME = 'mlops-lab3'
        // Настройки внутри docker-container
        // Префикс в собираемых образах docker (если не master ветка - добавим префикс для исключения перезаписи образов)
        IMAGE_PREFIX = "${env.BRANCH_NAME == 'master' ? '' : env.BRANCH_NAME}"
        // Имя сборки
        BUILD_NAME = "${env.BRANCH_NAME == 'master' ? 'prod' : 'dev'}"
        // Имя секрета с паролем для Ansible Vault
        ANSIBLE_VAULT_CREDS_NAME = "ansible_vault_${BUILD_NAME}_password"
        // Зададим COMPOSE_PROJECT_NAME в зависимости от ветки, чтобы контейнеры не пересекались внутри агента
        COMPOSE_PROJECT_NAME = "${PROJECT_NAME}_${env.BRANCH_NAME}"
    }

    options {
        timestamps()
        skipDefaultCheckout(true)
    }
    stages {
        stage('Checkout repo') {
            steps {
                // Склонируем репозиторий из нужной ветки
                git branch: "${env.BRANCH_NAME}", url: "https://github.com/rondi201/${REPO_NAME}.git"
                // Выведем содержимое репозитория
                sh "ls -lash"
                sh 'whoami'
            }
        }

        stage('Get data files from DVC') {
            steps {
                sh "dvc remote modify --local minio endpointurl ${params.dvc_minio_url}"
                sh 'dvc remote modify --local minio access_key_id "${DVC_MINIO_CREDS_USR}"'
                sh 'dvc remote modify --local minio secret_access_key "${DVC_MINIO_CREDS_PSW}"'
                sh 'dvc pull'
                sh 'tree . --filelimit 50'
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
                    // Добавим цветовую тему
                    ansiColor('xterm') {
                        // Запустим сборку с помощью Ansible Playbook
                        ansiblePlaybook(
                            playbook: "playbooks/build.yaml",
                            colorized: true
                        )
                    }
                }
            }
        }

        stage('Check auto tests') {
            steps {
                script {
                    // Добавим цветовую тему
                    ansiColor('xterm') {
                        // Запустим автотесты с помощью Ansible Playbook
                        ansiblePlaybook(
                            playbook: "playbooks/test.yaml",
                            // Пароль от Ansible Vaults
                            vaultCredentialsId: "${ANSIBLE_VAULT_CREDS_NAME}",
                            colorized: true,
                            extraVars: [
                                db_vault_file: "vars/app_database/vault.${BUILD_NAME}.yaml"
                            ]
                        )
                    }
                }
            }
        }

        stage('Run docker container') {
            steps {
                script {
                    // Добавим цветовую тему
                    ansiColor('xterm') {
                        // Запустим контейнера с помощью Ansible Playbook
                        ansiblePlaybook(
                            playbook: "playbooks/up.yaml",
                            // Пароль от Ansible Vaults
                            vaultCredentialsId: "${ANSIBLE_VAULT_CREDS_NAME}",
                            colorized: true,
                            extraVars: [
                                db_vault_file: "vars/app_database/vault.${BUILD_NAME}.yaml",
                                wait_timeout: 180
                            ]
                        )
                    }
                }
            }
        }

        stage('Check container logs') {
            steps {
                script {
                    sh '''
                        containerId=$(docker ps -qf "name=^${COMPOSE_PROJECT_NAME}-api")
                        if [[ -z "$containerId" ]]; then
                            echo "No container running"
                        else
                            docker logs --tail 100 "$containerId"
                        fi
                    '''
                }
            }
        }

        stage('Push') {
            // Отправим образ только при сборке release версии из ветки master
            when{
                branch 'master'
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
                if (fileExists("docker-compose.yaml")) {
                    // Остановим контейнеры и удалим volume с помощью Ansible Playbook
                    ansiblePlaybook(
                        playbook: "playbooks/down.yaml",
                        extraVars: [
                            with_volumes: true
                        ]
                    )
                }
            }
            cleanWs()
        }
    }
}
