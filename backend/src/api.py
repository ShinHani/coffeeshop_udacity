import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
with app.app_context():
    db_drop_and_create_all()

# ROUTES

@app.route('/drinks', methods=['GET'])
def get_drinks():
    '''
    Get all drinks.

    Return:
        Status code 200 and json {"success": True, "drinks": short_drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    '''
    drinks = Drink.query.all()
    short_drinks = [drink.short() for drink in drinks]
    return jsonify({
        'success': True,
        'drinks': short_drinks
    }), 200

@app.route('/drinks-detail', methods=['GET'])
@requires_auth(permission='get:drinks-detail')
def get_drinks_detail(payload):
    '''
    Get all drinks detail.

    Argument:
        payload: Payload from Auth0.

    Return:
        Status code 200 and json {"success": True, "drinks": long_drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure.
    '''
    drinks = Drink.query.all()
    long_drinks = [drink.long() for drink in drinks]
    return jsonify({
        'success': True,
        'drinks': long_drinks
    }), 200

@app.route('/drinks', methods=['POST'])
@requires_auth(permission='post:drinks')
def create_drink(payload):
    '''
    Create a new drink.

    Argument:
        payload: Payload from Auth0.

    Return:
        Status code 200 and json {"success": True, "drinks": [new_drink.long()]} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure.

    Raises:
        AuthError 403: If title or recipe is not provided.
    '''
    body = request.get_json()
    title = body.get('title')
    recipe = body.get('recipe')

    if  not title and not recipe:
        abort(403)

    new_drink = Drink(title=title, recipe=json.dumps(recipe))
    new_drink.insert()
    return jsonify({
        'success': True,
        'drinks': [new_drink.long()]
    }), 200

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    '''
    Update a drink.

    Argument: 
        payload: Payload from Auth0.
        id: Drink ID.

    Return:
        status code 200 and json {"success": True, "drinks": [drink.long()]} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure.
    
    Raises:
        AuthError 404: If the drink is not found.
        AuthError 400: If title or recipe is not provided.
    '''
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if not drink:
        abort(404)
    
    body = request.get_json()
    title = body.get('title', None)
    recipe = body.get('recipe', None)

    if not title and not recipe:
        abort(400)

    drink.title = title
    drink.recipe = json.dumps(recipe)
    drink.update()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    }), 200

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drink(payload, id):
    '''
    Delete a drink.

    Argument: 
        payload: Payload from Auth0.
        id: Drink ID.
    
    Return: 
        Status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure.
    
    Raises:
        AuthError 404: If the drink is not found.
    '''
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    
    if not drink:
        abort(404)

    drink.delete()

    return jsonify({
        'success': True,
        'delete': id
    }), 200

# Error Handling --------------------------------------------------------------

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({
    'success': False,
    'error': 404,
    'message': error.description
    }), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': error.description
    }), 400

@app.errorhandler(AuthError)
def handle_auth_error(e):
    return jsonify({
        "success": False,
        "error": e.status_code,
        "message": e.error['description']
    }), e.status_code