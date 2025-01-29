#!/usr/bin/env python
from __future__ import print_function
import json
import os
import sys
from os.path import expanduser


MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
REPOS_DIR = os.path.dirname(REPO_DIR)
if os.path.isfile(os.path.join(REPOS_DIR, "hierosoft", "hierosoft",
                               "__init__.py")):
    sys.path.insert(0, os.path.join(REPOS_DIR, "hierosoft"))

from hierosoft.logging2 import getLogger  # noqa: E402  #type:ignore

logger = getLogger(__name__)

# ENABLE_SSH = True
config_dir = os.path.join(expanduser("~"), ".config", "repo-organizer")
backup_dir = os.path.join(expanduser("~"), "repo-organizer")
settings_path = os.path.join(config_dir, "settings.json")


def masked(v):
    return "*" * len(v)


def load_settings():
    """Load settings from settings_path
    such as ~/.config/repo-organizer/settings.json.
    """

    if not os.path.exists(settings_path):
        return None

    with open(settings_path, "r") as settings_file:
        settings = json.load(settings_file)

    return settings


def emit_cast(value):
    return "{}({})".format(type(value).__name__, repr(value))