import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TORTOISE_ORM = {
    "connections": {
        "default": f"sqlite://{os.path.join(BASE_DIR, 'db.sqlite3')}",
    },
    "apps": {
        "data": {
            "models": ["models"],
            "default_connection": "default",
        },
    },
}