#!/usr/bin/python3
#
# mlhub - Machine Learning Model Repository
#
# A command line tool for managing machine learning models.
#
# Copyright 2018 (c) Graham.Williams@togaware.com All rights reserved.
#
# This file is part of mlhub.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the ""Software""), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import collections
import logging
import os

# ------------------------------------------------------------------------
# The default ML Hub can be overridden by an environment variable or by
# the command line option --mlhub.
# ------------------------------------------------------------------------

MLHUB = "https://mlhub.ai/"
if "MLHUB" in os.environ:
    # The following adds a trailing "/" as assumed in the code.
    MLHUB = os.path.join(os.getenv("MLHUB"), "")

HUB_PATH = "pool/main/"

# ------------------------------------------------------------------------
# The MLINIT contains all of the locally installed models and configuration
# files.
# ------------------------------------------------------------------------

MLINIT = os.path.expanduser("~/.mlhub/")
if "MLINIT" in os.environ:
    # The following adds a trailing "/" as assumed in the code.
    MLINIT = os.path.join(os.getenv("MLINIT"), "")

# Cache files for bash completion.

COMPLETION_DIR = os.path.join(MLINIT, ".completion")
COMPLETION_COMMANDS = os.path.join(COMPLETION_DIR, "commands")
COMPLETION_MODELS = os.path.join(COMPLETION_DIR, "models")

COMPLETION_SCRIPT = os.path.join("bash_completion.d", "ml.bash")

# Log files

LOG_DIR = os.path.join(MLINIT, ".log")
LOG_FILE = os.path.join(LOG_DIR, "mlhub.log")

# model package cache, archive and config dir

CACHE_DIR = os.path.join(MLINIT, ".cache")
ARCHIVE_DIR = os.path.join(MLINIT, ".archive")
CONFIG_DIR = os.path.join(MLINIT, ".config")
CONFIG_FILE = "config.yaml"

# ------------------------------------------------------------------------
# Application information.
# ------------------------------------------------------------------------

APP = "mlhub"  # The application name.
APPX = "{}: ".format(APP)  # For error messages.
CMD = "ml"  # The command line tool.

EXT_MLM = ".mlm"  # Archive filename extension
EXT_AIPK = ".aipk"  # Backward compatibility

VERSION = "3.7.2"  # DO NOT MODIFY. Managed from ../Makefile.

OPTIONS = {
    # Global command line options
    #
    # All the keys in dict correspond to the keyword arguments of
    # 'argparse.ArgumentParser.add_argument()'.
    "--version": {
        "alias": ["-v"],
        "help": "display version information of ml or a package and exit.",
        "action": "store_true",
    },
    "--debug": {"help": "display debug information.", "action": "store_true"},
    "--quiet": {
        "alias": ["-q"],
        "help": "reduce noise.",
        "action": "store_true",
    },
    "--init-dir": {
        "help": "use this as the init dir instead of '{}'.".format(MLINIT)
    },
    "--mlhub": {"help": "use this ML Hub instead of '{}'.".format(MLHUB)},
    "--cmd": {
        "help": "command display name instead of '{}'.".format(CMD),
        "dest": "mlmetavar",
    },
    "--working-dir": {
        "alias": ["--wd"],
        "help": "use this as the working dir instead of '{}'/<model>.".format(
            MLINIT
        ),
    },
}

# Basic common commands

COMMANDS = {
    # -------------------------------------------------------------------
    # 'description': used in the usage by argparse and to generate next
    #                step suggestion.
    # 'suggestion': Maybe give a better suggestion instead of generating
    #               automatically from 'description'.
    # 'alias': used by argparse.
    # 'func': used by argparse to dispatch to the actual function.
    # 'next': specify the next possible commands after the command.
    #         There can be groups of next commands for different scenarios,
    #         like the command 'installed'.
    #         Next step order: 'available', 'install', 'readme', 'configure',
    #                          'commands' and commands by the order in the
    #                          model's DESCRIPTION.yaml
    # 'confirm': Maybe used for collecting user's confirmation.
    # 'argument': possible argument for the command used by argparse.
    "available": {
        "description": "list the models available from the ML Hub repository",
        "argument": {
            "--name-only": {
                "help": "list only the names",
                "action": "store_true",
            },
        },
        "usage": "  available            list the models available from the ML Hub repository",
        "func": "list_available",
        "next": ["install"],
    },
    "installed": {
        "description": "list the locally installed models",
        "argument": {
            "--name-only": {
                "help": "list only the names",
                "action": "store_true",
            },
        },
        "usage": "  installed            list the locally installed models",
        "func": "list_installed",
        "next": {
            "exist": ["configure", "readme", "commands"],
            "none": ["available", "install"],
        },
    },
    "clean": {
        "description": "remove downloaded model package files",
        "usage": "  clean                remove downloaded model package files",
        "confirm": "remove model package archive '{}' [Y/n]? ",
        "func": "remove_mlm",
    },
    "install": {
        "description": "install a named model, local model file or URL",
        "argument": {"model": {}, "-i": {"help": "SSH key path"}},
        "usage": "  install    <model>   install a named model, local model file or URL",
        "func": "install_model",
        "next": ["configure"],
    },
    # 'download': {
    #     'description': "download the actual (often large) pre-built model",
    #     'argument': {'model': {}},
    #     'func': "download_model",
    #     'next': ['readme'],
    # },
    "readme": {
        "description": "view the model's README",
        "argument": {"model": {}},
        "usage": "  readme     <model>   view the model's README",
        "func": "readme",
        "next": ["commands"],
    },
    # 'license': {
    #     'description': "display the model's LICENSE information",
    #     'argument': {'model': {}},
    #     'func': "license",
    # },
    "commands": {
        "description": "list the commands supported by the model package",
        "argument": {
            "model": {},
            "--name-only": {"help": "list names only", "action": "store_true"},
        },
        "usage": "  commands   <model>   list the commands supported by the model package",
        "func": "list_model_commands",
    },
    "configure": {
        "description": "configure the package",
        "argument": {
            "model": {"nargs": "?"},
            "-y": {"action": "store_true", "help": 'the same as "--yes"'},
            "--yes": {
                "action": "store_true",
                "help": 'assume "yes" as answer to all prompts',
            },
            "-i": {"help": "SSH key path"},
        },
        "usage": "  configure [<model>]  configure ml or the model's dependencies",
        "func": "configure_model",
        "next": ["readme"],
    },
    "uninstall": {
        "description": "uninstall a model or all models",
        "argument": {"model": {"nargs": "?"}},
        "usage": "  uninstall    [<model>]  uninstall a model or all models",
        "func": "remove_model",
        "next": ["installed", "install"],
    },
    # 'demo': {
    #     'description': "run the model's demonstration",
    #     'alias': ['print', 'display', 'score', 'rebuild'],
    #     'argument': {
    #         'model': {},
    #         'param': {'nargs': "*"}
    #     },
    #     'usage': "  demo       <model>   demonstrate the model in action",
    #     'func': "dispatch",
    # },
    # 'donate': {
    #     'description': "consider a donation to the author.",
    #     'argument': {'model': {}},
    #     'func': "donate",
    # },
}

