FROM public.ecr.aws/docker/library/alpine:latest as layer-copy 

ARG AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-"eu-west-1"}
ARG AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-""}
ARG AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-""}
ENV AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}

RUN apk add aws-cli curl unzip

RUN mkdir -p /opt

ARG TARGETARCH
RUN curl $(aws lambda get-layer-version-by-arn --arn arn:aws:lambda:${AWS_DEFAULT_REGION}:901920570463:layer:aws-otel-python-${TARGETARCH}-ver-1-14-0:1 --query 'Content.Location' --output text) --output layer.zip
RUN unzip layer.zip -d /opt

FROM public.ecr.aws/docker/library/python:3.10-slim
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.5.1 /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /opt
COPY --from=layer-copy /opt .

WORKDIR /app

COPY src/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY src .

ENV OPENTELEMETRY_COLLECTOR_CONFIG_FILE='/app/collector-config.yaml'

CMD /opt/otel-instrument flask run --host=0.0.0.0 --port=8080

EXPOSE 8080