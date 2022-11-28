# START OpenTelemetry Manual Instrumentation
from opentelemetry import trace
from opentelemetry import metrics
# END OpenTelemetry Manual Instrumentation

import uuid
import time
import random

import boto3
from boto3.dynamodb.conditions import Attr
import flask
from flask import Flask, render_template, jsonify, redirect

# START OpenTelemetry Manual Instrumentation
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

game_counter = meter.create_counter(
    "game.counter", unit="1", description="Counts the number of games"
)

game_not_found_counter = meter.create_counter(
    "game.notFound", unit="1", description="Counts the number of game IDs not found"
)

attempt_counter = meter.create_counter(
    "attempt.counter", unit="1", description="Counts the number of attempts"
)

won_counter = meter.create_counter(
    "won.counter", unit="1", description="Counts the amount of won games"
)

already_won_counter = meter.create_counter(
    "won.already", unit="1", description="Counts the amount of games already won"
)
# END OpenTelemetry Manual Instrumentation


TABLE_NAME = 'guess-the-number'
QUEUE_NAME = 'guess-the-number-winners'

TTL = 24 * 60 * 60  # 1 day

MIN_NUMBER = 1
MAX_NUMBER = 100

dynamodb = boto3.resource('dynamodb')
sqs = boto3.resource('sqs')

guess_the_number_table = dynamodb.Table(TABLE_NAME)
guess_the_number_winners_queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)


app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/game')
def new_game():

    game = create_game()

    location = flask.url_for('describe_game', game_id=game['id'])
    print("new_game " + location)
    return redirect(location)


@app.route('/game/<game_id>')
def describe_game(game_id):

    game = get_game(game_id)

    if game == None or game['won']:
        location = flask.url_for('new_game')
        print("describe_game " + location)
        return redirect(location)

    del game['number']
    return jsonify(game)


@app.route('/game/<game_id>/<int:guess>')
def play_game(game_id, guess):

    try:
        game = get_game(game_id)
    except Exception as e:
        s = str(e)
        if s == 'GameNotFound' or s == 'GameWon':
            location = flask.url_for('new_game')
            print("play_game " + location)
            return redirect(location)

    won = False
    if guess > game['number']:
        message = "too big"
        attempts = incremet_attempts(game['id'])
    elif guess < game['number']:
        message = "too small"
        attempts = incremet_attempts(game['id'])
    else:
        attempts = win_game(game['id'])
        if attempts > 0:
            message = "correct"
            won = True
        else:
            message = "already won"

    response = {
        'message': message,
        'attempts': attempts,
        'won': won
    }

    return jsonify(response)


# ANNOTATION OpenTelemetry Manual Instrumentation
@tracer.start_as_current_span("create_game")
def create_game():
    game_id = str(uuid.uuid4())

    random_number = random.randint(MIN_NUMBER, MAX_NUMBER)
    game_ttl = int(time.time()) + TTL

    game = {
        'id': game_id,
        'min': MIN_NUMBER,
        'max': MAX_NUMBER,
        'number': random_number,
        'attempts': 0,
        'won': False,
        'ttl': game_ttl
    }

    guess_the_number_table.put_item(Item=game)

    # START OpenTelemetry Manual Instrumentation
    game_counter.add(1)
    current_span = trace.get_current_span()
    current_span.set_attribute("game.id", game_id)
    current_span.set_attribute("game.number", random_number)
    # END OpenTelemetry Manual Instrumentation

    return game


# ANNOTATION OpenTelemetry Manual Instrumentation
# @tracer.start_as_current_span("get_game")
def get_game(game_id):
    # START OpenTelemetry Manual Instrumentation
    with tracer.start_as_current_span("get_game") as span:
    # END OpenTelemetry Manual Instrumentation

        resp = guess_the_number_table.get_item(Key={'id': game_id})

        try:
            game = resp['Item']
            # START OpenTelemetry Manual Instrumentation
            span.set_attribute("game.id", game_id)
            span.set_attribute("game.attempts", int(game['attempts']))
            # END OpenTelemetry Manual Instrumentation
        except KeyError:
            game=None
            # START OpenTelemetry Manual Instrumentation
            game_not_found_counter.add(1)
            span.set_attribute("game.notFound", game_id)
            # END OpenTelemetry Manual Instrumentation
            raise Exception('GameNotFound')

        return game


# ANNOTATION OpenTelemetry Manual Instrumentation
@tracer.start_as_current_span("incremet_attempts")
def incremet_attempts(game_id):

    resp=guess_the_number_table.update_item(
        Key={
            'id': game_id
        },
        ConditionExpression = Attr('won').eq(False),
        UpdateExpression = 'SET attempts = attempts + :val',
        ExpressionAttributeValues = {
            ':val': 1
        },
        ReturnValues = 'UPDATED_NEW'
    )

    # Check that the table update worked
    try:
        attempts=resp['Attributes']['attempts']
    except KeyError:
        # START OpenTelemetry Manual Instrumentation
        game_not_found_counter.add(1)
        current_span=trace.get_current_span()
        current_span.set_attribute("game.notFound", game_id)
        # END OpenTelemetry Manual Instrumentation
        return 0

    # START OpenTelemetry Manual Instrumentation
    attempt_counter.add(1)
    current_span=trace.get_current_span()
    current_span.set_attribute("game.id", game_id)
    current_span.set_attribute("game.attempts", int(attempts))
    # END OpenTelemetry Manual Instrumentation

    return attempts


# ANNOTATION OpenTelemetry Manual Instrumentation
@tracer.start_as_current_span("win_game")
def win_game(game_id):

    resp=guess_the_number_table.update_item(
        Key = {
            'id': game_id
        },
        ConditionExpression = Attr('won').eq(False),
        UpdateExpression = 'SET won = :val1, attempts = attempts + :val2',
        ExpressionAttributeValues = {
            ':val1': True,
            ':val2': 1
        },
        ReturnValues = 'UPDATED_NEW'
    )

    # Check that the table update worked
    try:
        attempts=resp['Attributes']['attempts']
    except KeyError:
        # START OpenTelemetry Manual Instrumentation
        current_span=trace.get_current_span()
        current_span.set_attribute("game.id", game_id)
        # END OpenTelemetry Manual Instrumentation
        return 0

    # Send SQS message to winners queue
    resp=guess_the_number_winners_queue.send_message(
        MessageBody = 'There is a winner in {} attempts!'.format(attempts)
    )

    # START OpenTelemetry Manual Instrumentation
    won_counter.add(1)
    current_span=trace.get_current_span()
    current_span.set_attribute("game.id", game_id)
    current_span.set_attribute("game.attempts", int(attempts))
    # END OpenTelemetry Manual Instrumentation

    return attempts
