#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import json
import logging
from os.path import expanduser, exists, join
import requests  # Assuming the `requests` library is installed

# Global constant
ENABLE_SSH = True

# Ensure configuration directory exists
config_dir = expanduser("~/.config/repo-organizer")
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

# Setup logging
logging.basicConfig(level=logging.INFO)

class RepoCollection:
    def __init__(self):
        self.repos = None
        self.name = None
        self.is_org = None

    def set_name(self, name, is_org):
        """Sets the name and type (organization or user)."""
        self.name = name
        self.is_org = is_org

    def load_repos(self, refresh=False):
        """Loads repositories from GitHub or from cache."""
        repo_cache = join(config_dir, self.name, 'repos.json')
        downloaded = False

        if not refresh:
            if os.path.exists(repo_cache):
                with open(repo_cache, 'r') as cache_file:
                    self.repos = json.load(cache_file)
                    return
            else:
                logging.warning("No %s, so downloading from GitHub", repo_cache)

        # Construct URL based on whether it's an organization or user
        url = 'https://api.github.com/%s/%s/repos' % (
            'orgs' if self.is_org else 'users', self.name
        )
        response = requests.get(url)

        if response.status_code == 200:
            self.repos = response.json()
            downloaded = True
        else:
            logging.error("Failed to fetch repositories from GitHub: %s", url)
            return

        if downloaded:
            # Save downloaded data to cache
            if not os.path.exists(join(config_dir, self.name)):
                os.makedirs(join(config_dir, self.name))

            with open(repo_cache, 'w') as cache_file:
                json.dump(self.repos, cache_file)

    def log_error(self, message):
        """Appends errors to the error log."""
        with open(expanduser("~/.config/repo-organizer/errors.log"), 'a') as error_log:
            error_log.write(message + '\n')

    def log_success(self, message):
        """Appends success messages to the success log."""
        with open(expanduser("~/.config/repo-organizer/repo-organizer.log"), 'a') as success_log:
            success_log.write(message + '\n')

    def load_repos(self, repos_path):
        """Clones or updates repositories."""
        for repo in self.repos:
            repo_name = repo['name']
            if ENABLE_SSH:
                clone_url = "git@github.com:%s/%s.git" % (self.name, repo_name)
            else:
                clone_url = repo['clone_url']

            repo_dir = join(repos_path, 'mirror-' + self.name, repo_name)

            if not exists(repo_dir):
                cmd = "git clone %s %s" % (clone_url, repo_dir)
                result = os.system(cmd)
                if result != 0:
                    self.log_error("Failed to clone %s" % clone_url)
                else:
                    self.log_success(cmd)
            else:
                cmd = "cd %s && git pull" % repo_dir
                result = os.system(cmd)
                if result != 0:
                    self.log_error("Failed to pull in %s" % repo_dir)
                else:
                    self.log_success(cmd)

def gather_repos(name, is_org):
    """Find the repository path and gather repositories for the given name."""
    repos_path = None

    # Try to find repos_path
    try_paths = [r"C:\Projects", "~/git", "~/GitHub", "~/Documents/GitHub"]
    for path in try_paths:
        path = expanduser(path)
        if exists(join(path, "mirror-" + name)):
            repos_path = path
            break

    if not repos_path:
        logging.error("No repos dir was found, so for safety nothing was done. "
                      "Create mirror-%s folder in one of the following first: %s",
                      name, try_paths)
        return 1

    org = RepoCollection()
    org.set_name(name, is_org)
    org.load_repos(repos_path)

    return 0

def load_settings():
    """Load settings from the settings.json file."""
    settings_file = join(config_dir, "settings.json")
    if not exists(settings_file):
        logging.error("Missing settings file: %s", settings_file)
        return None

    with open(settings_file, 'r') as file:
        try:
            settings = json.load(file)
        except ValueError as e:
            logging.error("Error parsing settings file: %s", e)
            return None

    # Validate the structure of the settings file
    sources = settings.get('sources')
    if sources is None:
        logging.error("'sources' key is missing in settings file.")
        return None

    github = sources.get('github')
    if github is None:
        logging.error("'github' key is missing under 'sources' in settings file.")
        return None

    orgs = github.get('orgs')
    users = github.get('users')

    if not orgs and not users:
        logging.error("Both 'orgs' and 'users' are missing or invalid in settings file.")
        return None

    return settings

def main():
    """Main function."""
    settings = load_settings()
    if settings is None:
        return 1

    github = settings['sources']['github']

    # Process organizations
    orgs = github.get('orgs')
    if orgs:
        for org_name in orgs:
            gather_repos(org_name, True)

    # Process users
    users = github.get('users')
    if users:
        for user_name in users:
            gather_repos(user_name, False)

    return 0

if __name__ == "__main__":
    sys.exit(main())