COMMANDS_USAGE = collections.OrderedDict()
for cmd in collections.OrderedDict(COMMANDS):
    argname = ""
    if "argument" in COMMANDS[cmd]:
        for k, v in COMMANDS[cmd]["argument"].items():
            if not k.startswith("-"):
                argname = "<" + k + ">"
                if "nargs" in v and v["nargs"] == "?":
                    argname = "[" + argname + "]"
                break
    usage = "  {:10s}{:^9s}  {}".format(
        cmd, argname, COMMANDS[cmd]["description"]
    )
    COMMANDS_USAGE[cmd] = usage

USAGE = """Usage: {{}} [<options>] <command> [<command options>] [<model>]

Access machine learning models from the ML Hub.

Global commands:

{}

{}

The ML Hub repository is '{{}}'.

Models are installed into '{{}}'.

This is version {{}} of {{}}.

To ensure the pre-requisites are installed and for a better experience
with tab completion the sys admin can run the command:

  $ ml configure

The user can then run the following for tab completion:

  $ source /etc/bash_completion.d/ml.bash

List the available models from the repository with:

  $ ml available
""".format(
    "\n".join(list(COMMANDS_USAGE.values())[:3]),
    "\n".join(list(COMMANDS_USAGE.values())[3:]),
)

# ------------------------------------------------------------------------
# File names
# ------------------------------------------------------------------------

README = "README.txt"

MLHUB_YAML = "MLHUB.yaml"

DESC_YAML = "DESCRIPTION.yaml"
META_YAML = "Packages.yaml"

DESC_YML = "DESCRIPTION.yml"
META_YML = "Packages.yml"

# ------------------------------------------------------------------------
# Debugging
# ------------------------------------------------------------------------

LOG_FILE_LEVEL = logging.DEBUG
LOG_FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
LOG_CONSOLE_FORMAT = "--> %(name)s - %(levelname)s: %(message)s"
LOG_NOT_QUIET = {"quiet": False}
LOG_QUIET = {"quiet": True}

# ------------------------------------------------------------------------
# Model package config entry keys
# ------------------------------------------------------------------------

CONDA_ENV_NAME = "conda_env_name"  # Conda environment name
WORKING_DIR = "working_dir"  # Model's working dir
PYTHON_PATH = "python_path"  # python path, such as /usr/bin/python3
PIP_PATH = "pip_path"  # pip path, such as /usr/bin/pip3
SYS_PYTHON_PKG_USAGE = (
    "sys_python_pkg_usage"  # Whether system python packages installed
)


# ------------------------------------------------------------------------
# Command binary
# ------------------------------------------------------------------------

BASH_CMD = "/bin/bash"

R_CMD = "/usr/bin/R"
RSCRIPT_CMD = "/usr/bin/Rscript"

SYS_PYTHON_CMD = "/usr/bin/python3"
SYS_PIP_CMD = "/usr/bin/pip3"


# ------------------------------------------------------------------------
# Messages
# ------------------------------------------------------------------------

MSG_INCOMPATIBLE_PYTHON_ENV = """
WARNING: MLHub is not installed in system's site package directory!
The "{}" MLHub package requires system Python packages, which may not correctly
be included in the its Python search path.
To solve this problem, please make sure to install MLHub using:
    $ pip uninstall -y mlhub  # or $ pip3 uninstall -y mlhub
    $ sudo apt-get install -y python3-pip
    $ /usr/bin/pip3 install mlhub
followed by re-login.
Or for advanced users, you could manually `pip install` those required Python
packages.
"""
