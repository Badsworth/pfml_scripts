#
# Tests for pfml.users.users_get()
#

import json
import flask
import pfml
import pfml.users
from pfml import generate_fake_data as fake

app = pfml.create_app()

def test_valid_get():
    user = fake.create_user('johnsmith@example.com', '0000-111-2222')
    user_id = user.get('user_id')

    # a little janky - can't figure out how to properly mock the users dictionary so
    # I'm actually adding the user created above directly to it
    users = pfml.users.users 
    users[user_id] = user

    client = app.app.test_client()
    response = client.get("/v1/users/{}".format(user_id))
    assert response.status_code == 200

def test_invalid_get():
    client = app.app.test_client()
    response = client.get("/v1/users/{}".format('12345'))
    assert response.status_code == 404
