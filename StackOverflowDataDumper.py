from ExampleStackOverflowRest import db, Response, Schema
import csv
import logging
import time

# List of todo:
# - [in progress] Functionalize code that can be placed in a function
# - Rewrite commit logic to handle SSD
# - Break out code that can be shared across dumper and REST to a common Python file
# - [in progress] Appropriately document internal code in Python file
# - Put available public API on README.md (or appropriate file)
# - Enable argument support for dumper
# - [in progress] Cut down indentations (preferably below 3 levels of indentation)
# - Allow customization of logging verbosity
# - Make code sorta testable

# Directory path (relative to script location for the time being)
DIR = 'stackoverflow_data'

# Loggy bits
log = logging.getLogger('__name__')
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

# Start timer before launching
all_op_start_time = time.time_ns()
total_data = 0
dump_rate = 1000
log.info(f'Begin processing schema data located at "{DIR}".')
elapsed_time = 0


def measure_time(func):
    """
    Measure the time taken to run.

    :param func: A function that will be timed
    :return: The wrapped function with timer
    """

    def wrapper(*args, **kwargs):
        start_time = time.time_ns()
        func(*args, **kwargs)
        end_time = time.time_ns()
        internal_elapsed_time = end_time - start_time
        return start_time, end_time, internal_elapsed_time
    return wrapper


@measure_time
def commit_data():
    """
    Issues a commit to the current DB session.
    """
    log.debug('Committing changes to the database...')
    db.session.commit()
    log.debug('Commit success.')


# Assume the directory is labelled by year
# TODO: write in README about expected format
for i in range(2017, 2021):
    log.info(f'Start processing StackOverflow schema data for year {str(i)}.')
    with open('/'.join([DIR, str(i), 'survey_results_schema.csv']), newline='',
              encoding='utf8') as file:
        log.info(f'File "{file.name}" successfully opened.')
        data = csv.DictReader(file)
        row = {}
        log.info(f'Extracting schema data from "{file.name}"...')
        for d in data:
            log.debug(f'Discovered data {d}.')
            k, v = d.keys()
            row.update({d[k]: d[v]})
            log.debug(f'Extracted data with key {k} and value {v}')
        log.debug(f'Schema data extraction for year {str(i)} completed.')
        log.debug(f'Saving extracted schema data for year {str(i)} to database...')
        log.debug(f'Begin creating schema object with data {row}')
        schema = Schema(i, row)
        log.debug(f'Adding schema object {schema}...')
        db.session.add(schema)
        log.debug('Schema object created successfully.')
    commit_data()
    log.info(f'Schema data for year {str(i)} extracted.')
log.info('Finished processing all schema data')

log.info(f'Start processing response data from {DIR}.')
for i in range(2017, 2021):
    count = 0
    next_check = dump_rate
    log.info(f'Start processing StackOverflow response data for year {str(i)}.')

    with open('/'.join([DIR, str(i), 'survey_results_public.csv']), newline='',
              encoding='utf8') as file:
        log.info(f'Response data "{file.name}" opened successfully.')
        data = csv.DictReader(file)
        log.info(f'Extracting response data from "{file.name}". This may take a long time.')

        for d in data:
            row = {}
            log.debug(f'Discovered data {d}')
            log.debug(f'Extracted data with key {k} and value {v}')

            log.debug(f'Begin creating response object with data {row}')
            response = Response(d['Respondent'], i, d)
            log.debug(f'Response object created with data {response}.')
            log.debug(f'Begin saving response data {response} into database...')
            db.session.add(response)
            log.debug('Response data saved.')

            if count == next_check:
                _, _, elapsed_time = commit_data()
                log.info(
                    f'Dump rate is {dump_rate}. Inserted {count} rows of data. It took '
                    f'{round(elapsed_time / 1000000000, 3)}s to commit.')
                if dump_rate < 500:
                    dump_rate = 1000
                    log.info(f'Dump rate limited to {dump_rate} rows.')
                elif elapsed_time > 10 * (10 ** 9):

                    dump_rate -= 1000 if dump_rate != 0 else 1000
                    log.info(f'Commit time took longer than 10 seconds. Decreasing dump rate to {dump_rate} rows...')
                elif elapsed_time < 10 * (10 ** 9):
                    dump_rate += 500
                    log.info(f'Commit time is faster than 10 seconds. Increasing dump rate to {dump_rate} rows...')
                next_check = count + dump_rate
            count += 1
        log.info(f'Loaded {count} responses for year {str(i)}')
        log.info(f'Data successfully extracted. Committing one final time...')
        _, _, elapsed_time = commit_data()
        log.info(
            f'Dump rate is {dump_rate}. Inserted {count} rows of data. It took '
            f'{round(elapsed_time / 1000000000, 3)}s to commit.')
        log.info(f'Response data for year {str(i)} completed.')
        total_data += count
all_op_end_time = time.time_ns()
log.info(f'Finished processing all response data. Loaded {total_data} rows in '
         f'{round((all_op_end_time - all_op_start_time) / 1000000000, 3)}s.')
