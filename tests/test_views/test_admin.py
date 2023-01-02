"""
    Test the admin view
    Auth: Peter S. Zyambo
"""
import pytest
from lipila.db import get_db
from flask import g, session
from werkzeug.security import check_password_hash
from lipila.helpers import get_user, get_student

def test_dashboard(client, auth):
    response = auth.login()
    assert response.headers["Location"] == "/lipila/admin/dashboard"

    with client:
        res = client.get('/lipila/admin/dashboard')
        assert session['user_id'] == 1
        assert session['email'] == 'zyambo@icloud.com'
        assert b'ACADEMY' in res.data


def test_create_student(client, auth, app):
    """ test the add_student route and methods"""
    response = auth.login()
    assert response.headers['Location'] == '/lipila/admin/dashboard'
    with client:
        assert client.get('/lipila/admin/add').status_code == 200

    response = client.post(
        '/lipila/admin/add', data={
            'firstname':'ab', 'lastname':'b', 'school':1,
            'program':'b', 'tuition':300,
            }
    )
    assert response.headers['Location'] == '/lipila/admin/add'

    with app.app_context():
        conn = get_db()
        db = conn.cursor()
        db.execute(
            "SELECT * FROM student WHERE firstname = 'ab'",
        )
        assert db.fetchone() is not None


@pytest.mark.parametrize((
    'firstname', 'lastname', 'school', 'program', 'tuition', 'message'), (
    ('', '','','','', b'firstname is required'),
    ('p', '','','','', b'lastname is required'),
    ('p', 'z',1,'se','', b'tuition is required'),
))
def test_create_student_validate_input(
    client, auth, firstname, lastname, school, program, tuition, message):
    response = auth.login()
    assert response.headers['Location'] == '/lipila/admin/dashboard'
    with client:
        assert client.get('/lipila/admin/add').status_code == 200
    response = client.post(
        '/lipila/admin/add',
        data={
            'firstname':firstname, 'lastname':lastname, 'school':school,
            'program':program, 'tuition':tuition}
    )
    assert response.status_code == 200
    assert message in response.data


def test_show_students(client, auth):
    """ Test ths route to return registered students"""
    response = auth.login()
    assert response.headers['Location'] == '/lipila/admin/dashboard'
    with client:
        response = client.get('/lipila/admin/students')
        assert response.status_code == 200
        assert session['email'] == 'zyambo@icloud.com'
        assert b'pita' in response.data
        assert b'pita' in response.data
        assert b'sepi' in response.data
        assert b'sangwa' not in response.data
        assert b'zed' in response.data


def test_list_payments(client, auth):
    """ Test the route to return registered students"""
    response = auth.login()
    assert response.headers['Location'] == '/lipila/admin/dashboard'
    with client:
        response = client.get('/lipila/admin/payments')
        assert response.status_code == 200
        assert b'Payments' in response.data
        assert b'<h4>academy Payments</h4>' in response.data
        assert session['email'] == 'zyambo@icloud.com'
        assert session['user_id'] == 1
        assert b'2' in response.data # check code
        assert b'500' in response.data # check amount paid
        assert b'2023' in response.data # check date


def test_update_get(client, auth):
    """ Test the update view"""
    response = auth.login()
    assert response.headers['Location'] == '/lipila/admin/dashboard'
    with client:
        response = client.get('/lipila/admin/update/1')
        assert response.status_code == 200
        assert b"<h3>Update sepi zed's details</h3>" in response.data
        assert b'sepi' in response.data
        assert b'zed' in response.data
        assert b'IT' in response.data
        assert b'300' in response.data


def test_update_post(client, auth, app):
    """ test the add_student route and methods"""
    auth.login()

    response = client.post(
        '/lipila/admin/update/2', data={
            'firstname':'Sepiso', 'lastname':'Zyambo', 'school':1,
            'program':'Medicine', 'tuition':750,
            }
    )
    assert response.headers['Location'] == '/lipila/admin/students'

    with app.app_context():
        data = get_student(2)
        assert data is not None
        assert data[5] == 750
        assert data[1] == "Sepiso"
        assert data[4] == "Medicine"
    

def test_update_password_get(client, auth):
    """ Test the update view"""
    response = auth.login()
    assert response.headers['Location'] == '/lipila/admin/dashboard'
    with client:
        response = client.get('/lipila/admin/changepassword/1')
        assert response.status_code == 200
        assert b"Reset your password" in response.data


def test_reset_password(client):
    """ Test the update view"""
    with client:
        response = client.get('/lipila/admin/resetpassword')
        assert response.status_code == 200
        # assert response.headers['Location'] == '/'
        assert b"Enter your registered email to reset your password" in response.data


def test_update_password_post(client, auth, app):
    """ test the add_student route and methods"""
    auth.login()
    with app.app_context():
        user = get_user(1)
        assert check_password_hash(user[-1], 'test') == True

    response = client.post(
        '/lipila/admin/changepassword/1', data={
            'password':'newpassword'
            }
    )
    assert response.headers['Location'] == '/'
    # assert b'Password Changed Successfully' in response.data

    with app.app_context():
        user = get_user(1)
        assert check_password_hash(user[-1], 'newpassword') == True

def test_profile_get(client, auth):
    """ Test the update Profile view"""
    response = auth.login()
    assert response.headers['Location'] == '/lipila/admin/dashboard'
    with client:
        response = client.get('/lipila/admin/profile')
        assert response.status_code == 200
        assert b"Edit Profile Details" in response.data
        assert b"zyambo@icloud.com" in response.data
        assert b"academy" in response.data
        assert b"zyambo" in response.data
        assert b'<button class="btn btn-primary" type="submit">Save</button>' in response.data


@pytest.mark.parametrize((
    'job', 'school', 'email', 'mobile', 'reg_number',
    'firstname', 'lastname', 'message'), (
    ('Accountant', 'The School', 'school@email.com',
    '0971892260','369854200', 'Peter', 'zyambo', b'Profile Updated'),
))
def test_profile_post(
    client, auth, app, job,school,
    email, mobile, reg_number, firstname, lastname, message):
    """ test the add_student route and methods"""
    auth.login()
    with app.app_context():
        user = get_user(1)
        assert user[1] == "administrator"
        assert user[2] == "academy"
        assert user[3] == "zyambo@icloud.com"
        assert user[4] == "369854200"
        assert user[5] == "1245659"
        assert user[6] == "pita"
        assert user[7] == "zyambo"

    response = client.post(
        '/lipila/admin/profile', data={
            'job':job,
            'school':school,
            'email':email,
            'mobile':mobile,
            'reg_number':reg_number,
            'firstname':firstname,
            'lastname':lastname
            }
    )
    with app.app_context():
        user = get_user(1)
        assert user[4] == "0971892260"
    assert response.status_code == 200
    assert message in response.data
