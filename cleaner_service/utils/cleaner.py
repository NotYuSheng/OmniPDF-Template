import logging

from redis import Redis

from shared_utils.ttl_utils import CHROMA_FLAG, S3_FLAG, REDIS_FLAG, SEPERATOR
from shared_utils.redis import config, RedisStringStorage, RedisSetStorage
from shared_utils.s3_utils import delete_file

logger = logging.getLogger(__name__)

# UNABLE TO HANDLE srem AND OTHERS DUE TO ONLY HAVING EVENT AND KEY INFO

REMOVAL_EVENTS = ["del", "expired"]
ADDITION_EVENTS = ["new"]


def EMPTY_FUNCTION(x):
    pass

def clean_redis_key(key: str):
    logger.info(f"deleting redis {key}")
    redis_storage = RedisStringStorage()
    del redis_storage[key]


def clean_s3_files(key: str):
    logger.info(f"deleting s3 {key}")
    redis_set_store = RedisSetStorage()
    for doc_id in redis_set_store[key]:
        doc_id = doc_id
        if doc_id:
            logger.info(f"deleting {doc_id}")
            delete_file(f"{doc_id}.pdf")
    del redis_set_store[key]

def clean_s3_file(key: str):
    logger.info(f"deleting {key}")
    delete_file(key)

def clean_chromadb(key):
    pass


deletion_prefix_callback_dict = {
    S3_FLAG: clean_s3_files,
    "SessionHeader": clean_s3_files,
    "S3_File": clean_s3_file,
    REDIS_FLAG: clean_redis_key,
    CHROMA_FLAG: clean_chromadb,
}


def setup_session_expiry_timer(key: str):
    logger.info(f"Adding expiring for {key}")
    redis_store = RedisStringStorage()
    timer_key = S3_FLAG + ":" + key
    redis_store[timer_key] = 1
    redis_store.client.expire(timer_key, 10)


addition_prefix_callback_dict = {"Session_Files": setup_session_expiry_timer}


def event_handler(msg):
    logger.info(f'handler -- {msg["type"]} {msg['pattern']}) from {msg["channel"]}: {msg["data"]}')
    if msg["type"] != "pmessage":
        return
    msg_origin = msg["channel"]
    if any(event in msg_origin for event in REMOVAL_EVENTS):
        msg_data: str = msg["data"]
        flag, key = msg_data.split(SEPERATOR, maxsplit=1)
        # (deletion_prefix_callback_dict[flag])(key)
        deletion_prefix_callback_dict.get(flag, lambda x: None)(key)

    # if any(event in msg_origin for event in ADDITION_EVENTS):
    #     msg_data: str = msg["data"]
    #     prefix, key = msg_data.split(SEPERATOR, maxsplit=1)
    #     # (addition_prefix_callback_dict[prefix])(key)
    #     addition_prefix_callback_dict.get(prefix, lambda x: None)(msg_data)


async def setup_redis_watcher_thread():
    client = Redis.from_url(config.redis_url)
    # resp = client.config_set("notify-keyspace-events", "KEA")
    client.config_set("notify-keyspace-events", "Egsxn")
    pubsub = client.pubsub()
    sub_key = "__key*__:*"
    pubsub.psubscribe(**{sub_key: event_handler})
    logger.info(pubsub.patterns)
    logger.info(pubsub.channels)
    logger.info("Competed setup")
    return client, pubsub, pubsub.run_in_thread()


if __name__ == "__main__":
    pubsub = setup_redis_watcher_thread()
    # pubsub.run_in_thread()
    # OR
    logger.info("setup complte")
    for msg in pubsub.listen():
        pass


#  {'type': 'psubscribe', 'pattern': None, 'channel': b'__keyevent@*__', 'data': 1}
# ^ sub message reply
