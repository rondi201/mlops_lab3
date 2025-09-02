pipeline {
    agent any
    environment {
        DOCKERHUB_CREDS = credentials('dockerhub')
        REPO_NAME = 'mlops_lab2'
        // Имя сборки
        BUILD_NAME = "${env.BRANCH_NAME == 'master' ? 'prod' : 'dev'}"
        // Имя секрета с паролем для Ansible Vault
        ANSIBLE_VAULT_CREDS_NAME = "ansible_vault_${BUILD_NAME}_password"
    }

    options {
        timestamps()
        skipDefaultCheckout(true)
    }
    stages {
        stage('Login') {
            steps {
                sh 'docker login -u ${DOCKERHUB_CREDS_USR} -p ${DOCKERHUB_CREDS_PSW}'
            }
        }

        // Ввиду отсутствия отдельного проекта-сборки загрузим весь проект ради docker-compose файла
        stage('Checkout repo dir') {
            steps {
                    sh 'git clone https://github.com/rondi201/${REPO_NAME}.git'
                    sh 'ls -lash'
                    sh 'whoami'
            }
        }

        stage('Pull image'){
            steps{
                sh 'docker compose pull'
            }
        }

        stage('Run services'){
            steps{
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

    post {
        always {
            sh 'docker logout'
            // Остановим сервисы, т.к. CD часть тестовая и не подразумевает последующую работу контейнеров
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