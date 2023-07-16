from functools import wraps
from utils import sleep_until
import logging
import requests
from requests.adapters import HTTPAdapter


def api_rate_control(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            result = func(*args, **kwargs)
            limit = result.headers.get(
                "x-ratelimit-limit")
            remaining = result.headers.get(
                "x-ratelimit-remaining")
            reset_time = result.headers.get(
                "x-ratelimit-reset")
            used = result.headers.get(
                "x-ratelimit-used"
            )
            if remaining == 0:
                logging.warning("api rate limit hit")
                time_wait = float(reset_time)
                sleep_until(time_wait)
                continue
            else:
                logging.info(f"github api quota used:"
                             f" {used} / limit {limit}")
                logging.info(f"github api quota remaining:"
                             f" {remaining}")
                return result

    return wrapper


class GitNotModified(Exception):
    """ Raised when requested object was not modified """
    pass


class GitHubClient:
    """ GitHub client class """

    def __init__(self, api_token, api_host=None, max_retries=1):
        self.api_host = api_host if api_host else "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {api_token}"
        }
        self.client = requests.Session()
        self.client.mount(self.api_host, HTTPAdapter(max_retries=max_retries))

    @api_rate_control
    def api_call(self, api_url=None, api_route=None, verb=None,
                 headers: dict = None, query: dict = None, data: dict = None):
        headers = {**self.headers, **(headers or {})}
        if verb is None:
            verb = "POST" if data else "GET"
        if api_url is None:
            api_url = f"{self.api_host}/{api_route}"
        try:
            logging.debug(f"calling api endpoint {api_url} "
                          f"with headers {headers} "
                          f"and parameters {query}")
            response = self.client.request(method=verb, url=api_url,
                                           headers=headers,
                                           params=query, json=data)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as err:
            logging.warning(f"Github API client error: {err}")
            raise

    def get_pull_request(self, repo_owner, repo_name, number,
                         entity_tag=None, last_modified=None):
        api_route = f"repos/{repo_owner}/{repo_name}/pulls/{number}"
        headers = {}

        if entity_tag is not None:
            headers["If-None-Match"] = entity_tag
        if last_modified is not None:
            headers["If-Modified-Since"] = last_modified

        response = self.api_call(api_route=api_route,
                                 verb="GET",
                                 headers=headers)

        if (entity_tag or last_modified) and response.status_code == 304:
            raise GitNotModified("requested object was not modified")

        return {
            "headers": dict(response.headers),
            "details": response.json()
        }

    def get_pull_request_reviews(self, repo_owner, repo_name, number, page=None,
                                 entity_tag=None, last_modified=None):
        api_route = f"repos/{repo_owner}/{repo_name}/pulls/{number}/reviews"
        api_query = {"page": page, "per_page": 100}
        headers = {}

        if entity_tag is not None:
            headers["If-None-Match"] = entity_tag
        if last_modified is not None:
            headers["If-Modified-Since"] = last_modified

        response = self.api_call(api_route=api_route,
                                 verb="GET",
                                 query=api_query,
                                 headers=headers)

        if (entity_tag or last_modified) and response.status_code == 304:
            raise GitNotModified("requested object was not modified")

        result = {
            "headers": dict(response.headers),
            "reviews": response.json()
        }

        if page is None and "next" in response.links.keys():
            while "next" in response.links.keys():
                _response = self.api_call(api_url=response.links["next"]["url"],
                                          verb="GET",
                                          query=api_query,
                                          headers=headers)
                result["headers"] = dict(_response.headers)
                result["reviews"] = _response.json()

        return result
