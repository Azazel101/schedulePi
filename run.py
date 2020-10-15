from app import app
from app.views import initialize

if __name__ == "__main__":
    initialize()
    app.run(host='0.0.0.0', port=80)
