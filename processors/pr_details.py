from .processors import ProcessorBase
from .helpers import get_pull_request_urls,\
    get_cached_data, get_request_headers
from parsers import PullRequestUrlParser, PullRequestDataParser

from clients.github import GitNotModified
from requests.exceptions import RequestException, HTTPError
from slack_sdk.errors import SlackApiError

import logging
import argparse
import queue


class PullRequestDetails(ProcessorBase):
    def __init__(self, args_config: argparse.Namespace, source_queue: queue.Queue):
        super().__init__(args_config)

        self.source_queue = source_queue
        self.name = "PrDetailsProcessor"
        self.reaction = self.config.slack_merged_reaction_name

    def get_url_data(self, url: PullRequestUrlParser, cache_path: str):
        cached_data = get_cached_data(self.cache_client, cache_path)

        is_merged = PullRequestDetails.is_merged(cached_data)
        if cached_data and is_merged:
            return cached_data, is_merged

        if cached_data and not is_merged:
            entity_tag, last_modified = get_request_headers(cached_data)
            url.api_params.update({
                "entity_tag": entity_tag,
                "last_modified": last_modified
            })
        try:
            data = self.git_client.get_pull_request(**url.api_params)
        except GitNotModified as err:
            logging.info(err)
            data = cached_data
        except HTTPError as err:
            logging.warning(f"github client error: {err}")
            data = None

        is_merged = PullRequestDetails.is_merged(data)
        return data, is_merged

    def run(self):
        while True:
            message = self.source_queue.get()
            pull_request_states = []
            pull_request_caches = []
            try:
                pull_request_urls = get_pull_request_urls(message)
                for url in pull_request_urls:

                    cache_folder = f"{url.cache_path}/details"
                    state = self.process_pull_request(self.get_url_data,
                                                      url, cache_folder,
                                                      message)
                    pull_request_states.append(state)
                    pull_request_caches.append(cache_folder)

            except RequestException as err:
                logging.warning(f"github client exception: {err}")
                pass
            except SlackApiError as err:
                logging.warning(f"slack client exception: {err}")
                pass

            if pull_request_states and all(pull_request_states):
                self.add_reaction(message["ts"], self.reaction)

                for cache_path in pull_request_caches:
                    self.cache_client.clean_up_cached_dir(cache_path)

            self.source_queue.task_done()

    @staticmethod
    def is_merged(pull_request_data: dict):
        if pull_request_data:
            data_parser = PullRequestDataParser(pull_request_data)
            return data_parser.is_merged()
        else:
            return False
