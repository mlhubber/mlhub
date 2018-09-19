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

    utils.add_subcommand(subparsers, 'available', commands)

    #------------------------------------
    # INSTALLED
    #------------------------------------

    utils.add_subcommand(subparsers, 'installed', commands)

    #------------------------------------
    # CLEAN
    #------------------------------------

    utils.add_subcommand(subparsers, 'clean', commands)

    #------------------------------------
    # INSTALL
    #------------------------------------

    utils.add_subcommand(subparsers, 'install', commands)

    #------------------------------------
    # DOWNLOAD
    #------------------------------------

    utils.add_subcommand(subparsers, 'download', commands)

    #------------------------------------
    # README
    #------------------------------------

    utils.add_subcommand(subparsers, 'readme', commands)

    #------------------------------------
    # LICENSE
    #------------------------------------

    utils.add_subcommand(subparsers, 'license', commands)

    #------------------------------------
    # COMMANDS
    #------------------------------------

    utils.add_subcommand(subparsers, 'commands', commands)

    #------------------------------------
    # CONFIGURE
    #------------------------------------

    utils.add_subcommand(subparsers, 'configure', commands)

    #------------------------------------
    # REMOVE
    #------------------------------------

    utils.add_subcommand(subparsers, 'remove', commands)

    #------------------------------------
    # MODEL SPECIFIC COMMANDS
    #
    # Need to make this general or dynamic
    # based on the comannds available
    # from the locally installed models?
    #------------------------------------

    utils.add_subcommand(subparsers, 'demo', commands)

    #------------------------------------
    # DONATE
    #------------------------------------

    utils.add_subcommand(subparsers, 'donate', commands)

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
