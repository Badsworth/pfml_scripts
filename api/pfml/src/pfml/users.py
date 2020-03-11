import connexion
import flask
import pfml.generate_fake_data as fake

# since there is no DB connection, dictionary will hold all users
users = {}

def users_get(user_id):
    try:
        user = users[user_id]
    except KeyError:
        not_found_error = flask.Response(status=404)
        return not_found_error

    return user

def users_post():
    body = connexion.request.json
    email = body.get('email')
    auth_id = body.get('auth_id')

    # generate fake user
    user = fake.create_user(email, auth_id)
    user_id = user['user_id']

    # to simulate db, place user in dictionary so it can be fetched by id at GET /users
    users[user_id] = user
    return user
