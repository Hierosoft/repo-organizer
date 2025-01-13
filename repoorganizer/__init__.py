#!/usr/bin/env python
from __future__ import print_function
import os
import shlex
import subprocess
import sys
import json
from os.path import expanduser

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
REPOS_DIR = os.path.dirname(REPO_DIR)
if os.path.isfile(os.path.join(REPOS_DIR, "hierosoft", "hierosoft", "__init__.py")):
    sys.path.insert(0, os.path.join(REPOS_DIR, "hierosoft"))
import hierosoft.logging2 as logging

logging.basicConfig(level=logging.INFO)

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
config_dir = os.path.join(expanduser("~"), ".config", "repo-organizer")
backup_dir = os.path.join(expanduser("~"), "repo-organizer")
settings_path = os.path.join(config_dir, "settings.json")


class RepoCollection:
    """Handles operations related to GitHub repositories."""

    site = "github"

    def __init__(self):
        self.repos = None
        self.name = None
        self.is_org = False
        self.json_urls = []
        self.token = None

    def set_name(self, name, is_org):
        """Sets the name and type of the collection."""
        self.name = name
        self.is_org = is_org

    @classmethod
    def cache_dir(cls):
        return os.path.join(config_dir, "cache", cls.site)

    def backup_dir(self):
        return os.path.join(backup_dir, self.site)


    def _load_repos(self, refresh=False):
        """Loads the repositories for the given GitHub organization or user."""
        repo_cache = os.path.join(
            RepoCollection.cache_dir(), self.name, "repos.json"
        )
        downloaded = False

        url = "https://api.github.com/{}/{}/repos".format(
            "orgs" if self.is_org else "users", self.name
        )
        if url not in self.json_urls:
            self.json_urls.append(url)

        if not refresh:
            if os.path.exists(repo_cache):
                with open(repo_cache, "r") as cache_file:
                    self.repos = json.load(cache_file)
                logging.info("Loaded repos from cache: %s", repo_cache)
                return

            logging.warning("No %s, so downloading from %s" % (repo_cache, url))

        try:
            response = request.urlopen(url)
            self.repos = json.loads(response.read())
            downloaded = True
        except (HTTPError, URLError) as e:
            logging.error("Failed to fetch repositories: %s" % e)
            return
        # Cache the results if downloaded
        if downloaded:
            os.makedirs(os.path.dirname(repo_cache), exist_ok=True)
            with open(repo_cache, "w") as cache_file:
                json.dump(self.repos, cache_file, indent=2)
            logging.info("Cached repos to %s" % repo_cache)

    def clone_repos(self, refresh=False):
        if self.repos is None or refresh:
            self._load_repos(refresh=refresh)
        for repo in self.repos:
            # example entries:
            # "name": "openmrn",
            # "full_name": "traincontrolsystems/openmrn",
            # "fork": true,
            # "git_url": "git://github.com/traincontrolsystems/openmrn.git",
            # "ssh_url": "git@github.com:traincontrolsystems/openmrn.git",
            # "clone_url": "https://github.com/traincontrolsystems/openmrn.git",
            url = repo['ssh_url']  # necessary for using ssh credentials on CLI
            dst_dir = os.path.join(self.backup_dir(), *repo['full_name'].split("/"))
            dst_parent = os.path.dirname(dst_dir)
            popen_kwargs = {}
            if not os.path.isdir(dst_dir):
                os.makedirs(dst_dir)
                cmd_parts = ["git", "clone", url, dst_dir]
            else:
                popen_kwargs['cwd'] = dst_dir
                print("git pull  # in {}".format(repr(dst_dir)))
                cmd_parts = ["git", "pull"]
            meta_dst = os.path.join(dst_parent, "{}.json".format(repo['name']))
            with open(meta_dst, "w") as outs:
                json.dump(self.repos, outs, indent=2)
            result = subprocess.Popen(cmd_parts, **popen_kwargs)
            # stdout=subprocess.PIPE
            # stderr=subprocess.PIPE
            text, errors = result.communicate()
            code = result.returncode
            if code != 0:
                logging.error("`{}` failed"  #  in {}
                              .format(shlex.join(cmd_parts)))  # dst_dir
                logging.error()

def load_settings():
    """Loads the settings from ~/.config/repo-organizer/settings.json."""

    if not os.path.exists(settings_path):
        logging.error("Settings file not found: %s" % settings_path)
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
    logging.info("Collecting {} {} repo(s)"
                 .format(org_name, "org" if is_org else "user"))
    org.clone_repos(refresh=False)
    return org


def main():
    """Main entry point for the script."""
    settings = load_settings()

    github = settings["sources"]["github"]
    orgs = github.get("orgs")
    users = github.get("users")

    if not orgs and not users:
        logging.error(
            'No "orgs" or "users" specified under'
            ' "sources":{"github"... in settings.')
        return 1

    sources = settings.get('sources')
    github = None
    if sources:
        github = sources.get('github')
    if github:
        token = github.get('token')

    counts = {'orgs': 0, 'users': 0}
    all_json_urls = []
    collections = []
    if orgs is None:
        logging.info("orgs is None")
    elif isinstance(orgs, list):
        for org_name in orgs:
            collection = gather_repos(org_name, is_org=True)
            collections.append(collection)
            counts['orgs'] += 1
    else:
        logging.error("orgs is a {} (expected list). Check {}"
                      .format(type(orgs), repr(settings_path)))

    if users is None:
        logging.info("users is None")
    elif isinstance(users, list):
        for user_name in users:
            collection = gather_repos(user_name, is_org=False)
            collections.append(collection)
            counts['users'] += 1
    else:
        logging.error("users is a {} (expected list). Check {}"
                      .format(type(users), repr(settings_path)))

    logging.info("Processed {} orgs {} users"
                 .format(counts['orgs'], counts['users']))
    print()
    token_msg = ""
    if token:
        token_msg = " Your token in settings was used."
    msg = (
        "Private repos will not be shown unless you use"
        " a token.{} See {} to see what was listed. The token must"
        " be for a collaborator or team member with permission"
        " to list and clone desired repos:"
        .format(token_msg, repr(RepoCollection.cache_dir()))
    )
    # logging.warning(msg)
    print(msg)
    for collection in collections:
        for json_url in collection.json_urls:
            print("- {}".format(json_url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
