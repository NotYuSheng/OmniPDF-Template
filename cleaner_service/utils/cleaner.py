from collections import defaultdict

from redis import Redis

from shared_utils.ttl_utils import CHROMA_FLAG, S3_FLAG, REDIS_FLAG, SEPERATOR
from shared_utils.redis import config, RedisStringStorage, RedisSetStorage
from shared_utils.s3_utils import delete_file

# UNABLE TO HANDLE srem AND OTHERS DUE TO ONLY HAVING EVENT AND KEY INFO

REMOVAL_EVENTS = ["del", "expired"]
ADDITION_EVENTS = ["new"]


def EMPTY_FUNCTION(x):
    pass

def clean_redis_key(key: str):
    print("deleting redis key", key)
    redis_storage = RedisStringStorage()
    del redis_storage[key]


def clean_s3_files(key: str):
    print("deleting s3 key", key)
    redis_set_store = RedisSetStorage()
    for doc_id in redis_set_store[key]:
        doc_id = doc_id.decode()
        print("deleting" + doc_id)
        delete_file(doc_id)
    del redis_set_store[key]


def clean_chromadb(key):
    pass


deletion_prefix_callback_dict = defaultdict(EMPTY_FUNCTION)
for key, func in {
    S3_FLAG: clean_s3_files,
    REDIS_FLAG: clean_redis_key,
    CHROMA_FLAG: clean_chromadb,
}.items():
    deletion_prefix_callback_dict[key] = func


def setup_session_expiry_timer(key: str):
    redis_store = RedisStringStorage()
    timer_key = S3_FLAG + ":" + key
    redis_store[timer_key]
    redis_store.client.expire(timer_key, 120)


addition_prefix_callback_dict = defaultdict(EMPTY_FUNCTION)
for key, func in {"Session_Files": setup_session_expiry_timer}.items():
    addition_prefix_callback_dict[key] = func


def event_handler(msg):
    print(
        "handler --",
        msg["type"],
        f"({msg['pattern']})",
        "from",
        msg["channel"],
        ":",
        msg["data"],
    )
    if msg["type"] != "pmessage":
        return

    msg_origin = msg["channel"].decode()
    if any(event in msg_origin for event in REMOVAL_EVENTS):
        msg_data: str = msg["data"].decode()
        flag, key = msg_data.split(SEPERATOR, maxsplit=1)
        # (deletion_prefix_callback_dict[flag])(key)
        deletion_prefix_callback_dict.get(flag, lambda x: None)(key)

    if any(event in msg_origin for event in ADDITION_EVENTS):
        msg_data: str = msg["data"].decode()
        prefix, key = msg_data.split(SEPERATOR, maxsplit=1)
        # (addition_prefix_callback_dict[prefix])(key)
        addition_prefix_callback_dict.get(prefix, lambda x: None)(key)
    # if "del" in msg_data or "expired" in msg_data:
    #     if REDIS_FLAG in msg_origin:
    #         _, key_to_delete = msg_origin.split(REDIS_FLAG)
    #         clean_redis_key(key_to_delete)
    #     elif S3_FLAG in msg_origin:
    #         # Dangerous, assumes file_ids stored in a set
    #         _, key_to_delete = msg_origin.split(S3_FLAG)
    #         for doc_id in redis_set_store[key_to_delete]:
    #             doc_id = doc_id.decode()
    #             print("deleting" + doc_id)
    #             delete_file(doc_id)
    #         del redis_store[key_to_delete]
    #     elif CHROMA_FLAG in msg_origin:
    #         _, key_to_delete = msg_origin.split(CHROMA_FLAG)
    #         del redis_store[key_to_delete]


def setup_redis_watcher():
    client = Redis.from_url(config.redis_url)
    # resp = client.config_set("notify-keyspace-events", "KEA")
    client.config_set("notify-keyspace-events", "Egsxn")
    pubsub = client.pubsub()
    sub_key = "__key*__:*"
    pubsub.psubscribe(**{sub_key: event_handler})
    print(pubsub.patterns)
    print(pubsub.channels)
    return pubsub


pubsub = setup_redis_watcher()
# pubsub.run_in_thread()
# OR
print("setup complte")
for msg in pubsub.listen():
    pass


#  {'type': 'psubscribe', 'pattern': None, 'channel': b'__keyevent@*__', 'data': 1}
# ^ sub message reply
