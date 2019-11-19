import requests
from bs4 import BeautifulSoup
from app_files import json_functions, API_functions, data_functions

# script just to get name of book and rating from a list of books with movies from Goodreads
# will be used for random book search and also based on rating
# will be used for auto suggestion when searching
# only saving books with adaptation result
page = 1
books = []
num = 0
for full in range(15):
    print(page)
    URL = "https://www.goodreads.com/list/show/429.The_BOOK_was_BETTER_than_the_MOVIE?page={0}".format(page)
    r = requests.get(URL)

    text = BeautifulSoup(r.content, 'html5lib')
    for item in text.findAll('tr', attrs={'itemtype': 'http://schema.org/Book'}):
        search_term = item.find('div', attrs={'data-resource-type': 'Book'}).a['title']
        movie_result = API_functions.request_movie(search_term,
                                                   0)  # use function in API_functions.py
        tv_result = API_functions.request_tv_show(search_term, 0)

        if (movie_result["total_results"] != 0 and
            data_functions.validate_writer(API_functions.request_movie_credits(movie_result["id"]),
                                           item.find('span', attrs={'itemprop': 'author'}).find('span', attrs={
                                               'itemprop': 'name'}).text.replace(" ", ""),)) \
                or (tv_result["total_results"] != 0 and
                    data_functions.validate_writer(API_functions.request_tv_credits(tv_result["id"]),
                                                   item.find('span', attrs={'itemprop': 'author'}).find('span',
                                                                                                        attrs={
                                                                                                            'itemprop': 'name'}).text.replace(
                                                       " ", ""),)):
            books.append({'num': num, 'title': item.find('div', attrs={'data-resource-type': 'Book'}).a['title'],
                          'author': item.find('span', attrs={'itemprop': 'author'}).find('span', attrs={
                              'itemprop': 'name'}).text.replace(" ", ""),
                          'rating': item.find('span', attrs={'class': 'minirating'}).text[1:4]})
            num += 1

    page += 1

json_functions.save_request(books, 'books_with_movies.json')