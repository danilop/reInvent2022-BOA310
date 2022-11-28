cd GuessTheNumber-Auto
docker build --tag guess-the-number-auto .
cd ..

cd GuessTheNumber-Auto-Lambda
docker build --tag guess-the-number-auto-lambda . \
    --build-arg AWS_DEFAULT_REGION=eu-west-1 \
    --build-arg AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id) \
    --build-arg AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
cd ..

cd GuessTheNumber-Manual
docker build --tag guess-the-number-manual .
cd ..

cd GuessTheNumber-Manual-Lambda
docker build --tag guess-the-number-manual-lambda . \
    --build-arg AWS_DEFAULT_REGION=eu-west-1 \
    --build-arg AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id) \
    --build-arg AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
cd ..
