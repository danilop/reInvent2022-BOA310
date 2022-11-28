FROM public.ecr.aws/docker/library/python:3.10-slim

WORKDIR /app

COPY src/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY src .

RUN opentelemetry-bootstrap -a install

ENV OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=urllib3
ENV OTEL_RESOURCE_ATTRIBUTES='service.name=guess-the-number'

CMD OTEL_PROPAGATORS=xray OTEL_PYTHON_ID_GENERATOR=xray opentelemetry-instrument flask run --host=0.0.0.0 --port=8080

EXPOSE 8080