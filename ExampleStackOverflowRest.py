import dataclasses

from flask import Flask, jsonify, request
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
# Disable JSON key ordering.
# Fuck this took fucking forever to figure out.
# This setting is completely cosmetic, but used because most API put keys on top
app.config['JSON_SORT_KEYS'] = False

# Database
db = SQLAlchemy(app)
db.init_app(app)

migrate = Migrate(app, db)
migrate.init_app(app, db)

MAX_RESULTS_PER_PAGE = 100


# Schema database model
# Preferably, this would be based on the schema file provided by StackOverflow,
# however SQLAlchemy prohibits the use of variable attribute count which slightly
# complicates the implementation a bit.
# This class exists purely to facilitate data transfer to and from database.
# Full schema operation will be built later.
@dataclass
class Schema(db.Model, object):
    """
    Schema database object that represents the 'stackoverflow_schema table in database
    """
    __tablename__ = 'stackoverflow_schema'
    year: int = Column(Integer, primary_key=True, autoincrement=False,
                       comment='The year of the row the data represented')
    response_columns: dict = Column(JSON, comment='The columns represented by the year', nullable=False)

    def __init__(self, year, response_columns):
        self.year = year
        self.response_columns = response_columns

    @staticmethod
    def map():
        """
        Mapper function that provides a list of mappable attributes

        :return: Dictionary of mappable attributes
        """
        keys = {'year', 'response_columns'}
        return keys

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
@dataclass
class Response(db.Model):
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
    response_id: str = Column(Text, primary_key=True, comment='Common ID of the response')
    # An id for referring to the data, or extract the respondent ID from the response,
    # which is you know, CRAP.
    respondent_id: int = Column(Integer, comment='The anonymized ID of the response')
    # Set the year column to have a foreign key relationship with the
    # schema year column.
    response_year: int = Column(Integer, ForeignKey('stackoverflow_schema.year'), nullable=False)
    # Store responses as JSON because you know, it's goddamn impossible to store the responses using
    # RDBMS concepts. Just use JSON and refer to the schema to extract the data and call it a day, really
    responses: dict = Column(JSON, comment='The responses in JSON corresponding to the year of the data',
                             nullable=False)

    def __init__(self, respondent_id, response_year, responses, response_id=None):
        if response_id is None:
            self.response_id = str(uuid.uuid4())
        else:
            self.response_id = response_id
        self.respondent_id = respondent_id
        self.response_year = response_year
        self.responses = responses

    @staticmethod
    def map():
        """
        Mapper function that provides a list of mappable attributes

        :return: Dictionary of mappable attributes
        """
        keys = {'response_id', 'respondent_id', 'response_year', 'responses'}
        return keys

    def __repr__(self):
        return f'{self.__class__.__name__}({vars(self)})'


# TODO: get rid of MethodView (not suitable for this use case as we only do GET requests
@app.route('/responses')
def get_response_per_page():
    page_number = request.args.get('page', 1, type=int)
    size_per_page = request.args.get('size', MAX_RESULTS_PER_PAGE, type=int)
    result = Response.query.paginate(page=page_number, per_page=size_per_page, error_out=False).items
    return (jsonify({'error': 'Database is empty'}), 404) if len(result) == 0 else jsonify(result)


@app.route('/responses/<int:year>')
def get_response_by_year_per_page(year):
    page_number = request.args.get('page', 1, type=int)
    size_per_page = request.args.get('size', MAX_RESULTS_PER_PAGE, type=int)
    result = Response.query.filter_by(response_year=year).paginate(page=page_number, per_page=size_per_page, error_out=False).items
    return (jsonify({'error': 'Database is empty'}), 404) if len(result) == 0 else jsonify(result)


@app.route('/response/<response_id>')
def get_response_by_response_id(response_id):
    # response_id = request.args.get('response_id', type=str)
    result = Response.query.filter_by(response_id=response_id).all()
    if len(result) > 1:
        result.append({'Warning': 'More than one response detected!'})
    return (jsonify({'error': f'Response ID {response_id} not found.'}), 404) \
        if len(result) != 1 else jsonify(result)


@app.route('/response/<int:year>/<int:respondent_id>')
def get_response_by_year_respondent_id(year, respondent_id):
    # year = request.args.get('year', type=int)
    # respondent_id = request.args.get('respondent_id', type=int)
    result = Response.query.filter_by(response_year=year, respondent_id=respondent_id).all()
    return (jsonify({'error': f'Response data for respondent ID {respondent_id} for year {year} is not found.'}), 404) \
        if len(result) != 1 else jsonify(result)



# Class to provide REST interface for consumption
# class RespondentAnswers(MethodView):
#
#     # TODO: separate get request to respective routes
#     # TODO: pagination
#     # TODO: ratelimit
#     def get(self, response_year=None, response_id=None, page=1):
#         if response_year is None and response_id is None:
#             return jsonify(Response.query.paginate(page=page, per_page=MAX_RESULTS_PER_PAGE, error_out=False).items)
#         elif response_year is not None and response_id is None:
#             return jsonify(Response.query.filter_by(response_year=response_year).paginate(page=page, per_page=MAX_RESULTS_PER_PAGE, error_out=False).items)
#         elif response_year is not None and response_id is not None:
#             return jsonify(
#                 Response.query.filter_by(response_year=response_year, response_id=response_id).first_or_404())
#         return jsonify({'error': 'Invalid request'}), 400
#
#
# # Requires passing in JSON data
# app.add_url_rule('/responses/<int:page>', methods=['GET'], view_func=RespondentAnswers.as_view('users'))
# # Only require the ID for the operation
# app.add_url_rule('/responses/<int:response_year>/<int:page>', methods=['GET'],
#                  view_func=RespondentAnswers.as_view('users_year'))
# app.add_url_rule('/response/<int:response_year>/<int:response_id>', methods=['GET'],
#                  view_func=RespondentAnswers.as_view('users_year_id'))

if __name__ == '__main__':
    app.run(use_reloader=False)
