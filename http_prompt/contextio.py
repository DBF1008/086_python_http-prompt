"""Serialization and deserialization of a Context object."""

import io
import os

from . import xdg
from .context.transform import format_to_http_prompt
from .execution import execute


# Don't save these HTTPie options to avoid collision with user config file
EXCLUDED_OPTIONS = ['--style']

# Filename the current environment context will be saved to
CONTEXT_FILENAME = 'context.hp'

# Subdirectory name for named profiles
PROFILES_DIR = 'profiles'


def _get_context_filepath():
    dir_path = xdg.get_data_dir()
    return os.path.join(dir_path, CONTEXT_FILENAME)


def _get_profiles_dir():
    return xdg.get_data_dir(resource_name=PROFILES_DIR)


def _get_profile_filepath(name):
    profiles_dir = _get_profiles_dir()
    return os.path.join(profiles_dir, name + '.hp')


def load_context(context, file_path=None):
    """Load a Context object in place from user data directory."""
    if not file_path:
        file_path = _get_context_filepath()
    if os.path.exists(file_path):
        with open(file_path, encoding='utf-8') as f:
            for line in f:
                execute(line, context)


def save_context(context):
    """Save a Context object to user data directory or profile file."""
    if context.profile_name:
        file_path = _get_profile_filepath(context.profile_name)
    else:
        file_path = _get_context_filepath()
    content = format_to_http_prompt(context, excluded_options=EXCLUDED_OPTIONS)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def list_profiles():
    """Return a sorted list of saved profile names."""
    profiles_dir = _get_profiles_dir()
    if not os.path.isdir(profiles_dir):
        return []
    names = []
    for filename in os.listdir(profiles_dir):
        if filename.endswith('.hp'):
            names.append(filename[:-3])
    return sorted(names)


def delete_profile(name):
    """Delete a saved profile. Returns True if deleted, False if not found."""
    filepath = _get_profile_filepath(name)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


def profile_exists(name):
    """Check if a named profile exists."""
    return os.path.exists(_get_profile_filepath(name))
