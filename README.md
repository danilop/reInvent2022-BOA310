# reInvent2022-BOA310
Code used at re:Invent 2022 for session BOA310 "Building observable applications with OpenTelemetry"

## Role

Create a role using:
- Role/trust.json for the trust relationships
- Role/policy.json for permissions

Add these managed policies the the permissions:
- AWSXRayDaemonWriteAccess
- AmazonPrometheusRemoteWriteAccess

## Container images

The container image for th eLambda funciton is built for the arm64 architecture.
The other container images are multi-arch and support both amd64 and arm64.

## AppRunner

Create two services, one using the guess-the-number-auto container image, one using the guess-the-number-manual image. For both, enable Observability (Tracing with AWS X-Ray) in the Service settings.

## ECS

Create a service using the guess-the-number-manual image. Add observability using the console as described in this blog post:
https://aws.amazon.com/blogs/opensource/simplifying-amazon-ecs-monitoring-set-up-with-aws-distro-for-opentelemetry/

## Lambda

Create an arm64 function using the guess-the-number-manual-lambda ontainer image.
Create a function using the AWS SAM CLI and the app in the GuessTheNumber-SAM directory.
