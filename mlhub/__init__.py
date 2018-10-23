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
import argparse
import mlhub.commands as commands
import mlhub.constants as constants
import mlhub.utils as utils

from mlhub.constants import CMD, DEBUG, VERSION, COMMANDS, OPTIONS

def main():
    """Main program for the command line script."""

    # ------------------------------------
    # COMMAND LINE PARSER
    # ------------------------------------

    parser = argparse.ArgumentParser(
        prog=CMD,
        description="Access models from the ML Hub.",
    )

    optadder = utils.OptionAdder(parser, OPTIONS)
    optadder.add_alloptions()

    # ------------------------------------
    # We support a basic set of commands and then any model specific
    # commands provided in the archive.
    # ------------------------------------

    cmd_parser = argparse.ArgumentParser()  # Another parser for subcommand parsing
    subparsers = cmd_parser.add_subparsers(
        title='subcommands',
        dest="cmd",
    )

    cmdadder = utils.SubCmdAdder(subparsers, commands, COMMANDS)
    cmdadder.add_allsubcmds()

    #------------------------------------
    # ACTION
    #------------------------------------

    args, extra_args = parser.parse_known_args()

    if args.version:
        print(VERSION)
        return 0

    # Ensure we have a trainling slash on the mlhub.

    if args.mlhub is not None: mlhub = os.path.join(args.mlhub, "")

    if args.cmd is not None: constants.CMD = args.cmd

    if args.debug:
        constants.debug = True
        print(DEBUG + str(args))
        print(DEBUG + str(extra_args))


    if len(extra_args) > 0:
        if extra_args[0] in COMMANDS:
            cmd_parser.parse_args(extra_args, namespace=args)
        else:
            # Model-specifice commands
            
            setattr(args, 'cmd', extra_args[0])  # command name
            setattr(args, 'model', extra_args[1])  # model name
            setattr(args, 'func', commands.dispatch)  # dispatch model command
            setattr(args, 'param', extra_args[2:])  # parameters of model command


    if not "func" in args:
        utils.print_usage()
        return 0

    args.func(args)

if __name__ == "__main__":
    main()
