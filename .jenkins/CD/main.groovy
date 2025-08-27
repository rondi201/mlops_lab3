pipeline {
    agent any

    environment {
        DOCKERHUB_CREDS=credentials('mlops_lab')
        DB_CREDS = credentials('mlops_lab_database')
        REPO_NAME='mlops_lab2'
        PROJECT_NAME='mlops_lab2'
    }

options {
        timestamps()
        skipDefaultCheckout(true)
	}
    stages {
        stage('Login'){
            steps{
                    sh 'docker login -u ${DOCKERHUB_CREDS_USR} -p ${DOCKERHUB_CREDS_PSW}'
            }
        }

        // Ввиду отсутствия отдельного проекта-сборки загрузим весь проект ради docker-compose файла
        stage('Checkout repo dir') {
            steps {
                    sh 'git clone https://github.com/rondi201/${REPO_NAME}.git'
                    sh 'cd ${REPO_NAME} && ls -lash'
                    sh 'whoami'
            }
        }

        stage('Pull image'){
            steps{
                dir("${REPO_NAME}") {
                    sh 'docker compose pull'
                }
            }
        }

        stage('Run services'){
            steps{
                dir("${REPO_NAME}") {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'mlops_lab_database', 
                            usernameVariable: 'DB_USER',
                            passwordVariable: 'DB_PASSWORD'
                        )
                    ]) {
                        sh 'docker compose up -d'
                    }
                }
            }
        }
	}

    post {
        always {
            sh 'docker logout'
            // Остановим сервисы, т.к. CD часть тестовая и не подразумевает последующую работу контейнеров
            script {
                if (fileExists("${REPO_NAME}/docker-compose.yaml")) {
                    sh 'cd ${REPO_NAME} && docker compose down -v'
                }
            }
            cleanWs()
        }
    }
}