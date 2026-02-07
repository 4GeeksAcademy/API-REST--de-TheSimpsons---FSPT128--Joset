from flask import Blueprint, jsonify
from models import db, Character, Location, User
from sqlalchemy import select

api = Blueprint("api", __name__)

#[GET] /characters Listar todos los registros de characters en la base de datos.
@api.route("/characters", methods=["GET"])
def get_characters():
    characters = db.session.execute(    #metodo moderno. Execute devuelve filar
        select(Character)               #listar todos los registros de character. equivale a SELECT * FROM character en SQL
    ).scalars().all()                   # scalars: extrae objeto de character ---all: los convierte en listas
    response = [character.serialize() for character in characters]
    return jsonify(response), 200


#[GET] /characters/<int:characters_id> Muestra la información de un solo personaje según su id.
@api.route("/characters/<int:character_id>", methods=["GET"])
def get_character(character_id):
    character = db.session.get(Character, character_id) #En SQL seria: SELECT * FROM character WHERE id = character_id;
                                                        #estructura moderna: db.session.get(Model, id). Buscamos por PK
    if character is None:
        return jsonify({"msg": "Character not found"}), 404

    return jsonify(character.serialize()), 200



#[GET] /planets Listar todos los registros de planets en la base de datos.
@api.route("/locations", methods=["GET"])
def get_locations():
    locations = db.session.execute(     
        select(Location)                
    ).scalars().all()                   

    response = [location.serialize() for location in locations]  # conveierte cada objeto a diccionario JSON
    return jsonify(response), 200


#[GET] /planets/<int:planet_id> Muestra la información de un solo planeta según su id.
def get_location(location_id):
    location = db.session.get(Location, location_id)  

    if location is None:
        return jsonify({"msg": "Location not found"}), 404

    return jsonify(location.serialize()), 200

#[GET] /users Listar todos los usuarios del blog.
# @api.route("/users", methods=["GET"]) ------METODO TRADICIONAL VISTO EN CLASE-----
# def get_users():
#     users = User.query.all()
#     response = [user.serialize() for user in users]
#     return jsonify(response), 200

@api.route("/users", methods=["GET"])
def get_users():
    users = db.session.execute(
        select(User)               
    ).scalars().all()            

    response = [user.serialize() for user in users]  
    return jsonify(response), 200

#[GET] /users/favorites Listar todos los favoritos que pertenecen al usuario actual.
@api.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    user = db.session.get(User, user_id)  # Buscar usuario por ID 

    if user is None:
        return jsonify({"msg": "User not found"}), 404

    # relaciones muchos a muchos
    fav_characters = [character.serialize() for character in user.favs_characters]
    fav_locations = [location.serialize() for location in user.favs_locations]

    return jsonify({
        "fav_characters": fav_characters,
        "fav_locations": fav_locations
    }), 200



#[POST] /favorite/planet/<int:planet_id> Añade un nuevo planet favorito al usuario actual con el id = planet_id.
@api.route('/users/<int:user_id>/favorite/location/<int:location_id>', methods=['POST'])
def add_favorite_location(user_id, location_id):
    user = db.session.get(User, user_id)                # Buscarr al  usuario
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    location = db.session.get(Location, location_id)    # Buscar la location
    if location is None:
        return jsonify({"msg": "Location not found"}), 404

    if location in user.favs_locations:                 # este if es para evitar duplicados
        return jsonify({"msg": "Location already in favorites"}), 400

    user.favs_locations.append(location)                # Agregar a favoritos
    db.session.commit()

    return jsonify({"msg": f"{location.name} added to favorites"}), 201

#[POST] /favorite/characters/<int:people_id> Añade un nuevo characters favorito al usuario actual con el id = people_id.
@api.route('/users/<int:user_id>/favorite/character/<int:character_id>', methods=['POST'])
def add_favorite_character(user_id, character_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    character = db.session.get(Character, character_id)
    if character is None:
        return jsonify({"msg": "Character not found"}), 404

    if character in user.favs_characters:
        return jsonify({"msg": "Character already in favorites"}), 400

    user.favs_characters.append(character)
    db.session.commit()

    return jsonify({"msg": f"{character.name} added to favorites"}), 201


#[DELETE] /favorite/planet/<int:planet_id> Elimina un planet favorito con el id = planet_id.
@api.route('/users/<int:user_id>/favorite/location/<int:location_id>', methods=['DELETE'])
def delete_favorite_location(user_id, location_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"msg": "User not found"}), 404
    
    location = db.session.get(Location, location_id)
    if location is None:
        return jsonify({"msg": "Location not found"}), 404

    if location not in user.favs_locations:    # Necesitamos ver si el usuario ya tiene la location en favoritos.
        return jsonify({"msg": "Location is not in favorites"}), 400

    user.favs_locations.remove(location)        # Elimina de favoritos
    db.session.commit()

    return jsonify({"msg": f"{location.name} removed from favorites"}), 200


#[DELETE] /favorite/characters/<int:people_id> Elimina un characters favorito con el id = people_id.
@api.route('/users/<int:user_id>/favorite/character/<int:character_id>', methods=['DELETE'])
def delete_favorite_character(user_id, character_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"msg": "User not found"}), 404

    character = db.session.get(Character, character_id)
    if character is None:
        return jsonify({"msg": "Character not found"}), 404

    if character not in user.favs_characters:
        return jsonify({"msg": "Character is not in favorites"}), 400

    user.favs_characters.remove(character)
    db.session.commit()

    return jsonify({"msg": f"{character.name} removed from favorites"}), 200


#obtener un usuario en especifico, aunque no lo piden en el proyecto (visto en clase)
@api.route("/users/<int:user_id>",methods=["GET"])
def get_user(user_id):
    user = User.query.get(user_id) 
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.serialize()), 200

#crear usuario, (visto en clase)
@api.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400
    
    new_user = User(
        email= data["email"],
        password = data["password"]
    )


    db.session.add(new_user)   # Añade el nuevo usuario a la sesión de la base de datos, listo para ser guardado
    db.session.commit()        # Guarda todos los cambios pendientes en la base de datos  
    return jsonify(new_user.serialize()), 201  # Devuelve el usuario creado en formato JSON












 