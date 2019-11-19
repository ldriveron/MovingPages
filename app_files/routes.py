import xml, collections
from rauth import OAuth1Service
import oauth2 as oauth
from app_files import app, API_functions, data_functions, json_functions
from flask import render_template, request, redirect, url_for, make_response
from xml.dom.minidom import *

app_name = "MOVING PAGES"  # name of app so it could be changed
previous_searches = collections.deque()  # deque for five most recent searches


@app.route('/')
def index():
    # if cookies are disabled, "cookies_disabled" will = 1
    # show status message to user that they need to be enabled for Goodreads authentication
    if request.args.get("cookies_disabled") == "1":
        status_num = 6
        status_msg = "Goodreads authentication requires cookies. Please enable them."
    else:
        status_msg = None
        status_num = 0

    # when navigating to the website, render the index.html page with default data
    return render_template("index.html", book_name=None, app_name=app_name, search=None,
                           status_msg=status_msg, status_num=status_num, previous_searches=previous_searches)


@app.route('/', methods=['POST'])  # this method is called when form is submitted
def search_for_adaptation():
    book_id = 0
    # variables for status results; 0 for no error, 1 for no book found, 2 for no movie found,
    # 3 for no tv show found, 4 for no tv show and movie found
    status_msg = ""
    status_num = 0

    # if the Random Book button is chosen, then select a random book from the list
    # try to match the book with a movie or tv show until one is found
    if request.args.get('random') == "1":
        search_term = data_functions.get_random_book()
    else:
        # if search input is used, then get the search term
        search_term = request.form['search']  # get search term from input box

    # Goodreads API functions
    gr_result = API_functions.request_book(search_term)  # use function in API_functions.py

    # if no book is found, generate status code
    if gr_result["total"] == 0:
        status_msg = "No matching book found for {0}. Try another.".format(search_term)
        status_num = 1

    # TheMovieDB functions
    movie_result = {}  # empty dictionary
    tv_result = {}  # empty dictionary
    if status_num == 0:  # only continue if there is a book found
        # search for movie
        # use function in API_functions.py
        movie_result = API_functions.request_movie(gr_result["name_split"], gr_result["author_name_clean"], 0)

        if movie_result["total_results"] != 0:  # if a movie is found, save some of its data
            movie_id = movie_result["id"]  # save movie ID

        else:  # if no movie is found, generate status message
            status_msg = "No movie found. Try another."
            status_num = 2

        # search for TV show
        # use function in API_functions.py
        tv_result = API_functions.request_tv_show(gr_result["name_split"], gr_result["author_name_clean"], 0)

        if tv_result["total_results"] != 0:  # if a tv show is found, save some of its data
            tv_id = tv_result["id"]  # save tv ID

        else:  # if no tv show is found, generate status message
            status_msg = "No TV Show found. Try another."
            status_num = 3

        if movie_result["total_results"] == 0 and tv_result["total_results"] == 0:
            # if no movie and tv show found, generate status message.
            # in the case they are found, but not based on the book, generate the same message
            status_msg = "No adaptation found for {0}. Try another.".format(search_term)
            status_num = 4

        if previous_searches.count(
                gr_result["name_split"]) == 0 and status_num != 4:  # only add if book name is not in deque
            if len(previous_searches) == 5:  # keep the deque at only five most recent searches
                previous_searches.pop()  # remove one if there is already five
            previous_searches.appendleft(gr_result["name_split"])  # add recent search to beginning of deque
    # render the page again with updated information, pass all data to render_template method
    return render_template("index.html", book_id=book_id, book_data=gr_result, movie_data=movie_result,
                           tv_data=tv_result, app_name=app_name, search=search_term, status_msg=status_msg,
                           status_num=status_num, previous_searches=previous_searches)


# OAuth service needs to be here to allow for multiple sessions at once
gr_key = json_functions.read_data("p_k.json")
gr_secret = gr_key["gr_secret"]
gr_key = gr_key["gr"]  # get Goodreads key
CONSUMER_KEY = gr_key
CONSUMER_SECRET = gr_secret
goodreads = OAuth1Service(
    consumer_key=gr_key,
    consumer_secret=gr_secret,
    name='goodreads',
    request_token_url='https://www.goodreads.com/oauth/request_token',
    authorize_url='https://www.goodreads.com/oauth/authorize',
    access_token_url='https://www.goodreads.com/oauth/access_token',
    base_url='https://www.goodreads.com/'
)


@app.route('/gr_result')  # route after authenticating the user on Goodreads (user will go here second)
def gr_result():
    status_msg = ""
    status_num = 0
    client = 0
    user_id = 0
    users_books = []

    # Get a real consumer key & secret from: https://www.goodreads.com/api/keys
    if request.args.get("authorize") == "1":  # if user authorized the connection
        try:
            # use cookies to get session tokens
            session = goodreads.get_auth_session(request.cookies.get('rt'),
                                                 request.cookies.get('rts'))  # get the current session
        except (KeyError, AttributeError) as e:
            return redirect(url_for('gr_init'))  # redirect to gr_init to try again

        # session information
        access_token = session.access_token
        access_token_secret = session.access_token_secret

        consumer = oauth.Consumer(key=CONSUMER_KEY,
                                  secret=CONSUMER_SECRET)
        token = oauth.Token(access_token,
                            access_token_secret)

        client = oauth.Client(consumer, token)
        url = 'http://www.goodreads.com'
        response, content = client.request('%s/api/auth_user' % url, 'GET')  # get the users goodreads ID
        if response['status'] != '200':
            raise Exception('Cannot fetch resource: %s' % response['status'])

        userxml = xml.dom.minidom.parseString(content)
        user_id = userxml.getElementsByTagName('user')[0].attributes['id'].value  # variable for user ID from Goodreads

        users_books = API_functions.get_users_books(user_id, client)  # use page to paginate results
        if len(users_books) == 1:  # check if adaptations were found for any books on users read list
            status_num = 6
            status_msg = "No adaptations found on your books list."
    else:  # if user did not authorize connection, generate a message
        status_msg = "Goodreads authentication required."
        status_num = 6  # number to identify an authentication requirement

    return render_template("gr_result.html", search=None, app_name=app_name, user_id=user_id, status_msg=status_msg,
                           status_num=status_num, users_books=users_books, previous_searches=previous_searches)


@app.route("/gr_init")
def gr_init():  # method to establish auth and create cookies (user will go here first)
    if request.args.get("authorize") != "1":
        request_token, request_token_secret = goodreads.get_request_token(header_auth=True)  # request a token to use

        authorize_url = goodreads.get_authorize_url(request_token)  # url for authorization

        res = make_response(render_template("gr_redirect.html", search=None, app_name=app_name, url=authorize_url,
                                            previous_searches=previous_searches,
                                            authorized=request.args.get("authorize"),
                                            oauth_token=None))  # redirect to gr_redirect

        res.set_cookie('rt', request_token, max_age=60 * 60 * 24 * 365 * 2)
        res.set_cookie('rts', request_token_secret,
                       max_age=60 * 60 * 24 * 365 * 2)  # make cookies using the token information
    else:
        res = make_response(render_template("gr_redirect.html", search=None, app_name=app_name, url=None,
                                            previous_searches=previous_searches,
                                            authorized=request.args.get("authorize"),
                                            oauth_token=request.cookies.get("rt")))  # redirect to gr_redirect

    return res  # set the cookies and go to gr_redirect.html for redirecting to authorize_url

