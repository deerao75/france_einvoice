from flask import Flask

# Initialize the app
app = Flask(__name__)

# Define the "route" (the URL path)
@app.route('/')
def hello_world():
    return '<h1>Hello, Flask!</h1>'

if __name__ == '__main__':
    app.run(debug=True)
