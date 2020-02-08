import math
import requests
from xml.etree import ElementTree
from app_files import json_functions, data_functions
from lxml import etree

# open json file holding Goodreads API keys, TheMovieDB API key
keys = json_functions.read_data("p_k.json")

# Goodreads API functions
gr_secret = keys["gr_secret"]
gr_key = keys["gr"]  # get Goodreads key


def request_book(search_term):  # search for book via GoodReads API
    """This function uses the search term entered by the user to find a book with the use of Goodreads API.

    Args:
        search_term (str): This argument is used when searching for a book with the use of Goodreads API.

    Raises:
        IndexError: Index not found in the XML received from Goodreads.

    Returns:
        book_result: A dictionary with book data picked from the XML result received from Goodreads.
    """

    gr_url = "https://www.goodreads.com/search/index.xml?key={0}&q={1}".format(gr_key,
                                                                               search_term)  # api call to Goodreads

    gr_xml = requests.get(gr_url)  # get book information xml result
    gr_result = ElementTree.fromstring(gr_xml.content)
    book_result = {}  # empty dictionary
    try:
        current_top = 0
        if gr_result[1][3].text != "0":
            # find most popular book in the results
            for result in gr_result[1][6].findall('work'):
                if int(result[2].text) > current_top:
                    current_top = int(result[2].text)
            # put most popular result as the book result
            for result in gr_result[1][6].findall('work'):
                if int(result[2].text) == current_top:
                    book_result["total"] = 1
                    # useful for other Goodreads API requests
                    book_result["id"] = result.find('best_book').find('id').text
                    book_result["name"] = result.find('best_book').find('title').text
                    book_result["author"] = result.find('best_book').find('author').find('name').text
                    book_result["year"] = result.find('original_publication_year').text
                    book_result["rating"] = result.find('average_rating').text
                    # get rid of spaces in author name
                    book_result["author_name_clean"] = book_result["author"].replace(" ", "")
                    # if book title includes series name and number, remove it
                    book_result["name_split"] = book_result["name"].split('(', 1)[0]
                    book_result["img"] = result.find('best_book').find('image_url').text
                    book_result["goodreads_url"] = "https://www.goodreads.com/book/show/{0}".format(book_result["id"])

                    gr_isbn_url = "https://www.goodreads.com/book/show/{0}.xml?key={1}".format(book_result["id"],
                                                                                               gr_key)
                    gr_xml = requests.get(gr_isbn_url)  # using this to get the book's ISBN10 and ISBN13
                    gr_result = ElementTree.fromstring(gr_xml.content)
                    book_result["isbn_10"] = gr_result[1][2].text
                    book_result["isbn_13"] = gr_result[1][3].text
                    book_result["pages"] = gr_result[1][19].text
                    book_result["author_img"] = gr_result[1][26][0][3].text
                    book_result["author_url"] = gr_result[1][26][0][5].text
                    break
        else:
            book_result["total"] = 0
    except IndexError as e:
        book_result["total"] = 0

    return book_result


