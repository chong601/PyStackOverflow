from ExampleStackOverflowRest import db, Response, Schema
import csv
import logging
import time
# Loggy bits
log = logging.getLogger('__name__')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)
DIR = 'stackoverflow_data'

dump_rate = 10000
log.info('Begin processing schema data located at "{DIR}".')
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
        log.info(f'Schema data extraction for year {str(i)} completed.')
        log.info(f'Saving extracted schema data for year {str(i)} to database...')
        log.debug(f'Begin creating schema object with data {row}')
        schema = Schema(i, row)
        log.debug(f'Adding schema object {schema}...')
        db.session.add(schema)
        log.debug('Schema object created successfully.')
        log.debug(f'Committing data to database...')
        db.session.commit()
        log.debug(f'Commit data to database successful.')
        log.info(f'Schema data for year {str(i)} extracted.')
log.info('Finished processing all schema data')

log.info('Start processing response data from {DIR}.')
for i in range(2017,2021):
    log.info(f'Start processing StackOverflow response data for year {str(i)}.')
    with open('/'.join([DIR, str(i), 'survey_results_public.csv']), newline='',
              encoding='utf8') as file:
        log.info(f'Response data "{file.name}" opened successfully.')
        data = csv.DictReader(file)
        log.info(f'Extracting response data from "{file.name}". This make take a long time.')
        count = 1
        previous_time=0
        for d in data:
            row = {}
            log.debug(f'Discovered data {d}')
            log.debug(f'Extracted data with key {k} and value {v}')
            log.info(f'Saving extracted response data for year to database...')
            log.debug(f'Begin creating response object with data {row}')
            response = Response(d['Respondent'], i, d)
            log.debug(f'Response object created with data {response}.')
            log.debug(f'Begin saving response data {response} into database...')
            db.session.add(response)
            log.debug('Response data saved.')
            count += 1
            if count % dump_rate == 0:
                log.debug(f'Dump rate is {dump_rate}. Inserted {count} rows of data. It took {previous_time} ns to dump.')
                log.debug('Committing changes to the database...')
                start_time = time.time_ns()
                db.session.commit()
                end_time = time.time_ns()

                if end_time - start_time > 3*(10**9):
                    dump_rate -= 500
                    if dump_rate < 100:
                        dump_rate = 100
                elif end_time - start_time < 3*(10**9):
                    dump_rate += 200
                log.debug('Commit success.')

        log.debug('Committing changes to the database...')
        db.session.commit()
        log.debug('Commit success.')
        log.info(f'Response data for year {str(i)} completed.')

log.info('Finished processing all response data.')
