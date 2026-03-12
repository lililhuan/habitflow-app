# asgi.py - ASGI entry point for production web deployment (Heroku, Render, Railway, Fly.io)
# Serves the Flet app via uvicorn as a FastAPI ASGI application.
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("FLET_WEB", "1")

import flet as ft
from app.main import main

app = ft.run(
    main,
    view=ft.AppView.WEB_BROWSER,
    export_asgi_app=True,
)
