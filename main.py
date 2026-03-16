#!/usr/bin/env python3
import logging
from app import config
from app.web.server import start

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    config._load()
    start(host="0.0.0.0", port=3000)