# get the user's read books from Goodreads after authenticating
def get_users_books(user_id, client):  # much faster now. average ~58 seconds for 109 books
    """This function uses session created between the MovingPages application and the Goodreads user to retrieve
    all their Read books and search for adaptations for each.

    Args:
        user_id (int): This argument is used to get the users Read books by using the Goodreads API.
        client (object): This argument is the generated session between MovingPages and the Goodreads user.

    Raises:
        AttributeError: Attribute not found in the JSON data received from Goodreads.

    Returns:
        books: A dictionary containing all the books found with matching adaptations.
    """

    books = []  # list for books
    url = 'http://www.goodreads.com'
    response, content = client.request('{0}/review/list/{1}.xml?key={2}&v=2'  # get the user's read shelf
                                       '&shelf=read&per_page=1000&page=1'.format(url, user_id, gr_key), 'GET')
    if response['status'] != '200':
        raise Exception('Cannot fetch resource: %s' % response['status'])

    result = etree.fromstring(content)  # put results into an ElementTree
    total_books_read = result[2].attrib['total']
    pages_needed = math.ceil(int(total_books_read) / 10)
    books.append({"total_books": total_books_read, "pages_needed": pages_needed})
    if int(total_books_read) > 0:  # only add books to list if there are books
        for book in result[2].findall('review'):  # loop through each book
            movie_match = False
            tv_match = False  # reset the match
            try:
                compare_book = {"total": 1, "id": book.find('book').find('id').text,
                                "name": book.find('book').find('title').text,
                                "author": book.find('book').find('authors').find('author').find('name').text,
                                "year": book.find('book').find('publication_year').text,
                                "rating": book.find('book').find('average_rating').text,
                                "name_split": book.find('book').find('title_without_series').text,
                                "img": book.find('book').find('image_url').text,
                                "goodreads_url": book.find('book').find('link').text,
                                "isbn_10": book.find('book').find('isbn').text,
                                "isbn_13": book.find('book').find('isbn13').text,
                                "pages": book.find('book').find('num_pages').text,
                                "author_img": book.find('book').find('authors').find('author').find('image_url').text,
                                "author_url": book.find('book').find('authors').find('author').find('link').text}
                compare_book["author_name_clean"] = compare_book["author"].replace(" ", "")
            except (AttributeError, TypeError) as e:
                # if the xml above has issues getting the data, revert back to normal request_book method
                compare_book = request_book(book.find('book').find('title_without_series').text)
            # print(compare_book["name_split"])
            movie = request_movie(compare_book["name_split"], compare_book["author_name_clean"], 1)
            if movie["total_results"] != 0:  # check for a movie result
                movie_match = True
            tv_show = request_tv_show(compare_book["name_split"], compare_book["author_name_clean"], 1)
            if tv_show["total_results"] != 0:  # check for a tv show result
                tv_match = True

            # add book to list of movie or tv show match is found
            if movie_match and tv_match:
                books.append({"movie_match": movie_match, "tv_match": tv_match, "book": compare_book,
                              "movie": movie, "tv_show": tv_show})
            elif movie_match:
                books.append({"movie_match": movie_match, "tv_match": tv_match, "book": compare_book,
                              "movie": movie})
            elif tv_match:
                books.append({"movie_match": movie_match, "tv_match": tv_match, "book": compare_book,
                              "tv_show": tv_show})

    return books


# TheMovieDB API Functions
mdb_key = keys["the_movie_db"]  # get mdb key
proxies = {
    "http": None,
    "https": None,
}


def request_movie(book_name, author_name_clean, source):  # search for movie via TheMovieDB API
    """This function is used to find a movie from TheMovieDB based on a book name.

    Args:
        book_name (str): This argument is used to search TheMovieDB for a matching adaptation.
        author_name_clean (str): This argument is used to make sure the book author has a credit in the movie.
        source (int): This argument is used to know where the search comes from and change result based on source.

    Raises:
        KeyError: Attribute not found in the JSON data received from TheMovieDB.

    Returns:
        movie_result: A dictionary containing the movie result.
    """

    moviedb_movie_url = "https://api.themoviedb.org/3/search/movie?api_key={0}&language=en-US" \
                        "&query={1}&page=1&include_adult=false".format(mdb_key,
                                                                       book_name)  # this is the url for movie search

    movie_result = requests.get(moviedb_movie_url).json()  # get the movie data from themoviedb
    try:
        if movie_result["total_results"] != 0:
            top_result = movie_result["results"][0]
            movie_credits = request_movie_credits(top_result["id"])
            if not data_functions.validate_writer(movie_credits, author_name_clean):
                movie_result["total_results"] = 0
                return movie_result  # stop here if book writer is not credited in the movie
            try:
                movie_result = {"id": top_result["id"], "original_title": top_result["original_title"],
                                "poster_path": top_result["poster_path"],
                                "original_language": top_result["original_language"],
                                "vote_average": top_result["vote_average"], "release_date": top_result["release_date"],
                                "overview": top_result["overview"],
                                "movie_youtube_id": request_movie_trailer(top_result["id"]),
                                "credits": movie_credits, "total_results": 1}
                # only including movie details if it is for a singular search
                if source == 0:
                    movie_result["movie_details"] = request_movie_details(top_result["id"])
            except KeyError as e:  # if there is a KeyError, just skip the result
                movie_result["total_results"] = 0
        else:
            movie_result["total_results"] = 0
    except KeyError as e:
        movie_result["total_results"] = 0
    return movie_result


def request_movie_details(movie_id):  # get details of the movie
    """This function is used to find movie details from TheMovieDB based on a movie id.

    The details gathered are: production companies, genre, and IMDB ID.

    Args:
        movie_id (int): This argument is used to search TheMovieDB movie details.

    Raises:
        KeyError: Attribute not found in the JSON data received from TheMovieDB.

    Returns:
        detail_result_final: A dictionary containing the movie details result.
    """

    movie_detail_url = "https://api.themoviedb.org/3/movie/{0}?api_key={1}".format(movie_id,
                                                                                   mdb_key)  # details movie search url

    detail_result = requests.get(movie_detail_url).json()  # get the movie details from themoviedb
    try:
        detail_result_final = {"total": 1, "production_companies": [], "genre": detail_result["genres"][0]["name"]}
        try:
            detail_result_final["imdb_id"] = detail_result["imdb_id"]
        except KeyError as e:
            detail_result_final["imdb_id"] = None
        for company in detail_result["production_companies"]:
            if company["logo_path"] != None and company["name"] != None:
                detail_result_final["production_companies"].append({"name": company["name"],
                                                                    "logo_path": company["logo_path"]})
    except (KeyError, TypeError, IndexError) as e:
        detail_result_final = {"total": 0}

    return detail_result_final


