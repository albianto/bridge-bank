import schedule
import time
import logging
import threading
from datetime import datetime, timedelta, timezone
from . import db

logger = logging.getLogger(__name__)

def _should_catchup() -> bool:
    last = db.get_last_sync()
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - last_dt) > timedelta(hours=20)
    except Exception:
        return False

def _run_sync():
    from . import sync
    logger.info("Scheduled sync triggered at %s", datetime.now().isoformat())
    sync.run()

def start():
    from . import config
    hours = int(config.SYNC_INTERVAL_HOURS or 6)
    logger.info("Scheduler starting — syncing every %d hours", hours)

    schedule.every(hours).hours.do(_run_sync)

    if _should_catchup():
        logger.info("Last sync was >20 hours ago or never ran. Running catch-up sync.")
        threading.Thread(target=_run_sync, daemon=True).start()

    def loop():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    logger.info("Scheduler running.")
