from __future__ import print_function
import os
import shlex
import subprocess
import sys
import json

from repoorganizer.moregitcli import (
    current_branch,
    list_remote_branches,
    switch_branch,
    pull_repo,
)


MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
REPOS_DIR = os.path.dirname(REPO_DIR)
if os.path.isfile(os.path.join(REPOS_DIR, "hierosoft", "hierosoft",
                               "__init__.py")):
    sys.path.insert(0, os.path.join(REPOS_DIR, "hierosoft"))

from hierosoft.logging2 import getLogger  # noqa: E402  #type:ignore
# import hierosoft.logging2 as logging  # noqa:E402 #type:ignore

# logging.basicConfig(level=logging.INFO)

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

from repoorganizer import (  # noqa: E402
    config_dir,
    backup_dir,
    masked,
)


logger = getLogger(__name__)


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
        self.sites_dir = None

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
        if self.sites_dir:
            os.path.join(self.sites_dir, self.site)
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
            logger.error(
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
                logger.info("Loaded repos from cache: %s", repos_cache_path)
                if not self.repos:
                    logger.warning(
                        "Got {} from {}".format(self.repos, repos_cache_path))
                    self.repos = None  # fall through to download
                    os.remove(repos_cache_path)
                else:
                    return

            logger.warning(
                "No %s, so downloading from %s"
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
                    logger.warning(
                        "Got {} but expected dict"
                        .format(type(self.full_response)))
            # with request.urlopen(req) as response:
            #     self.repos = json.loads(response.read().decode())
            downloaded = True
        except HTTPError as e:
            logger.error("Failed to fetch repositories from %s" % url)
            error_message = e.read().decode('utf-8')
            print("HTTPError: {} - {}".format(e.code, error_message))
            logger.error("self.token = {}".format(self.get_token_msg()))
            raise
        except URLError as e:
            logger.error("Failed to fetch repositories from %s" % url)
            print("URLError: {}".format(e.reason))
            # logger.error("Failed to fetch repositories: %s" % e)
            logger.error("self.token = {}".format(self.get_token_msg()))
            raise
        # Cache the results if downloaded
        if downloaded:
            if self.repos:
                os.makedirs(os.path.dirname(repos_cache_path), exist_ok=True)
                with open(repos_cache_path, "w") as stream:
                    json.dump(self.repos, stream, indent=2)
                logger.info("Cached repos to %s" % repos_cache_path)
            else:
                logger.warning("Got {} from {}".format(self.repos, url))
        if self.repos is None:
            raise NotImplementedError(
                "No repos loaded. repo-organizer should have loaded,"
                " downloaded, or raised a more exception first.")
        return

    def clone_repos(self, refresh=False, forks=True, destination=None):
        """Clone all repos in the collection.

        Args:
            refresh (bool, optional): Download metadata again. Advisable
                if token was changed or added since last run, or if new
                repos were added! Defaults to False.
            forks (bool, optional): Include repos which are forks.
                Defaults to True.
            destination (str, optional): Parent for site dir
                (RepoCollection.site) which will be added under it.
                Defaults to backup_dir or last used destination
                (sets self.sites_dir).
        """
        if destination:
            self.sites_dir = backup_dir  # affect result of self.backup_dir
        if self.repos is None or refresh:
            self._load_repos(refresh=refresh)
        for repo in self.repos:
            print()
            default_branch = repo.get("default_branch")
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
                logger.error(
                    "`{}` failed"  # in {}
                    .format(shlex.join(cmd_parts)))  # dst_dir
                logger.error()
            previous_branch = current_branch(dst_dir)
            if not previous_branch:
                print("Skipping {} (bare repo assumed--no branch selected)"
                      .format(repr(dst_dir)))
                continue
            branches = list_remote_branches(dst_dir)
            for branch in branches:
                switch_branch(dst_dir, branch)
                pull_repo(dst_dir)
            switch_branch(dst_dir, previous_branch)


def gather_repos(org_name, is_org, token=None, refresh=False, dry_run=False,
                 forks=False, destination=None):
    """Handles repository operations for the given organization or user."""
    org = RepoCollection()
    org.set_name(org_name, is_org, token=token)
    logger.info(
        "Collecting {} {} repo(s)"
        .format(org_name, "org" if is_org else "user"))
    if not dry_run:
        org.clone_repos(refresh=refresh, forks=forks, destination=destination)
    return org
