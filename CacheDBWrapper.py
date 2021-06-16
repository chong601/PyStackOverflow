from ExampleStackOverflowRest import Response, db_cache


def get_responses_by_page(req, page_number, size_per_page):
    if db_cache.check(req):
        return db_cache.get(req)
    result = Response.query.paginate(page=page_number, per_page=size_per_page, error_out=False).items
    db_cache.insert(req, result)
    return result


def get_responses_by_year_per_page(req, year, page_number, size_per_page):
    if db_cache.check(req):
        return db_cache.get(req)
    result = Response.query.filter_by(response_year=year).paginate(page=page_number, per_page=size_per_page,
                                                                   error_out=False).items
    db_cache.insert(req, result)
    return result


def get_response_by_response_id(req, response_id):
    if db_cache.check(req):
        return db_cache.get(req)
    result = Response.query.filter_by(response_id=response_id).all()
    db_cache.insert(req, result)
    return result


def get_response_by_year_respondent_id(req, year, respondent_id):
    if db_cache.check(req):
        return db_cache.get(req)
    result = Response.query.filter_by(response_year=year, respondent_id=respondent_id).all()
    db_cache.insert(req, result)
    return result


def get_stats():
    return db_cache.get_stats()
