import logging
from urllib.parse import urlparse


class PullRequestUrlParser:
    """ Pull Request URL Parser """

    def __init__(self, pull_request_url):
        logging.info(f"parsing pull request url {pull_request_url}"
                     f" using {self.__class__.__name__}")
        self.url = pull_request_url
        self.url_path = urlparse(self.url).path.split("/")

        self.api_params = self.api_params_from_url()
        self.cache_path = self.generate_cache_path()

    def api_params_from_url(self):
        try:
            params = {"repo_owner": self.url_path[1], "repo_name": self.url_path[2], "number": self.url_path[4]}
            return params
        except IndexError:
            return None

    def generate_cache_path(self):
        try:
            cache_path = f"repos/{self.url_path[1]}/{self.url_path[2]}/{self.url_path[4]}"
            return cache_path
        except IndexError:
            return None


class PullRequestDataParser:
    """ Pull Request Data Parser """

    def __init__(self, pull_request_data):
        self.data = pull_request_data
        if self.data:
            logging.info("parsing pull request data using"
                         f" {self.__class__.__name__}")

    def is_merged(self):
        details = self.data.get("details", {})
        merged = details.get("merged")
        html_url = details.get("html_url")
        if merged:
            if html_url:
                logging.info(f"pull request [{html_url}] is merged")
                return True
        logging.info("pull request is not merged")
        return False

    def is_approved(self):
        reviews = self.data.get("reviews", [])
        states = [review["state"] for review in reviews]
        hrefs = [review["html_url"] for review in reviews]
        if states and states[-1] == "APPROVED":
            logging.info(f"pull request is approved: {hrefs[-1]}")
            return True
        else:
            logging.info(f"pull request is not approved")
            return False
