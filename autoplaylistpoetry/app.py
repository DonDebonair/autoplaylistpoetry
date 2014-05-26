import logging.config

from flask import Flask, g

from autoplaylistpoetry.web import web
from autoplaylistpoetry.api import api


DEFAULT_BLUEPRINTS = (
    web,
    api
)


def create_app(blueprints=None):
    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS

    app = Flask(__name__)
    config_app(app)
    config_blueprints(app, blueprints)
    return app


def config_app(app):
    app.config.from_object('autoplaylistpoetry.config')
    app.config.from_envvar('APP_CONFIG', silent=True)
    logging.config.dictConfig(app.config['LOGGING'])


def config_blueprints(app, blueprints):
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
