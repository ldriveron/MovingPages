from flask import request, jsonify
from app_files import app, API_functions, data_functions


@app.route('/api/book', methods=['GET'])  # this method is called when form is submitted
def api_book_title():
    # get the title of the book to search for from the url
    search_term = request.args.get('title')

    # Goodreads API functions
    gr_result = API_functions.request_book(search_term)  # use function in API_functions.py

    # if no book is found, return a json file stating so
    if gr_result["total"] == 0:
        return jsonify({"total_results": 0, "message": "No book found."})

    # TheMovieDB functions
    movie_result = {}  # empty dictionary
    tv_result = {}  # empty dictionary
    if gr_result["total"] != 0:  # only continue if there is a book found
        # search for movie
        # use function in API_functions.py
        movie_result = API_functions.request_movie(gr_result["name_split"], gr_result["author_name_clean"], 0)

        if movie_result["total_results"] == 0:  # if no movie is found, return no result for movie
            movie_result = {"total_results": 0}

        # search for TV show
        # use function in API_functions.py
        tv_result = API_functions.request_tv_show(gr_result["name_split"], gr_result["author_name_clean"], 0)

        if tv_result["total_results"] == 0:  # if no tv show is found, return no result for tv show
            tv_result = {"total_results": 0}

    final_data = {"book": gr_result, "movie": movie_result, "tv_show": tv_result}

    return jsonify(final_data)


@app.route('/api/random', methods=['GET'])  # this method is called when form is submitted
def api_random_book():
    # get a random book to search for
    search_term = data_functions.get_random_book()

    # Goodreads API functions
    gr_result = API_functions.request_book(search_term)  # use function in API_functions.py

    # if no book is found, return a json file stating so
    if gr_result["total"] == 0:
        return jsonify({"total_results": 0, "message": "No book found."})

    # TheMovieDB functions
    movie_result = {}  # empty dictionary
    tv_result = {}  # empty dictionary
    if gr_result["total"] != 0:  # only continue if there is a book found
        # search for movie
        # use function in API_functions.py
        movie_result = API_functions.request_movie(gr_result["name_split"], gr_result["author_name_clean"], 0)

        if movie_result["total_results"] == 0:  # if no movie is found, return no result for movie
            movie_result = {"total_results": 0}

        # search for TV show
        # use function in API_functions.py
        tv_result = API_functions.request_tv_show(gr_result["name_split"], gr_result["author_name_clean"], 0)

        if tv_result["total_results"] == 0:  # if no tv show is found, return no result for tv show
            tv_result = {"total_results": 0}

    final_data = {"book": gr_result, "movie": movie_result, "tv_show": tv_result}

    return jsonify(final_data)

