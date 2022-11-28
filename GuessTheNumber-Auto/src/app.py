import random
import time
import uuid

import flask
from flask import Flask, render_template, jsonify, redirect

import boto3
from boto3.dynamodb.conditions import Attr

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

    location = flask.url_for('describe_game', game_id = game['id'])
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

    return game


def get_game(game_id):

    resp = guess_the_number_table.get_item(Key={'id': game_id})

    try:
        game = resp['Item']
    except KeyError:
        game = None
        raise Exception('GameNotFound')

    return game


def incremet_attempts(game_id):

    resp = guess_the_number_table.update_item(
        Key={
            'id': game_id
        },
        ConditionExpression=Attr('won').eq(False),
        UpdateExpression='SET attempts = attempts + :val',
        ExpressionAttributeValues={
            ':val': 1
        },
        ReturnValues='UPDATED_NEW'
    )

    attempts = resp['Attributes']['attempts']

    return attempts


def win_game(game_id):

    resp = guess_the_number_table.update_item(
        Key={
            'id': game_id
        },
        ConditionExpression=Attr('won').eq(False),
        UpdateExpression='SET won = :val1, attempts = attempts + :val2',
        ExpressionAttributeValues={
            ':val1': True,
            ':val2': 1
        },
        ReturnValues='UPDATED_NEW'
    )

    # Check that the table update worked
    try:
        attempts = resp['Attributes']['attempts']
    except KeyError:
        return 0

    # Send SQS message to winners queue
    resp = guess_the_number_winners_queue.send_message(
        MessageBody='There is a winner in {} attempts!'.format(attempts)
    )
    print(resp.get('MessageId'))
    print(resp.get('MD5OfMessageBody'))

    return attempts
