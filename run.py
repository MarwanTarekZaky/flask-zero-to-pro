from app import create_app
from app.config import DevConfig

# Create the Flask application using the factory pattern
app = create_app(DevConfig)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)