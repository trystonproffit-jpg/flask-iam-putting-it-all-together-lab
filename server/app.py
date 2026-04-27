#!/usr/bin/env python3

from flask import request, session, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema

user_schema = UserSchema()
recipe_schema = RecipeSchema()
recipes_schema = RecipeSchema(many=True)


class Signup(Resource):
    def post(self):
        data = request.get_json()

        try:
            user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            user.password_hash = data.get('password')

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id

            return make_response(user_schema.dump(user), 201)

        except (IntegrityError, ValueError) as e:
            db.session.rollback()
            return make_response({'errors': [str(e)]}, 422)


class CheckSession(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get('user_id')).first()

        if user:
            return make_response(user_schema.dump(user), 200)

        return make_response({'error': 'Unauthorized'}, 401)


class Login(Resource):
    def post(self):
        data = request.get_json()

        user = User.query.filter(User.username == data.get('username')).first()

        if user and user.authenticate(data.get('password')):
            session['user_id'] = user.id
            return make_response(user_schema.dump(user), 200)

        return make_response({'error': 'Unauthorized'}, 401)


class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id')
            return make_response('', 204)

        return make_response({'error': 'Unauthorized'}, 401)


class RecipeIndex(Resource):
    def get(self):
        if not session.get('user_id'):
            return make_response({'error': 'Unauthorized'}, 401)

        recipes = Recipe.query.all()
        return make_response(recipes_schema.dump(recipes), 200)

    def post(self):
        if not session.get('user_id'):
            return make_response({'error': 'Unauthorized'}, 401)

        data = request.get_json()

        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=session.get('user_id')
            )

            db.session.add(recipe)
            db.session.commit()

            return make_response(recipe_schema.dump(recipe), 201)

        except (IntegrityError, ValueError) as e:
            db.session.rollback()
            return make_response({'errors': [str(e)]}, 422)


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)