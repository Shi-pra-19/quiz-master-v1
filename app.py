from extensions import db
from config import Config
from model import create_test_data
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  
        create_test_data()
    app.run(debug=True)