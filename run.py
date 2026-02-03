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
    # ATENÇÃO: Este modo é APENAS para desenvolvimento local!
    # Em produção, SEMPRE use: gunicorn -c gunicorn.conf.py run:app
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    print(f"🚀 Starting Flask development server on port {Config.PORT}")
    print(f"⚠️  DEBUG MODE: {debug_mode}")
    if debug_mode:
        print("⚠️  WARNING: Debug mode is ENABLED. Do NOT use in production!")
    app.run(host="0.0.0.0", port=Config.PORT, debug=debug_mode)
