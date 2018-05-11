# 
# accounts/controllers.py
# created by Nate Lee
# adapted from https://blog.miguelgrinberg.com/post/restful-authentication-with-flasky

import os
from flask import Blueprint, Flask, abort, request, jsonify, g, url_for
# from api import require_apikey
from flask_sqlalchemy import SQLAlchemy # SQL things
from flask_httpauth import HTTPBasicAuth 
from passlib.apps import custom_app_context as pwd_context # Hashing library
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)


accounts = Blueprint('account', __name__)
accounts.config['SECRET_KEY'] = 'culturemeshrocks lol good times also drew is kool'
accounts.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
accounts.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# extensions
db = SQLAlchemy(accounts)
auth = HTTPBasicAuth()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(accounts.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(accounts.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@accounts.route('/api/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@accounts.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@accounts.route('/api/token')
@auth.login_required
def get_auth_token(): # Login Required things
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@accounts.route('/api/resource')
@auth.login_required
def get_resource(): # Login Required things
    return jsonify({'data': 'Hello, %s!' % g.user.username})