def request_movie_trailer(movie_id):  # search for movie trailer Youtube ID via TheMovieDB API
    """This function is used to find a movie trailer from TheMovieDB based on a movie id.

    Args:
        movie_id (str): This argument is used to search TheMovieDB for a matching trailer.

    Raises:
        KeyError: Attribute not found in the JSON data received from TheMovieDB.

    Returns:
        movie_youtube_id: A string containing the trailers YouTube ID.
    """

    moviedb_movie_trailer_url = "http://api.themoviedb.org/3/movie/{0}/videos?api_key={1}".format(movie_id, mdb_key)

    try:
        movie_trailer_result = requests.get(moviedb_movie_trailer_url).json()  # get trailer data from themoviedb
        if not movie_trailer_result["results"]:  # if a trailer is found, get the youtube id
            movie_youtube_id = None
        else:
            movie_youtube_id = movie_trailer_result["results"][0]["key"]
    except ValueError:
        movie_youtube_id = None

    return movie_youtube_id


def request_movie_credits(movie_id):  # search for TV show credits via TheMovieDB API
    """This function is used to find movie credits from TheMovieDB based on a movie id.

    Args:
        movie_id (str): This argument is used to search TheMovieDB for movie credits.

    Raises:
        KeyError: Attribute not found in the JSON data received from TheMovieDB.

    Returns:
        final_credits: An array containing writing credits and the top 3 acting credits for the movie.
    """

    moviedb_movie_credits = "https://api.themoviedb.org/3/movie/{0}/credits?api_key={1}&language=en-US".format(movie_id,
                                                                                                               mdb_key)

    movie_credits_results = requests.get(moviedb_movie_credits).json()
    final_credits = [[], []]
    try:
        if len(movie_credits_results["cast"]) > 3:  # if a movie is found but has less than 3 actors listed, then skip
            # add crew with writing credit in the movie
            for credit in movie_credits_results["crew"]:
                if credit["department"] == "Writing":
                    final_credits[1].append(credit)

            # add the top three actors in the movie
            for actor in range(3):
                final_credits[0].append({"name": movie_credits_results["cast"][actor]["name"],
                                         "character": movie_credits_results["cast"][actor]["character"],
                                         "profile_path": "https://image.tmdb.org/t/p/w500{0}"
                                        .format(movie_credits_results["cast"][actor]["profile_path"]),
                                         "id": movie_credits_results["cast"][actor]["id"]})
                # if the actors image does not exist, then replace it with a default
                if not data_functions.url_exists(final_credits[0][actor]["profile_path"]):
                    final_credits[0][actor]["profile_path"] = "../static/actor_no_img.png"
    except KeyError as e:  # if there is a KeyError, just skip the result
        pass

    return final_credits


def request_tv_show(book_name, author_name_clean, source):  # search for TV show via TheMovieDB API
    """This function is used to find a tv show from TheMovieDB based on a book name.

    Args:
        book_name (str): This argument is used to search TheMovieDB for a matching adaptation.
        author_name_clean (str): This argument is used to make sure the book author has a credit in the tv show.
        source (int): This argument is used to know where the search comes from and change result based on source.

    Raises:
        KeyError: Attribute not found in the JSON data received from TheMovieDB.

    Returns:
        tv_result: A dictionary containing the tv show result.
    """

    moviedb_tv_url = "https://api.themoviedb.org/3/search/tv?api_key={0}&query={1}" \
                     "&language=en-US&page=1".format(mdb_key, book_name)  # this is the url for tv show search

    tv_result = requests.get(moviedb_tv_url).json()  # get the tv data from themoviedb
    try:
        if tv_result["total_results"] != 0:
            top_result = tv_result["results"][0]
            tv_credits = request_tv_credits(top_result["id"])
            if not data_functions.validate_writer(tv_credits, author_name_clean):
                tv_result["total_results"] = 0
                return tv_result  # stop here if book writer is not credited in the tv show
            try:
                tv_result = {"id": top_result["id"], "original_name": top_result["original_name"],
                             "poster_path": top_result["poster_path"],
                             "original_language": top_result["original_language"],
                             "vote_average": top_result["vote_average"], "first_air_date": top_result["first_air_date"],
                             "overview": top_result["overview"],
                             "tv_youtube_id": request_tv_trailer(top_result["id"]),
                             "credits": tv_credits, "total_results": 1}
                # only including tv show details if it is for a singular search
                if source == 0:
                    tv_result["tv_details"] = request_tv_details(top_result["id"])
            except KeyError as e:  # if there is a KeyError, just skip the result
                tv_result["total_results"] = 0
        else:
            tv_result["total_results"] = 0
    except KeyError as e:
        tv_result["total_results"] = 0

    return tv_result


