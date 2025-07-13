import logging

from utils.cleaner import setup_redis_watcher_thread

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    # load the redis watcher
    watcher_thread = setup_redis_watcher_thread()
    logger.info(f"{watcher_thread}")
    watcher_thread.join()
    # stop the watcher
    watcher_thread.stop()
    logger.info("Stopped well")


if __name__ == "__main__":
    main()