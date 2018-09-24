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

import os

#------------------------------------------------------------------------
# The default ML Hub can be overriden by an environment variable or by
# the command line option --mlhub.
#------------------------------------------------------------------------

MLHUB  = "https://mlhub.ai/"
if "MLHUB" in os.environ:
    # The following adds a trainling "/" as assumed in the code.
    MLHUB = os.path.join(os.getenv("MLHUB"), "")

HUB_PATH = "pool/main/"

#------------------------------------------------------------------------
# The MLINIT contains all of the locally installed models.
#------------------------------------------------------------------------

MLINIT = os.path.expanduser("~/.mlhub/")
if "MLINIT" in os.environ:
    # The following adds a trainling "/" as assumed in the code.
    MLINIT = os.path.join(os.getenv("MLINIT"), "")


#------------------------------------------------------------------------
# Application information.
#------------------------------------------------------------------------

APP  = "mlhub"            # The application name.
APPX = "{}: ".format(APP) # For error messages.
CMD  = "ml"               # The command line tool.

EXT_MLM  = ".mlm"         # Archive filename extension
EXT_AIPK = ".aipk"        # Backward compatibility

VERSION = "1.3.6" # DO NOT MODIFY. Managed from ../Makefile.

# Commands

COMMANDS = {
    # -------------------------------------------------------------------
    # 'description': used in the usage by argparse and to genereate next
    #                step suggestion.
    # 'suggestion': Maybe give a better suggestion instead of generating
    #               automatically from 'description'.
    # 'alias': used by argparse.
    # 'func': useed by argparse to dispatch to the actual function.
    # 'next': specify the next possible commands after the command.
    #         There can be groups of next commands for different scenarios,
    #         like the command 'installed'.
    #         Next step order: 'available', 'install', 'readme', 'configure',
    #                          'commands' and commands by the order in the
    #                          model's DESCRIPTION.yaml
    # 'confirm': Maybe used for collecting user's confirmation.
    # 'argument': possible argument for the command used by argparse.

    'available':
        {'description': "List the models available from the ML Hub",
               'alias': ['avail'],
               'usage': "  available            "
                        "List the models available from the repository.",
                'func': "list_available",
                'next': ['install'],
        },

    'installed':
        {'description': "List the locally installed models",
               'usage': "  installed            "
                        "List the models installed locally.",
                'func': "list_installed",
                'next': {'exist': ['configure', 'demo'],
                          'none': ['available', 'install']},
        },

    'clean':
        {'description': "Remove downloaded .mlm archive files",
               'usage': "  clean                "
                        "Remove all (downloaded) {} files from {}.",
             'confirm': "Remove model package archive '{}' [Y/n]? ",
                'func': "remove_mlm",
        },

    'install':
        {'description': "Locally install a model downloaded from a ML Hub",
            'argument': {'model': {}},
               'usage': "  install    <model>   "
                        "Install the named model, local model file or URL.",
                'func': "install_model",
                'next': ['readme'],
        },

    'download':
        {'description': "Download the actual (large) pre-built model",
            'argument': {'model': {}},
                'func': "download_model",
                'next': ['readme'],
        },

    'readme':
        {'description': "Display the model's README information",
            'argument': {'model': {}},
               'usage': "  readme     <model>   "
                        "View the model's README.",
                'func': "readme",
                'next': ['configure'],
        },

    'license':
        {'description': "Display the model's LICENSE information",
            'argument': {'model': {}},
                'func': "license",
        },

    'commands':
        {'description': "List all of the commands supported by the model",
            'argument': {'model': {}},
               'usage': "  commands   <model>   "
                        "List the commands supported by the model.",
                'func': "list_model_commands",
        },

    'configure':
        {'description': "Configure the dependencies required for the model",
            'argument': {'model': {}},
               'usage': "  configure  <model>   "
                        "Configure the model's dependencies.",
                'func': "configure_model",
                'next': ['commands'],
        },

    'remove':
        {'description': "Remove installed model",
            'argument': {'model': {'nargs': "?"}},
               'usage': "  remove    [<model>]  "
                        "Remove a model or remove all models.",
                'func': "remove_model",
                'next': ['installed'],
        },

    'demo':
        {'description': "Run the model's demonstration",
               'alias': ['print', 'display', 'score', 'rebuild'],
            'argument': {'model': {},
                         'param': {'nargs': "*"}},
               'usage': "  demo       <model>   "
                        "Demostrate the model in action.",
                'func': "dispatch",
        },

    'donate':
        {'description': "Consider a donation to the author",
            'argument': {'model': {}},
                'func': "donate",
        },

    'download':
        {'description': "Download the large pre-built model"},

    'print':
        {      'usage': "  print      <model>   "
                        "Technical information about the model."
        },

    'display':
        {      'usage': "  display    <model>   "
                        "Visual presentaiton of the model."
        },
}

USAGE = """Usage: {{}} [<options>] <command> [<command options>] [<model>]

Access machine learning models from the ML Hub.

Global commands:

{commands[available][usage]}
{commands[installed][usage]}
{commands[clean][usage]}

{commands[install][usage]}
{commands[readme][usage]}
{commands[commands][usage]}
{commands[configure][usage]}
{commands[demo][usage]}
{commands[print][usage]}
{commands[display][usage]}
{commands[remove][usage]}

The ML Hub repository is '{{}}'.

Models are installed into '{{}}'.

This is version {{}} of {{}}.

List the available models from the repository with:

  $ ml available
""".format(commands=COMMANDS)

# Filenames.

README    = "README.txt"

DESC_YAML = "DESCRIPTION.yaml"
META_YAML = "Packages.yaml"

DESC_YML = "DESCRIPTION.yml"
META_YML = "Packages.yml"

# Debugging

debug = False
DEBUG = "--> " + APP + ": debug: "
