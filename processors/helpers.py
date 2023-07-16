from parsers import MessagePullRequestUrlParser,\
    PullRequestUrlParser, MessageReactionsParser
from clients import NoCachedData, CacheClient

import logging


def get_pull_request_urls(message):
    parser = MessagePullRequestUrlParser(message)
    if parser.pull_requests:
        return [PullRequestUrlParser(pr)
                for pr in parser.pull_requests]
    return None


def lookup_reaction(message, reaction):
    parser = MessageReactionsParser(message)
    if parser.reactions:
        return parser.lookup_reaction(reaction)
    return False


def get_cached_data(local_client: CacheClient, cache_path: str,
                    file_name: str = None):
    file_name = file_name if file_name else "data.json"
    try:
        cached_data = local_client.load_data_from_file(
            cache_path, file_name)
        return cached_data
    except NoCachedData:
        return None


def get_request_headers(cache_data: dict):
    headers = cache_data.get("headers", {})

    entity_tag = headers.get("ETag")
    last_modified = headers.get("Last-Modified")

    if entity_tag and not last_modified:
        logging.info(f"Using cached ETag header: {entity_tag}")
        return entity_tag, None

    if entity_tag and last_modified:
        logging.info(f"Using cached Last-Modified header: {last_modified}")
        return None, last_modified

    logging.warning("No cached headers to use")
    return None, None
