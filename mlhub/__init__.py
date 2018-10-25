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

from mlhub.constants import CMD, DEBUG, VERSION, COMMANDS, OPTIONS

def main():
    """Main program for the command line script."""

    # ------------------------------------
    # COMMAND LINE PARSER
    # ------------------------------------

    # Global option parser

    parent_parser = argparse.ArgumentParser(add_help=False)
    optadder = utils.OptionAdder(parent_parser, OPTIONS)
    optadder.add_alloptions()

    # ------------------------------------
    # We support a basic set of commands and then any model specific
    # commands provided in the archive.
    # ------------------------------------

    parser = argparse.ArgumentParser(
        prog=CMD,
        description="Access models from the ML Hub.",
        parents=[parent_parser],
    )
    subparsers = parser.add_subparsers(
        title='subcommands',
        dest="cmd",
    )
    cmdadder = utils.SubCmdAdder(subparsers, commands, COMMANDS)
    cmdadder.add_allsubcmds()

    # ------------------------------------
    # ACTION
    # ------------------------------------

    pos_args = [(i, arg) for i, arg in enumerate(sys.argv[1:])
                if not arg.startswith('-')]
    ver_args = [(i, arg) for i, arg in enumerate(sys.argv[1:])
                if arg == '-v' or arg == '--version']

    if len(pos_args) != 0 and pos_args[0][1] not in COMMANDS:

        # Model-specific commands

        if len(ver_args) != 0:
            # --------------------------------------------
            # Query the version of the model, for example
            #   $ ml rain -v
            # Otherwise, output the version of ml
            #   $ ml -v rain
            # --------------------------------------------

            model = pos_args[0][1] if ver_args[0][0] > pos_args[0][0] else None
            print(model, utils.get_version(model))
            return 0
 
        model_cmd_parser = argparse.ArgumentParser(
            prog=CMD,
            parents=[parent_parser],
            add_help=False)
        model_cmd_parser.add_argument('cmd', metavar='command')
        model_cmd_parser.add_argument('model')
        args, extra_args = model_cmd_parser.parse_known_args(sys.argv[1:])

        # Simple help message for the model-specific command
        
        if '--help' in extra_args or '-h' in extra_args:
            info = utils.load_description(args.model)
            utils.print_model_cmd_help(info, args.cmd)
            return 0

        setattr(args, 'func', commands.dispatch)
        setattr(args, 'param', extra_args)
    else:

        # Basic common commands
        
        args = parser.parse_args()


    if args.debug:
        constants.debug = True
        print(DEBUG + str(args))

    if args.version:
        print('ml', utils.get_version())
        return 0

    # Ensure we have a trailing slash on the mlhub.

    if args.mlhub is not None: constants.MLHUB = os.path.join(args.mlhub, "")

    if args.cmd is not None: constants.CMD = args.cmd

    if "func" not in args:
        utils.print_usage()
        return 0

    args.func(args)

if __name__ == "__main__":
    main()
