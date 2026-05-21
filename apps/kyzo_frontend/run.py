"""Entry point — starts the Flask development server."""

import sys
import os

# Add the 'apps' directory to the Python path so we can import kyzo_frontend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kyzo_frontend import create_app

app = create_app("development")

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
