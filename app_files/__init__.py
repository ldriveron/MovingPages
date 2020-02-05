from flask import Flask, redirect, request

app = Flask(__name__)
app._static_folder = "static"  # set a static files folder for Flask app


# Redirect all HTTP traffic to HTTPS
@app.before_request
def before_request():
    if not request.is_secure and app.env != "development":
        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)


from app_files import routes  # import the routes python file
