import dataclasses

from flask import Flask, jsonify, render_template
from flask.views import MethodView
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
from sqlalchemy import Column, JSON, Integer, ForeignKey, Text
from flask_migrate import Migrate
import collections
import os
import uuid

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
    """
    Schema database object that represents the 'stackoverflow_schema table in database
    """
    __tablename__ = 'stackoverflow_schema'
    year: int = Column(Integer, primary_key=True, autoincrement=False,
                       comment='The year of the row the data represented')
    columns: dict = Column(JSON, comment='The columns represented by the year', nullable=False)

    @staticmethod
    def map():
        """
        Mapper function that provides a list of mappable attributes

        :return: Dictionary of mappable attributes
        """
        keys = {'insight_year', 'response_columns'}

    # Don't know if this is doable, but it would be a good debugging tool to start with ;)
    def __repr__(self):
        return f'{self.__class__.__name__}({vars(self)})'


class OrderedClassMembers(type):
    @classmethod
    def __prepare__(self, name, bases):
        return collections.OrderedDict()

    def __new__(self, name, bases, classdict):
        classdict['__ordered__'] = [key for key in classdict.keys()
                if key not in ('__module__', '__qualname__')]
        return type.__new__(self, name, bases, classdict)


# Respondent database model
@dataclass(order=True)
class Response(db.Model, object):
    """
    Response class object that represents the `stackoverflow_response` table in database
    """
    __tablename__ = 'stackoverflow_response'
    # Use UUID to represent the common set of response data on response
    # This is a workaround to support SQLite as the original intention is to have composite
    # key that includes response_id and year to make the data unique.
    # Most database systems out there would generally support composite keys as a primary key
    # but that's not a choice as it would require a different approach to make it compatible across
    # all database software out there which is beyond of my skillset as of now.
    # UUID will be stored as a string again to work around SQLite lack of native UUID data type support
    # so string version of UUID is selected to maintain compatibility across database software.
    row_id: str = Column(Text, primary_key=True, comment='Common ID of the response')
    # An id for referring to the data, or extract the respondent ID from the response,
    # which is you know, CRAP.
    response_id: int = Column(Integer, comment='The anonymized ID of the response')
    # Set the year column to have a foreign key relationship with the
    # schema year column.
    year: int = Column(Integer, ForeignKey('stackoverflow_schema.year'), nullable=False)
    # Store responses as JSON because you know, it's goddamn impossible to store the responses using
    # RDBMS concepts. Just use JSON and refer to the schema to extract the data and call it a day, really
    responses: dict = Column(JSON, comment='The responses in JSON corresponding to the year of the data',
                             nullable=False)

    def __init__(self, response_id, year, responses):
        self.row_id = str(uuid.uuid4())
        self.response_id = response_id
        self.year = year
        self.responses = responses

    @staticmethod
    def map():
        """
        Mapper function that provides a list of mappable attributes

        :return: Dictionary of mappable attributes
        """
        keys = {'id', 'response_id', 'response_year', 'responses'}

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
