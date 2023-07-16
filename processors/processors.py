from clients import *
from parsers import *
from threading import Thread
import argparse

from slack_sdk.errors import SlackApiError


class ProcessorBase(Thread):
    def __init__(self, args_config: argparse.Namespace):
        super().__init__()

        self.daemon = True
        self.config = args_config

        self.git_client = GitHubClient(
            api_token=args_config.github_api_token,
            max_retries=args_config.max_client_retries
        )
        self.slack_client = SlackClient(
            api_token=args_config.slack_api_token,
            max_retries=args_config.max_client_retries
        )
        self.cache_client = CacheClient(
            local_dir_path=args_config.cache_folder_path
        )

        self.reaction_err = self.config.slack_github_error_reaction_name

    def process_pull_request(self, func_to_run, url: PullRequestUrlParser,
                             cache_folder: str, message: dict):
        url_data, state = func_to_run(url, cache_folder)
        if url_data:
            self.cache_client.save_data_to_file(url_data, cache_folder)
        if url_data is None:
            # Indicate that fetching data failed by adding an error reaction
            self.add_reaction(message["ts"], self.reaction_err)
            # Clean up and stop processing
            self.cache_client.clean_up_cached_dir(cache_folder)
            return False
        return state

    def add_reaction(self, message_ts: str, reaction: str):
        try:
            self.slack_client.add_message_reaction(
                self.config.slack_channel_id,
                reaction, message_ts,
                self.config.dry_run)
        except SlackApiError as e:
            if e.response["error"] == "already_reacted":
                pass

    def run(self):
        pass
