import unittest
from app_files import API_functions, data_functions


class MovingPagesAPITests(unittest.TestCase):
    # search for a book that does not exist
    def test_book_search_zero(self):
        result = API_functions.request_book("poaskk oewrof kl")

        # since this is not a title for any book that exists in Goodreads, we can assert that the total result is 0
        self.assertTrue(result["total"] == 0)

    # search for a book that exists
    def test_book_search_zero_one(self):
        result = API_functions.request_book("Harry Potter and the Goblet of Fire")

        # since this is a book that exists, we can assert that the total result is 1
        self.assertTrue(result["total"] == 1)

    # search for a movie that actually exists
    def test_movie_search_one(self):
        book = API_functions.request_book("The Great Gatsby")
        result = API_functions.request_movie(book["name"], book["author_name_clean"], 0)

        # since this is a movie that exists, we can assert that there will be 1 result
        self.assertTrue(result["total_results"] == 1)

    # search for a movie that doesn't exist
    def test_movie_search_zero(self):
        book = API_functions.request_book("I Let you go")
        result = API_functions.request_movie(book["name"], book["author_name_clean"], 0)

        # since this is a movie that does not exist, we can assert that there will be 0 results
        self.assertTrue(result["total_results"] == 0)

    # search for a tv show that actually exists
    def test_tv_search_one(self):
        book = API_functions.request_book("The Handmaid's Tale")
        result = API_functions.request_tv_show(book["name"], book["author_name_clean"], 0)

        # since this is a tv show that exists, we can assert that there will be 1 result
        self.assertTrue(result["total_results"] == 1)

    # search for a tv show that doesn't exist
    def test_tv_search_zero(self):
        book = API_functions.request_book("The Way Of Kings")
        result = API_functions.request_tv_show(book["name"], book["author_name_clean"], 0)

        # since this is a tv show that does not exist, we can assert that there will be 0 results
        self.assertTrue(result["total_results"] == 0)

    # testing the validate_writer method in data_functions
    def test_validate_writer(self):
        book = API_functions.request_book("The Handmaid's Tale")
        result = API_functions.request_tv_show(book["name"], book["author_name_clean"], 0)
        validate = data_functions.validate_writer(result["credits"], book["author_name_clean"])

        # since the writer of the book is credited as a writer in the tv show, we can assert
        # validate writer will return true
        self.assertTrue(validate)

    if __name__ == '__main__':
        unittest.main()


