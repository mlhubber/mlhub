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
import sys
import argparse
import mlhub.commands as commands
import mlhub.constants as constants
import mlhub.utils as utils

from mlhub.constants import CMD, USAGE, DEBUG, MLINIT, MLHUB

def main():
    """Main program for the command line script."""

    #------------------------------------
    # COMMAND LINE PARSER
    #------------------------------------
    
    parser = argparse.ArgumentParser(
        prog=CMD,
        description="Access models from the ML Hub.",
    )

    #------------------------------------
    # --DEBUG
    #------------------------------------

    parser.add_argument('--debug',  action='store_true', help="Display debug information.")
    
    #------------------------------------
    # --QUIET

    parser.add_argument('--quiet',  action='store_true', help="Reduce noise.")
    
    #------------------------------------
    # --INIT-DIR
    #------------------------------------

    parser.add_argument('--init-dir', help="Use this as the init dir instead of '{}'.".format(MLINIT))

    #------------------------------------
    # --MLHUB
    #------------------------------------

    parser.add_argument('--mlhub', help="Use this ML Hub instead of '{}'.".format(MLHUB))

    #------------------------------------
    # --CMD
    #------------------------------------

    parser.add_argument('--cmd', help="Command display name instead of '{}'.".format(CMD))

    #------------------------------------
    # We support a basic set of commands
    # and then any model specific
    # commands provided in the archive.
    #------------------------------------

    subparsers = parser.add_subparsers(
        title='subcommands',
        dest="cmd",
    )

    #------------------------------------
    # AVAILABLE
    #------------------------------------
    
    parser_available = subparsers.add_parser(
        "available",
        aliases=['avail'],
        description="List the models available from the ML Hub",
    )
    parser_available.set_defaults(func=commands.list_available)

    #------------------------------------
    # INSTALLED
    #------------------------------------
    
    parser_installed = subparsers.add_parser(
        "installed",
        description="List the locally installed models",
    )
    parser_installed.set_defaults(func=commands.list_installed)

    #------------------------------------
    # CLEAN
    #------------------------------------
    
    parser_clean = subparsers.add_parser(
        "clean",
        description="Remove downloaded .mlm archive files",
    )
    parser_clean.set_defaults(func=commands.remove_mlm)

    #------------------------------------
    # INSTALL
    #------------------------------------
    
    parser_install = subparsers.add_parser(
        "install",
        description="Locally install a model downloaded from a ML Hub",
    )
    parser_install.add_argument("model")
    parser_install.set_defaults(func=commands.install_model)

    #------------------------------------
    # DOWNLOAD
    #------------------------------------
    
    parser_download = subparsers.add_parser(
        "download",
        description="Download the actual (large) pre-built model",
    )
    parser_download.add_argument("model")
    parser_download.set_defaults(func=commands.download_model)

    #------------------------------------
    # README
    #------------------------------------
    
    parser_readme = subparsers.add_parser(
        "readme",
        description="Display the model's README information",
    )
    parser_readme.add_argument("model")
    parser_readme.set_defaults(func=commands.readme)

    #------------------------------------
    # LICENSE
    #------------------------------------
    
    parser_license = subparsers.add_parser(
        "license",
        description="Display the model's LICENSE information",
    )
    parser_license.add_argument("model")
    parser_license.set_defaults(func=commands.license)

    #------------------------------------
    # COMMANDS
    #------------------------------------
    
    parser_cmds = subparsers.add_parser(
        "commands",
        description="List all of the commands supported by the model",
    )
    parser_cmds.add_argument("model")
    parser_cmds.set_defaults(func=commands.list_model_commands)

    #------------------------------------
    # CONFIGURE
    #------------------------------------
    
    parser_configure = subparsers.add_parser(
        "configure",
        description="Configure the dependencies required for the model",
    )
    parser_configure.add_argument("model")
    parser_configure.set_defaults(func=commands.configure_model)

    #------------------------------------
    # MODEL SPECIFIC COMMANDS
    #
    # Need to make this general or dynamic
    # based on the comannds available
    # from the locally installed models?
    #------------------------------------

    parser_cmd = subparsers.add_parser(
        "demo",
        aliases = ['print', 'display', 'score', 'rebuild'],
        description="Model commands",
    )
    parser_cmd.add_argument("model")
    parser_cmd.add_argument("param", nargs="*")
    parser_cmd.set_defaults(func=commands.dispatch)

    #------------------------------------
    # DONATE
    #------------------------------------
    
    parser_donate = subparsers.add_parser(
        "donate",
        description="Consider a donation to the author",
    )
    parser_donate.add_argument("model")
    parser_donate.set_defaults(func=commands.donate)

    #------------------------------------
    # ACTION
    #------------------------------------

    sys.argv.pop(0)
    args = parser.parse_args(sys.argv)

    # Ensure we have a trainling slash on the mlhub.
    
    if args.mlhub is not None: mlhub = os.path.join(args.mlhub, "")

    if args.cmd is not None: constants.CMD = args.cmd

    if args.debug:
        constants.debug = True
        print(DEBUG + str(args))
    
    if not "func" in args:
        utils.print_usage()
        return 0
    
    args.func(args)

if __name__ == "__main__":
    main()
