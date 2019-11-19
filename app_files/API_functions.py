import math
import requests
from xml.etree import ElementTree
from app_files import json_functions, data_functions
from lxml import etree

# Goodreads API functions
gr_key = json_functions.read_data("p_k.json")
gr_secret = gr_key["gr_secret"]
gr_key = gr_key["gr"]  # get Goodreads key


def request_book(search_term):  # search for book via GoodReads API
    gr_url = "https://www.goodreads.com/search/index.xml?key={0}&q={1}".format(gr_key,
                                                                               search_term)  # api call to Goodreads
    gr_xml = requests.get(gr_url)  # get book information xml result
    gr_result = ElementTree.fromstring(gr_xml.content)
    book_result = {}  # empty dictionary
    # XML order goes like this: [search][results][work][...]
    try:
        if gr_result[1][3].text != "0":
            book_result["total"] = 1
            book_result["id"] = gr_result[1][6][0][8][0].text  # useful for other Goodreads API requests
            book_result["name"] = gr_result[1][6][0][8][1].text
            book_result["author"] = gr_result[1][6][0][8][2][1].text
            book_result["year"] = gr_result[1][6][0][4].text
            book_result["rating"] = gr_result[1][6][0][7].text
            book_result["author_name_clean"] = book_result["author"].replace(" ",
                                                                             "")  # get rid of spaces in author name
            book_result["name_split"] = book_result["name"].split('(', 1)[0]  # if book title includes series name
            # and number, remove it
            book_result["img"] = gr_result[1][6][0][8][3].text
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
        else:
            book_result["total"] = 0
    except IndexError as e:
        book_result["total"] = 0

    return book_result


# get the user's read books from Goodreads after authenticating
def get_users_books(user_id, client):  # much faster now. average ~58 seconds for 109 books
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
            print(compare_book["name_split"])
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
mdb_key = json_functions.read_data("p_k.json")
mdb_key = mdb_key["the_movie_db"]  # get mdb key


def request_movie(book_name, author_name_clean, source):  # search for movie via TheMovieDB API
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
                return movie_result # stop here if book writer is not credited in the movie
            try:
                movie_result = {"id": top_result["id"], "original_title": top_result["original_title"],
                                "poster_path": top_result["poster_path"],
                                "original_language": top_result["original_language"],
                                "vote_average": top_result["vote_average"], "release_date": top_result["release_date"],
                                "overview": top_result["overview"],
                                "movie_youtube_id": request_movie_trailer(top_result["id"]),
                                "credits": movie_credits, "total_results": 1}
                # only including movie details and youtube id if it is for a singular search
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
    moviedb_tv_url = "https://api.themoviedb.org/3/search/tv?api_key={0}&query={1}" \
                     "&language=en-US&page=1".format(mdb_key, book_name)  # this is the url for tv show search

    tv_result = requests.get(moviedb_tv_url).json()  # get the tv data from themoviedb
    try:
        if tv_result["total_results"] != 0:
            top_result = tv_result["results"][0]
            tv_credits = request_tv_credits(top_result["id"])
            if not data_functions.validate_writer(tv_credits, author_name_clean):
                tv_result["total_results"] = 0
                return tv_result # stop here if book writer is not credited in the tv show
            try:
                tv_result = {"id": top_result["id"], "original_name": top_result["original_name"],
                             "poster_path": top_result["poster_path"],
                             "original_language": top_result["original_language"],
                             "vote_average": top_result["vote_average"], "first_air_date": top_result["first_air_date"],
                             "overview": top_result["overview"],
                             "tv_youtube_id": request_tv_trailer(top_result["id"]),
                             "credits": tv_credits, "total_results": 1}
                # only including tv show details, credits, and youtube id if it is for a singular search
                if source == 0:
                    tv_result["tv_details"] = request_tv_details(top_result["id"])
            except KeyError as e:  # if there is a KeyError, just skip the result
                tv_result["total_results"] = 0
        else:
            tv_result["total_results"] = 0
    except KeyError as e:
        tv_result["total_results"] = 0

    return tv_result


def request_tv_details(tv_id):  # get details of the tv show [genre, production companies, imdb id]
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
