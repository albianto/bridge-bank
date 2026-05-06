#!/usr/bin/env python3
import logging
import os
from app import config
from app.web.server import start

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    config._load()
    port = int(os.environ.get("INGRESS_PORT", os.environ.get("PORT", "3000")))
    start(host="0.0.0.0", port=port)
