from clients import SlackClient
from parsers import MessagePullRequestUrlParser
from processors.helpers import lookup_reaction
from utils import get_arguments, SafeScheduler
from processors import PullRequestDetails,\
    PullRequestReview

import argparse
import queue
import logging
import time


def generate_messages(slack_api_token: str, channel_id: str, time_window: int, max_retries: int,):
    slack_client = SlackClient(api_token=slack_api_token, max_retries=max_retries)
    messages = slack_client.get_conversation_history(channel_id,
                                                     time_window)
    for message in messages:
        message_ts = message["ts"]
        replies = slack_client.get_conversation_replies(channel_id, time_window, message_ts)
        for reply in replies:
            yield reply


def publish_to_queues(config: argparse.Namespace, reviews_queue: queue.Queue, details_queue: queue.Queue):
    messages = generate_messages(config.slack_api_token, config.slack_channel_id,
                                 config.slack_time_window_minutes, config.max_client_retries)
    for message in messages:
        parser = MessagePullRequestUrlParser(message)

        # skip processing these messages (usually caused by no access to repos).
        if parser.pull_requests and lookup_reaction(
                message, config.slack_github_error_reaction_name):
            continue

        if parser.pull_requests and not lookup_reaction(
                message, config.slack_approved_reaction_name):
            reviews_queue.put(message)
        if parser.pull_requests and not lookup_reaction(
                message, config.slack_merged_reaction_name):
            details_queue.put(message)

    # block main thread until all tasks are processed by workers
    reviews_queue.join()
    details_queue.join()

    return None


def main():
    args = get_arguments()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s - "
                               "%(threadName)s - "
                               "%(levelname)s "
                               "%(message)s")

    reviews_queue = queue.Queue()  # PRs requiring approval
    details_queue = queue.Queue()  # PRs details (merged or not)

    processor_approve = PullRequestReview(args, reviews_queue)
    processor_merging = PullRequestDetails(args, details_queue)

    processor_approve.start()
    processor_merging.start()

    scheduler = SafeScheduler(reschedule_on_failure=True)

    scheduler.every(args.sleep_period_minutes).minutes.do(
        publish_to_queues, args, reviews_queue, details_queue
    )
    scheduler.run_all()

    while True:
        scheduler.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
