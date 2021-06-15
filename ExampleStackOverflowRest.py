from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
from sqlalchemy import Column, JSON, Integer, ForeignKey, Text, Index
from flask_migrate import Migrate
import os
import uuid

# Results per page
MAX_RESULTS_PER_PAGE = 100

# Create a new Flask instance
app = Flask(__name__)
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://chong601:chong601@10.102.7.97/pystackoverflow'
# Disable JSON key ordering.
# Fuck this took fucking forever to figure out.
# This setting is completely cosmetic, but used because most API put keys on top
app.config['JSON_SORT_KEYS'] = False
# Inform Flask-SQLAlchemy to disable modification tracking
# We do not rely on events so it's probably safe to disable it.
# This shouldn't cause issues, but do raise a bug issue if weird things occur in production!
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
@dataclass
class Schema(db.Model, object):
    """
    Schema database object that represents the 'stackoverflow_schema table in database
    """
    __tablename__ = 'stackoverflow_schema'

    year: int = Column(Integer, primary_key=True, autoincrement=False,
                       comment='The year of the row the data represented')
    response_columns: dict = Column(JSON, comment='The columns represented by the year',
                                                       nullable=False)

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


db.Index('idx_response_identifier', Response.response_id, Response.respondent_id, Response.response_year)
db.Index('idx_response_year_respondent', Response.respondent_id, Response.response_year)


@app.route('/schemas')
def get_schema():
    result = Schema.query.all()
    return (jsonify({'error': 'No schema found.'}), 404) if len(result) == 0 else jsonify(result)


@app.route('/schema/<int:year>')
def get_schema_by_year(year):
    result = Schema.query.filter_by(year=year).all()
    if len(result) > 1:
        result.append({'warning': 'Multiple results exist. Your database may be inconsistent!'})
    return (jsonify({'error': f'Schema for year {year} not found.'}), 404) if len(result) == 0 else jsonify(result)


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
    result = Response.query.filter_by(response_year=year).paginate(page=page_number, per_page=size_per_page,
                                                                   error_out=False).items
    return (jsonify({'error': 'Database is empty'}), 404) if len(result) == 0 else jsonify(result)


@app.route('/response/<response_id>')
def get_response_by_response_id(response_id):
    # response_id = request.args.get('response_id', type=str)
    result = Response.query.filter_by(response_id=response_id).all()
    if len(result) > 1:
        result.append({'warning': 'More than one response detected. Your database may be inconsistent!'})
    return (jsonify({'error': f'Response ID {response_id} not found.'}), 404) \
        if len(result) != 1 else jsonify(result)


@app.route('/response/<int:year>/<int:respondent_id>')
def get_response_by_year_respondent_id(year, respondent_id):
    # year = request.args.get('year', type=int)
    # respondent_id = request.args.get('respondent_id', type=int)
    result = Response.query.filter_by(response_year=year, respondent_id=respondent_id).all()
    return (jsonify({'error': f'Response data for respondent ID {respondent_id} for year {year} is not found.'}), 404) \
        if len(result) != 1 else jsonify(result)


if __name__ == '__main__':
    app.run(use_reloader=False)
