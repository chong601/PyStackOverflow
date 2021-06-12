from flask import Flask, jsonify, render_template
from flask.views import MethodView
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
from sqlalchemy import Column, JSON, Integer, ForeignKey
from flask_migrate import Migrate
import os

# Create a new Flask instance
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.getcwd() + '/database.db'
# Database
db = SQLAlchemy(app)
db.init_app(app)

migrate = Migrate(app, db)
migrate.init_app(app, db)


# Schema database model
# Preferably, this would be based on the schema file provided by StackOverflow,
# however SQLAlchemy prohibits the use of variable attribute count which slightly
# complicates the implementation a bit.
# This class exists purely to facilitate data transfer to and from database.
# Full schema operation will be built later.
@dataclass(order=True)
class Schema(db.Model, object):
    __tablename__ = 'stackoverflow_schema'
    year: int = Column(Integer, primary_key=True, autoincrement=False,
                       comment='The year of the row the data represented')
    columns: dict = Column(JSON, comment='The columns represented by the year', nullable=False)

    def __init__(self, year, columns):
        self.year = year
        self.columns = columns

    # Don't know if this is doable, but it would be a good debugging tool to start with ;)
    def __repr__(self):
        return f'{self.__class__.__name__}({vars(self)})'


# Respondent database model
@dataclass(order=True)
class Response(db.Model, object):
    __tablename__ = 'stackoverflow_response'
    # An id for referring to the data, or extract the respondent ID from the response,
    # which is you know, CRAP.
    response_id: int = Column(Integer, primary_key=True, comment='The anonymized ID of the response')
    # Set the year column to have a foreign key relationship with the
    # schema year column. Also enforce to populate the data if it doesn't exist
    year: int = Column(Integer, ForeignKey('stackoverflow_schema.year'), nullable=False)
    # Store responses as JSON because you know, it's goddamn impossible to store the responses using
    # RDBMS concepts. Just use JSON and refer to the schema to extract the data and call it a day, really
    responses: dict = Column(JSON, comment='The responses in JSON corresponding to the year of the data',
                             nullable=False)

    def __init__(self, response_id, year, responses):
        self.response_id = response_id
        self.year = year
        self.responses = responses

    # Don't know if this is doable, but it would be a good debugging tool to start with ;)
    def __repr__(self):
        return f'{self.__class__.__name__}({vars(self)})'


# Class to provide REST interface for consumption
class RespondentAnswers(MethodView):

    def get(self, response_id=None):
        if response_id is None:
            return jsonify(Response.query.all())
        elif response_id is int:
            return jsonify(Response.query.filter_by(response_id=response_id).first_or_404())
        return jsonify({'error': 'Invalid request'}), 400


# Requires passing in JSON data
app.add_url_rule('/response', methods=['GET'], view_func=RespondentAnswers.as_view('users'))
# Only require the ID for the operation
app.add_url_rule('/response/<int:response_id>', methods=['GET'],
                 view_func=RespondentAnswers.as_view('users_id'))

if __name__ == '__main__':
    app.run(use_reloader=False)
