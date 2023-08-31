#!/usr/bin/env bash
set -e

read -p "Barcodez environment to deploy to? [production/staging]: " APP_ENVIRONMENT

# make sure envsubst can read the var
export APP_ENVIRONMENT=$APP_ENVIRONMENT
export DATE_TIMESTAMP=$(echo $(date +"%Y-%m-%dT%H%M%SZ"))
export IMAGE_TAG=$APP_ENVIRONMENT-$DATE_TIMESTAMP

echo "
----------------
ENVIRONMENT > $APP_ENVIRONMENT
----------------
"

if [[ "$APP_ENVIRONMENT" == "production" || "$APP_ENVIRONMENT" == "staging" ]]; then

    echo "Building and publishing Docker image"

    # build Docker image with tag matching the current environment and date timestamp
    docker build --build-arg GO_ENV=$APP_ENVIRONMENT -t barcodez:$IMAGE_TAG .
    # create matching remote Docker image tags
    docker tag barcodez:$IMAGE_TAG 947453556251.dkr.ecr.us-east-1.amazonaws.com/barcodez:$IMAGE_TAG
    # authenticate to Amazon ECR registry with Docker
    aws --region us-east-1 ecr get-login-password | docker login --username AWS --password-stdin 947453556251.dkr.ecr.us-east-1.amazonaws.com/barcodez
    # push docker images to remote repository
    docker push 947453556251.dkr.ecr.us-east-1.amazonaws.com/barcodez:$IMAGE_TAG

    APP_RUNNER_SERVICE=$(aws apprunner list-services --query 'ServiceSummaryList[?ServiceName==`barcodez-'$APP_ENVIRONMENT'`].ServiceArn' --output text)

    echo "Start App Runner Service update"
    APP_RUNNER_OPERATION_ID=$(aws apprunner update-service --service-arn "$APP_RUNNER_SERVICE" \
        --source-configuration '{"ImageRepository": {"ImageIdentifier": "947453556251.dkr.ecr.us-east-1.amazonaws.com/barcodez:'$IMAGE_TAG'", "ImageRepositoryType": "ECR"}}' --query 'OperationId')

    aws apprunner list-operations --service-arn $APP_RUNNER_SERVICE --query 'OperationSummaryList[?Id==`'$APP_RUNNER_OPERATION_ID'`]'
    
    echo "Invoked app deployment of version $IMAGE_TAG to Barcodez $APP_ENVIRONMENT"
else
	echo "Invalid app environment"
fi