def request_tv_details(tv_id):
    """This function is used to find tv show details from TheMovieDB based on a tv show id.

    The details gathered are: production companies, genre, and IMDB ID.

    Args:
        tv_id (int): This argument is used to search TheMovieDB tv show details.

    Raises:
        KeyError: Attribute not found in the JSON data received from TheMovieDB.

    Returns:
        detail_result: A dictionary containing the tv show details result.
    """

    # details tv show search url
    tv_detail_url = "https://api.themoviedb.org/3/tv/{0}?api_key={1}".format(tv_id, mdb_key)

    detail_result = requests.get(tv_detail_url).json()  # get the tv show details from themoviedb
    try:
        detail_result_final = {"total": 1, "production_companies": [], "genre": detail_result["genres"][0]["name"]}
        for company in detail_result["production_companies"]:
            if company["logo_path"] != None and company["name"] != None:
                detail_result_final["production_companies"].append({"name": company["name"],
                                                                    "logo_path": company["logo_path"]})
        try:
            detail_result_final["imdb_id"] = detail_result["imdb_id"]
        except KeyError as e:
            detail_result_final["imdb_id"] = None
    except (KeyError, TypeError, IndexError) as e:
        detail_result_final = {"total": 0}

    return detail_result_final


def request_tv_trailer(tv_id):  # search for movie trailer Youtube ID via TheMovieDB API
    """This function is used to find a tv show trailer from TheMovieDB based on a tv show id.

    Args:
        tv_id (str): This argument is used to search TheMovieDB for a matching trailer.

    Raises:
        KeyError: Attribute not found in the JSON data received from TheMovieDB.

    Returns:
        tv_trailer_id: A string containing the trailers YouTube ID.
    """

    moviedb_tv_trailer_url = "http://api.themoviedb.org/3/tv/{0}/videos?api_key={1}".format(tv_id, mdb_key)

    try:
        tv_trailer_result = requests.get(moviedb_tv_trailer_url).json()  # get trailer data from themoviedb
        if not tv_trailer_result["results"]:  # if a trailer is found, get the youtube id
            tv_trailer_id = None
        else:
            tv_trailer_id = tv_trailer_result["results"][0]["key"]
    except ValueError:
        tv_trailer_id = None

    return tv_trailer_id


def request_tv_credits(tv_id):  # search for TV show credits via TheMovieDB API
    """This function is used to find tv show credits from TheMovieDB based on a tv show id.

    Args:
        tv_id (str): This argument is used to search TheMovieDB for tv show credits.

    Raises:
        KeyError: Attribute not found in the JSON data received from TheMovieDB.

    Returns:
        final_credits: An array containing writing credits and the top 3 acting credits for the tv show.
    """

    moviedb_tv_credits = "https://api.themoviedb.org/3/tv/{0}/credits?api_key={1}&language=en-US".format(tv_id,
                                                                                                         mdb_key)

    tv_credits_results = requests.get(moviedb_tv_credits).json()
    final_credits = [[], []]
    try:
        if len(tv_credits_results["cast"]) > 3:  # if a movie is found but has less than 3 actors listed, then skip
            # add crew with writing credit in the movie
            for credit in tv_credits_results["crew"]:
                if credit["department"] == "Writing":
                    final_credits[1].append(credit)

            # add the top three actors in the tv show
            for actor in range(3):
                final_credits[0].append({"name": tv_credits_results["cast"][actor]["name"],
                                         "character": tv_credits_results["cast"][actor]["character"],
                                         "profile_path": "https://image.tmdb.org/t/p/w500{0}"
                                        .format(tv_credits_results["cast"][actor]["profile_path"]),
                                         "id": tv_credits_results["cast"][actor]["id"]})
                # if the actors image does not exist, then replace it with a default
                if not data_functions.url_exists(final_credits[0][actor]["profile_path"]):
                    final_credits[0][actor]["profile_path"] = "../static/actor_no_img.png"
    except KeyError as e:  # if there is a KeyError, just skip the result
        pass

    return final_credits
