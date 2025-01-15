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
if os.path.isfile(os.path.join(REPOS_DIR, "hierosoft", "hierosoft",
                               "__init__.py")):
    sys.path.insert(0, os.path.join(REPOS_DIR, "hierosoft"))
import hierosoft.logging2 as logging  # noqa:E402 #type:ignore

logging.basicConfig(level=logging.INFO)

# Conditional imports for Python 2 and 3 compatibility
if sys.version_info.major >= 3:
    import urllib.request as request
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlparse, parse_qs, quote as urllib_quote
    from urllib.parse import quote_plus as urllib_quote_plus, urlencode
else:
    import urllib2 as urllib  # type:ignore
    request = urllib
    from urllib2 import HTTPError, URLError  # noqa: F401 # type:ignore
    from urlparse import urlparse, parse_qs  # noqa: F401 # type:ignore
    from urllib import quote as urllib_quote, quote_plus as urllib_quote_plus, urlencode  # noqa:E501,F401 #type:ignore
    from HTMLParser import HTMLParser  # noqa: F401 #type:ignore

ENABLE_SSH = True
config_dir = os.path.join(expanduser("~"), ".config", "repo-organizer")
backup_dir = os.path.join(expanduser("~"), "repo-organizer")
settings_path = os.path.join(config_dir, "settings.json")


def masked(v):
    return "*" * len(v)


