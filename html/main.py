import flask
from flask import Flask


app = Flask(__name__)


@app.route("/")
def index():
    return flask.render_template('base.html')  

@app.route("/specifications")
def specifications():
    return flask.render_template('specifications.html')

@app.route("/base")
def base():
    return flask.render_template('base.html')















if __name__ == "__main__":
    app.run(debug=True)