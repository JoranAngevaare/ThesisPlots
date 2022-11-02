import os
import socket
import sys
import typing as ty
from collections import defaultdict
from importlib import import_module
from platform import python_version

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from git import Repo, InvalidGitRepositoryError
from cycler import cycler
import json
from base64 import b32encode
from hashlib import sha1
from collections.abc import Mapping


root_folder = os.path.join(os.path.split(os.path.realpath(__file__))[0], '..')


def setup_plt(use_tex=True):
    """Change the plots to have my style and fashion"""
    params = {'axes.grid': False,
              #           'font.size': 16,
              #           'axes.titlesize': 22,
              #           'axes.labelsize': 18,
              #           'axes.linewidth': 2,
              #           'xtick.labelsize': 16,
              #           'ytick.labelsize': 16,
              'font.size': 20,
              'axes.titlesize': 22,
              'axes.labelsize': 20,
              'axes.linewidth': 2,
              'xtick.labelsize': 20,
              'ytick.labelsize': 20,
              'ytick.major.size': 8,
              'ytick.minor.size': 4,
              'xtick.major.size': 8,
              'xtick.minor.size': 4,
              'xtick.major.width': 2,
              'xtick.minor.width': 2,
              'ytick.major.width': 2,
              'ytick.minor.width': 2,
              'xtick.direction': 'in',
              'ytick.direction': 'in',
              'legend.fontsize': 20,
              'figure.facecolor': 'w',
              'figure.figsize': (10, 8),
              'image.cmap': 'viridis',
              'lines.linewidth': 2,
              }
    plt.rcParams.update(params)
    # from https://github.com/XENONnT/nton/blob/d5d71b2798d74b9632a8846eb2e0f19ab0d1f563/nton/mplconfigs/stylelib/xenonnt.mplstyle
    custom_cycler = (
            cycler(
                color=[f'#{c}' for c in
                       ['000000', '0052FF', 'FF2A2A', '4AC124', 'F7BF24', '00CFFF', 'FF6AFF', 'A54040']]
            ) +
            cycler(marker=['o', 's', 'v', '^', 'D', 'P', '>', 'x']))

    plt.rcParams.update({'axes.prop_cycle': custom_cycler})
    if use_tex and not os.environ.get('DISABLE_LATEX', False):
        # Allow latex to be disabled from the environment coverage see #30
        matplotlib.rc('text', usetex=True)


def save_fig(name,
             file_types=('png', 'pdf'),
             **kwargs):
    """Save a figure in the figures dir"""
    kwargs.setdefault('dpi', 150)
    kwargs.setdefault('bbox_inches', "tight")
    for file_type in file_types:
        path = os.path.join(root_folder, 'figures', f'{name}.{file_type}')
        plt.savefig(path, **kwargs)


def print_versions(
        modules=('thesis_plots',),
        print_output=True,
        include_python=True,
        return_string=False,
        include_git=True
):
    """
    Print versions of modules installed.

    :param modules: Modules to print, should be str, tuple or list. E.g.
        print_versions(modules=('numpy', 'thesis_plots',))
    :param return_string: optional. Instead of printing the message,
        return a string
    :param include_git: Include the current branch and latest
        commit hash
    :return: optional, the message that would have been printed
    """
    versions = defaultdict(list)
    if include_python:
        versions['module'] = ['python']
        versions['version'] = [python_version()]
        versions['path'] = [sys.executable]
        versions['git'] = [None]
    for m in to_str_tuple(modules):
        result = _version_info_for_module(m, include_git=include_git)
        if result is None: continue
        version, path, git_info = result
        versions['module'].append(m)
        versions['version'].append(version)
        versions['path'].append(path)
        versions['git'].append(git_info)
    df = pd.DataFrame(versions)
    info = f'Host {socket.getfqdn()}\n{df.to_string(index=False)}'
    if print_output:
        print(info)
    return info if return_string else df


def _version_info_for_module(module_name, include_git):
    try:
        mod = import_module(module_name)
    except ImportError:
        print(f'{module_name} is not installed')
        return
    git = None
    version = mod.__dict__.get('__version__', None)
    module_path = mod.__dict__.get('__path__', [None])[0]
    if include_git:
        try:
            repo = Repo(module_path, search_parent_directories=True)
        except InvalidGitRepositoryError:
            # not a git repo
            pass
        else:
            try:
                branch = repo.active_branch
            except TypeError:
                branch = 'unknown'
            try:
                commit_hash = repo.head.object.hexsha
            except TypeError:
                commit_hash = 'unknown'
            git = f'branch:{branch} | {commit_hash[:7]}'
    return version, module_path, git


def to_str_tuple(x: ty.Union[str, bytes, list, tuple, pd.Series, np.ndarray]) -> ty.Tuple[str]:
    """
    Convert any sensible instance to a tuple of strings
    stolen from
    https://github.com/AxFoundation/strax/blob/d3608efc77acd52e1d5a208c3092b6b45b27a6e2/strax/utils.py#242
    """
    if isinstance(x, (str, bytes)):
        return x,
    if isinstance(x, list):
        return tuple(x)
    if isinstance(x, tuple):
        return x
    raise TypeError(f"Expected string or tuple of strings, got {type(x)}")


def string_to_mathrm(string):
    """wrap a string in mathrm mode for latex labels"""
    string = string.replace(' ', '\ ')
    return f'$\mathrm{{{string}}}$'


def hashablize(obj):
    """Convert a container hierarchy into one that can be hashed.
    See http://stackoverflow.com/questions/985294

    Copied from https://github.com/AxFoundation/strax/blob/master/strax/utils.py
    """
    if isinstance(obj, Mapping):
        # Convert immutabledict etc for json decoding
        obj = dict(obj)
    try:
        hash(obj)
    except TypeError:
        if isinstance(obj, dict):
            return tuple((k, hashablize(v)) for (k, v) in sorted(obj.items()))
        elif hasattr(obj, '__iter__'):
            return tuple(hashablize(o) for o in obj)
        else:
            raise TypeError("Can't hashablize object of type %r" % type(obj))
    else:
        return obj

def deterministic_hash(thing, length=6):
    """Return a base32 lowercase string of length determined from hashing
    a container hierarchy
    Copied from https://github.com/AxFoundation/strax/blob/master/strax/utils.py
    """
    hashable = hashablize(thing)
    jsonned = json.dumps(hashable, cls=json.JSONEncoder)
    # disable bandit
    digest = sha1(jsonned.encode('ascii')).digest()
    return b32encode(digest)[:length].decode('ascii').lower()