class RepoCollection:
    """Handles operations related to GitHub repositories."""

    site = "github"
    user = None  # cannot use self.name for this if is_org!

    def __init__(self):
        self.repos = None
        self.name = None
        self.is_org = False
        self.json_urls = []
        self.token = None
        self.expected_res_type = list
        self.full_response = None

    def set_name(self, name, is_org, token=None):
        """Set the name and type of the collection."""
        self.name = name
        self.is_org = is_org
        if token:
            self.token = token
        if not is_org:
            RepoCollection.user = name

    @classmethod
    def cache_dir(cls):
        return os.path.join(config_dir, "cache", cls.site)

    def backup_dir(self):
        return os.path.join(backup_dir, self.site)

    def _get_headers(self):
        """Return headers for GitHub API requests,
        including authentication if available.
        """
        headers = {"Accept": "application/vnd.github.v3+json"}
        # or application/vnd.github+json
        if self.token:
            # headers["Authorization"] = "token {}".format(self.token)
            # ^ Doesn't work. See
            #   <https://github.com/orgs/community/discussions/24382>
            headers["Authorization"] = "Bearer {}".format(self.token)
        print("Using header:")
        for k, v in headers.items():
            v_msg = v
            if k.lower() == "authorization":
                v_msg = masked(v)
            print("{}: {}".format(k, v_msg))
        return headers

    def _get_url(self):
        """Construct the correct API URL based on user or organization type."""
        if not self.token:
            logging.error(
                "User not set, so auth token is not tested in this case!")
            url = "https://api.github.com/{}/{}/repos".format(
                "orgs" if self.is_org else "users", self.name
            )
            return url

        if self.is_org:  # and not RepoCollection.user:
            return "https://api.github.com/orgs/{}/repos".format(self.name)
        self.expected_res_type = dict
        return "https://api.github.com/search/repositories?q=user:{}".format(
            RepoCollection.user
        )

    def get_token_msg(self):
        token_msg = self.token
        if token_msg is not None:
            token_msg = masked(token_msg)
        return token_msg

    def _load_repos(self, refresh=False):
        """Load the repositories for the given GitHub organization or user."""
        repos_cache_path = os.path.join(
            RepoCollection.cache_dir(), self.name, "repos.json"
        )
        downloaded = False
        url = self._get_url()
        if url not in self.json_urls:
            self.json_urls.append(url)
        print("Listing repos using {}".format(url))

        if not refresh:
            if os.path.exists(repos_cache_path):
                with open(repos_cache_path, "r") as stream:
                    self.repos = json.load(stream)
                logging.info("Loaded repos from cache: %s", repos_cache_path)
                if not self.repos:
                    logging.warning(
                        "Got {} from {}".format(self.repos, repos_cache_path))
                    self.repos = None  # fall through to download
                    os.remove(repos_cache_path)
                else:
                    return

            logging.warning("No %s, so downloading from %s"
                            % (repos_cache_path, url))

        try:
            # response = request.urlopen(url)
            # self.repos = json.loads(response.read())
            request_obj = request.Request(url, headers=self._get_headers())
            response = request.urlopen(request_obj)
            self.full_response = json.loads(response.read().decode())
            if isinstance(self.full_response, dict):
                # Example:
                # {
                #   "total_count": 31,
                #   "incomplete_results": false,
                #   "items": [
                self.repos = self.full_response.get('items')
                if self.repos is None:
                    raise ValueError("Expected 'items' field, got only {}"
                                     .format([x for x in self.full_response]))
            else:
                self.repos = self.full_response  # must be a list already
                if self.expected_res_type is dict:
                    logging.warning("Got {} but expected dict"
                                    .format(type(self.full_response)))
            # with request.urlopen(req) as response:
            #     self.repos = json.loads(response.read().decode())
            downloaded = True
        except HTTPError as e:
            logging.error("Failed to fetch repositories from %s" % url)
            error_message = e.read().decode('utf-8')
            print("HTTPError: {} - {}".format(e.code, error_message))
            logging.error("self.token = {}".format(self.get_token_msg()))
            raise
        except URLError as e:
            logging.error("Failed to fetch repositories from %s" % url)
            print("URLError: {}".format(e.reason))
            # logging.error("Failed to fetch repositories: %s" % e)
            logging.error("self.token = {}".format(self.get_token_msg()))
            raise
        # Cache the results if downloaded
        if downloaded:
            if self.repos:
                os.makedirs(os.path.dirname(repos_cache_path), exist_ok=True)
                with open(repos_cache_path, "w") as stream:
                    json.dump(self.repos, stream, indent=2)
                logging.info("Cached repos to %s" % repos_cache_path)
            else:
                logging.warning("Got {} from {}".format(self.repos, url))
        if self.repos is None:
            raise NotImplementedError(
                "No repos loaded. repo-organizer should have loaded,"
                " downloaded, or raised a more exception first.")
        return

    def clone_repos(self, refresh=False):
        if self.repos is None or refresh:
            self._load_repos(refresh=refresh)
        for repo in self.repos:
            print()
            # example entries:
            # "name": "{repo_name}",
            # "full_name": "{self.name}/{repo_name}",
            # "fork": true,
            # "git_url": "git://github.com/{self.name}/{repo_name}.git",
            # "ssh_url": "git@github.com:{self.name}/{repo_name}.git",
            # "clone_url": "https://github.com/{self.name}/{repo_name}.git",
            url = repo['ssh_url']  # necessary for using ssh credentials on CLI
            dst_dir = os.path.join(self.backup_dir(),
                                   *repo['full_name'].split("/"))
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
                json.dump(repo, outs, indent=2)
                print("Saved {}".format(repr(meta_dst)))
            result = subprocess.Popen(cmd_parts, **popen_kwargs)
            # stdout=subprocess.PIPE
            # stderr=subprocess.PIPE
            text, errors = result.communicate()
            code = result.returncode
            if code != 0:
                logging.error("`{}` failed"  # in {}
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


def gather_repos(org_name, is_org, token=None, refresh=False, dry_run=False):
    """Handles repository operations for the given organization or user."""
    org = RepoCollection()
    org.set_name(org_name, is_org, token=token)
    logging.info("Collecting {} {} repo(s)"
                 .format(org_name, "org" if is_org else "user"))
    if not dry_run:
        org.clone_repos(refresh=refresh)
    return org


def main():
    """Main entry point for the script."""
    settings = load_settings()
    refresh = False
    for arg in sys.argv[1:]:
        if arg == "--refresh":
            refresh = True
        else:
            logging.error("Unknown argument: {}".format(arg))
            return 1

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
    tokens = None
    if sources:
        github = sources.get('github')
    if github:
        tokens = github.get('tokens')
    else:
        github = {}
    if not tokens:
        tokens = {}
    counts = {}
    collections = []
    no_token = {}
    no_token_total = 0
    for cat_name in ("orgs", "users"):
        no_token[cat_name] = []
        counts[cat_name] = 0
        names = github.get(cat_name)
        # if cat_name == "users": break  # for debug only!
        if names is None:
            logging.info("'{}' is None".format(cat_name))
        elif isinstance(names, list):
            for name in names:
                token = tokens.get(name)
                if not token:
                    no_token[cat_name].append(name)
                    no_token_total += 1
                collection = gather_repos(name, is_org=(cat_name == "orgs"),
                                          token=token,
                                          refresh=refresh,
                                          dry_run=False)  # True is debug only!
                collections.append(collection)
                counts[cat_name] += 1
        else:
            logging.error("{} is a {} (expected list). Check {}"
                          .format(repr(cat_name), type(cat_name).__name__,
                                  repr(settings_path)))
    # else the URL is used which lists all repos user can access
    #   (full name covers directory structure)

    logging.info("Processed {} orgs {} users"
                 .format(counts['orgs'], counts['users']))
    print()
    if no_token_total:
        print("Your tokens need to be set and have permissions"
              " to read repositories, branches, etc.! See readme.")
        print("The following names have no tokens in the 'tokens'"
              " dict in 'github' in {}: "
              .format(repr(settings_path)))
        print('{\n'
              '  "sources": {\n'
              '    "github":  {\n'
              '      "tokens": {\n')
        for cat_name in ("orgs", "users"):
            for name in no_token[cat_name]:
                print('        "{}": "[some {} token]",'
                      .format(name, cat_name))
    else:
        print("INFO: If private repos are still not cloned,"
              " try the --refresh argument."
              " Otherwise, ensure tokens have permissions to read repos"
              " for respective user or organization"
              " (must have separate token owned by organization)"
              " and are not expired."
              " Tokens were used for all list URLs during this run.")
    print("JSON URLs used:")
    for collection in collections:
        for json_url in collection.json_urls:
            print("- {}".format(json_url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
