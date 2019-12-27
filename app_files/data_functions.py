import requests, random
from app_files import json_functions, API_functions


def validate_writer(credits, author_name_clean):  # method to find book author in the tv or movie credits
    """This function is used to make sure the author of a book has a writing credit in a movie or a tv show.

    Args:
        credits (dict): This argument contains the writing credits for a movie or tv show.
        author_name_clean (str): This is the name of the book author without spaces.

    Raises:
        None.

    Returns:
        boolean: Returns true if the book author is credited in the movie or tv show.
                 Returns false if the book author does not have a credit in the movie or tv show.
    """

    if len(credits[1]) == 0:
        return False
    else:
        for i in credits[1]:  # find book author as writer credit in tv show
            if i["department"] == "Writing":
                if i["name"].replace(" ", "") == author_name_clean:
                    # if author_name_clean.replace(" ", "") == writer_name.replace(" ", ""):
                    # print("Yes, same writer.")
                    return True
    return False  # will return false if author name is never found in credits


# if the Random Book button is chosen, then select a random book from the list
# try to match the book with a movie or tv show until one is found
def get_random_book():
    """This function uses the 'books_with_movies.json' file to find a random book to search for.

    Args:
        None.

    Raises:
        None.

    Returns:
        search_term: A random book title to search adaptations for.
    """

    books_list = json_functions.read_data("app_files/static/books_with_movies.json")
    matched = 0
    search_term = ""
    while matched != 1:
        # keep changing the random number until an actual book and tv show match is found
        rand_num = random.randint(0, 487)
        for item in books_list:
            if item["num"] == rand_num:
                search_term = item["title"]

                movie_result = API_functions.request_movie(search_term, item["author"],
                                                           0)  # use function in API_functions.py
                tv_result = API_functions.request_tv_show(search_term, item["author"], 0)
                # match book author to movie or tv show credits
                if (movie_result["total_results"] != 0 and
                    validate_writer(API_functions.request_movie_credits(movie_result["id"]), item["author"])) \
                        or (tv_result["total_results"] != 0 and
                            validate_writer(API_functions.request_tv_credits(tv_result["id"]), item["author"])):
                    search_term = item["title"]
                    matched = 1
                else:
                    matched = 0
    return search_term


# check if the url request returns an ok (200) response
# using this to check if actor image exists, if it doesnt't then a default is used
def url_exists(url):
    """This function is used to check if a image url exists.

    Args:
        url: The image url to test.

    Raises:
        None.

    Returns:
        boolean: Returns true if the image url returns an ok (200) response.
                 Returns false if the response is not an ok (200) response.
    """

    image = requests.head(url)
    return image.status_code == requests.codes.ok

