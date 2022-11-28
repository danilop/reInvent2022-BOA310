export REGION=$(aws configure get region)
export ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

aws ecr delete-repository --repository-name guess-the-number-auto --force
aws ecr delete-repository --repository-name guess-the-number-manual --force
aws ecr delete-repository --repository-name guess-the-number-manual-lambda --force

aws ecr create-repository --repository-name guess-the-number-auto
aws ecr create-repository --repository-name guess-the-number-manual
aws ecr create-repository --repository-name guess-the-number-manual-lambda

aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

docker buildx create --use

cd GuessTheNumber-Auto
docker buildx build --platform linux/amd64,linux/arm64 --push -t ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/guess-the-number-auto .
cd ..

cd GuessTheNumber-Manual
docker buildx build --platform linux/amd64,linux/arm64 --push -t ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/guess-the-number-manual .
cd ..

cd GuessTheNumber-Manual-Lambda
docker buildx build --platform linux/arm64 --push -t ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/guess-the-number-manual-lambda . \
    --build-arg AWS_DEFAULT_REGION=${REGION} \
    --build-arg AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id) \
    --build-arg AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
cd ..
