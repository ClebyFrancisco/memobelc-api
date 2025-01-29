"""
Entry point for starting the Flask application.

This script initializes the Flask app by calling `create_app()` from the
application factory located in `src.app`. It then runs the app with the specified
host, port, and debug mode. This allows the application to be accessible at
http://0.0.0.0:5000 when executed directly.

Attributes:
    app (Flask): The main Flask application instance created by `create_app()`.

Usage:
    Run this script to start the Flask application:
    ```
    python run.py
    ```
"""

import sys
sys.path.append('./src')

from src.app import create_app
from src.app import Config
import os

app = create_app()

if __name__ == "__main__":
    print(Config.PORT)
    app.run(host="0.0.0.0", port=Config.PORT)
