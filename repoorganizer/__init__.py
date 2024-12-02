#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import json
import logging2 as logging
from os.path import expanduser

# Conditional imports for Python 2 and 3 compatibility
if sys.version_info.major >= 3:
    import urllib.request as request
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlparse, parse_qs, quote as urllib_quote
    from urllib.parse import quote_plus as urllib_quote_plus, urlencode
else:
    import urllib2 as urllib
    request = urllib
    from urllib2 import HTTPError, URLError
    from urlparse import urlparse, parse_qs
    from urllib import quote as urllib_quote, quote_plus as urllib_quote_plus, urlencode
    from HTMLParser import HTMLParser  # noqa: F401

ENABLE_SSH = True


class RepoCollection:
    """Handles operations related to GitHub repositories."""

    def __init__(self):
        self.repos = None
        self.name = None
        self.is_org = False

    def set_name(self, name, is_org):
        """Sets the name and type of the collection."""
        self.name = name
        self.is_org = is_org

    def load_repos(self, refresh=False):
        """Loads the repositories for the given GitHub organization or user."""
        repo_cache = os.path.join(
            expanduser("~"), ".config", "repo-organizer", self.name, "repos.json"
        )
        downloaded = False

        if not refresh:
            if os.path.exists(repo_cache):
                with open(repo_cache, "r") as cache_file:
                    self.repos = json.load(cache_file)
                logging.info("Loaded repos from cache: %s", repo_cache)
                return

            url = "https://api.github.com/{}/{}".format(
                "orgs" if self.is_org else "users", self.name
            )
            logging.warning("No %s, so downloading %s", repo_cache, url)

        # Download repositories from GitHub
        url = "https://api.github.com/{}/{}/repos".format(
            "orgs" if self.is_org else "users", self.name
        )
        try:
            response = request.urlopen(url)
            self.repos = json.loads(response.read())
            downloaded = True
        except (HTTPError, URLError) as e:
            logging.error("Failed to fetch repositories: %s", e)
            return

        # Cache the results if downloaded
        if downloaded:
            os.makedirs(os.path.dirname(repo_cache), exist_ok=True)
            with open(repo_cache, "w") as cache_file:
                json.dump(self.repos, cache_file)
            logging.info("Cached repos to %s", repo_cache)


def load_settings():
    """Loads the settings from ~/.config/repo-organizer/settings.json."""
    config_dir = os.path.join(expanduser("~"), ".config", "repo-organizer")
    settings_path = os.path.join(config_dir, "settings.json")

    if not os.path.exists(settings_path):
        logging.error("Settings file not found: %s", settings_path)
        sys.exit(1)

    with open(settings_path, "r") as settings_file:
        settings = json.load(settings_file)

    # Validate structure
    if "sources" not in settings:
        logging.error("Missing 'sources' key in settings.")
        sys.exit(1)

    github = settings["sources"].get("github")
    if github is None:
        logging.error("Missing 'github' key in 'sources'.")
        sys.exit(1)

    return settings


def gather_repos(org_name, is_org):
    """Handles repository operations for the given organization or user."""
    org = RepoCollection()
    org.set_name(org_name, is_org)
    org.load_repos(refresh=False)


def main():
    """Main entry point for the script."""
    config_dir = os.path.join(expanduser("~"), ".config", "repo-organizer")
    settings = load_settings()

    github = settings["sources"]["github"]
    orgs = github.get("orgs")
    users = github.get("users")

    if not orgs and not users:
        logging.error("No 'orgs' or 'users' specified in settings.")
        return 1

    if isinstance(orgs, list):
        for org_name in orgs:
            gather_repos(org_name, is_org=True)

    if isinstance(users, list):
        for user_name in users:
            gather_repos(user_name, is_org=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
