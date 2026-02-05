"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import requests
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Location
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_hello():
    response_body = {
        "msg": "Hello, this is your GET /user response "
    }
    return jsonify(response_body), 200

# ----ENDPOINTS CREADOS-----

# [GET] /people Listar todos los registros de people en la base de datos.
@app.route('/simpsons-characters', methods=['GET'])
def get_simpsons_characters():
    response = requests.get('https://thesimpsonsapi.com/api/characters')
    data = response.json()
    return jsonify(data), 200

# [GET] /people/<int:people_id> Muestra la información de un solo personaje según su id.
@app.route('/simpsons-characters/<int:character_id>', methods=['GET'])
def get_simpsons_character(character_id):
    response = requests.get(
        f'https://thesimpsonsapi.com/api/characters/{character_id}')
    character = response.json()
    if not character:
        return jsonify({"error": "Character not found"}), 404
    return jsonify(character), 200

# [GET] /planets Listar todos los registros de planets en la base de datos.
@app.route('/simpsons-locations', methods=['GET'])
def get_simpsons_locations():
    response = requests.get('https://thesimpsonsapi.com/api/locations')
    data = response.json()
    return jsonify(data), 200

# [GET] /planets/<int:planet_id> Muestra la información de un solo planeta según su id.
@app.route('/simpsons-locations/<int:location_id>', methods=['GET'])
def get_simpsons_location(location_id):
    response = requests.get(
        f'https://thesimpsonsapi.com/api/locations/{location_id}')
    location = response.json()
    if not location:
        return jsonify({"error": "Location not found"}), 404
    return jsonify(location), 200

# [GET] /users Listar todos los usuarios del blog.
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    users_list = []
    for user in users:
        users_list.append(user.serialize())
    return jsonify(users_list), 200

# [GET] /users/favorites Listar todos los favoritos que pertenecen al usuario actual.
@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    # para leer parametros de la url y si no hay id usa 1 por defecto y lo convierte a entero
    user_id = request.args.get('user_id', 1, type=int)
    user = User.query.get(user_id)  # para buscar el id del usuario de la db

    if not user:
        return jsonify({"message": "User not found"}), 404

    characters = []
    for character in user.favs_characters:
        characters.append(character.serialize())

    locations = []  # lista vacia
    for location in user.favs_locations: # Para cada 'location' en user.favs_locations:
        locations.append(location.serialize()) # Agregamos a la lista el resultado de location.serialize()"

    return jsonify({
        "characters": characters,
        "locations": locations
    }), 200

# POST] /favorite/planet/<int:planet_id> Añade un nuevo planet favorito al usuario actual con el id = planet_id.
@app.route('/favorite/location/<int:location_id>', methods=['POST'])
def add_location_favorite(location_id):
    user_id = request.args.get('user_id', 1, type=int)
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404 #si no hay user en la db, error

    location = Location.query.get(location_id)
    if not location:
        return jsonify({"message": "Location not found"}), 404 #si no hay location en la db, error

    if location in user.favs_locations: #para evitar duplicado
        return jsonify({"message": "Already favorite"}), 409

    user.favs_locations.append(location) #agrega a la lista de fav
    db.session.commit() #guarda en la DB

    return jsonify({
        "message": "Location added to favorites",
        "location_id": location_id,
        "user_id": user_id
    }), 201

#[POST] /favorite/people/<int:people_id> Añade un nuevo people favorito al usuario actual con el id = people_id.
@app.route('/favorite/character/<int:character_id>', methods=['POST'])
def add_character_favorite(character_id):
    user_id = request.args.get('user_id', 1, type=int)
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    character = Character.query.get(character_id)
    if not character:
        return jsonify({"message": "Character not found"}), 404
    
    if character in user.favs_characters:
        return jsonify({"message": "Already favorite"}), 409
    
    user.favs_characters.append(character)
    db.session.commit()
    
    return jsonify({
        "message": "Character added to favorites",
        "character_id": character_id,
        "user_id": user_id
    }), 201

#[DELETE] /favorite/planet/<int:planet_id> Elimina un planet favorito con el id = planet_id.
@app.route('/favorite/location/<int:location_id>', methods=['DELETE'])
def remove_location_favorite(location_id):
    user_id = request.args.get('user_id', 1, type=int)
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    location = Location.query.get(location_id)
    if not location:
        return jsonify({"message": "Location not found"}), 404
    
    if location not in user.favs_locations:
        return jsonify({"message": "Not a favorite"}), 404
    
    user.favs_locations.remove(location)
    db.session.commit()
    
    return jsonify({
        "message": "Location removed from favorites",
        "location_id": location_id,
        "user_id": user_id
    }), 200

#[DELETE] /favorite/people/<int:people_id> Elimina un people favorito con el id = people_id.
@app.route('/favorite/character/<int:character_id>', methods=['DELETE'])
def remove_character_favorite(character_id):
    user_id = request.args.get('user_id', 1, type=int)
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    character = Character.query.get(character_id)
    if not character:
        return jsonify({"message": "Character not found"}), 404
    
    if character not in user.favs_characters:
        return jsonify({"message": "Not a favorite"}), 404
    
    user.favs_characters.remove(character)
    db.session.commit()
    
    return jsonify({
        "message": "Character removed from favorites",
        "character_id": character_id,
        "user_id": user_id
    }), 200









    # this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
