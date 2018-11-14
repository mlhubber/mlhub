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
import logging
import argparse
import mlhub.commands as commands
import mlhub.constants as constants
import mlhub.utils as utils

from mlhub.constants import (
    CMD,
    APP,
    VERSION,
    COMMANDS,
    OPTIONS,
)

# ----------------------------------------------------------------------
# Set up log.
# ----------------------------------------------------------------------

# Initialize log dir.  Ensure it exists.

utils.create_log_dir()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add file log handler to log all into a file

utils.add_log_handler(
    logger,
    logging.FileHandler(constants.LOG_FILE),
    constants.LOG_FILE_LEVEL,
    constants.LOG_FILE_FORMAT)

logger.info('---------- Start logging ----------')
# ----------------------------------------------------------------------
# Set up command line parser and dispatch commands.
# ----------------------------------------------------------------------


def main():
    """Main program for the command line script."""

    logger = logging.getLogger(__name__)

    # --------------------------------------------------
    # COMMAND LINE PARSER
    # --------------------------------------------------

    # Global option parser.  See mlhub.constants.OPTIONS

    logger.info("Create global option parser.")
    global_option_parser = argparse.ArgumentParser(add_help=False)  # Use custom help message
    utils.OptionAdder(global_option_parser, OPTIONS).add_alloptions()

    # --------------------------------------------------
    # We support a basic set of commands and then any model specific
    # commands provided in the archive.  See mlhub.constants.COMMANDS
    # --------------------------------------------------

    logger.info("Create basic commands parser.")
    basic_cmd_parser = argparse.ArgumentParser(
        prog=CMD,
        description="Access models from the ML Hub.",
        parents=[global_option_parser])
    subparsers = basic_cmd_parser.add_subparsers(
        title='subcommands',
        dest="cmd")
    utils.SubCmdAdder(subparsers, commands, COMMANDS).add_allsubcmds()

    # --------------------------------------------------
    # Parse version
    # --------------------------------------------------

    logger.info("Parse global options.")
    args, extra_args = global_option_parser.parse_known_args(sys.argv[1:])

    if args.debug:  # Add console log handler to log debug message to console
        logger.info('Enable printing out debug log on console.')
        utils.add_log_handler(
            logger,
            logging.StreamHandler(),
            logging.DEBUG,
            constants.LOG_CONSOLE_FORMAT)

    logger.debug('args: {}, extra_args: {}'.format(args, extra_args))

    # Get the first positional argument.

    pos_args = [arg for i, arg in enumerate(extra_args) if not arg.startswith('-')]
    first_pos_arg = pos_args[0] if len(pos_args) != 0 else None
    logger.debug('First positional argument: {}'.format(first_pos_arg))

    if args.version:
        logger.info('Query version.')

        # --------------------------------------------------
        # Query the version of the model, for example
        #   $ ml rain -v
        # Otherwise, output the version of ml
        #   $ ml -v rain
        # --------------------------------------------------

        first_pos_arg_index = [i for i, x in enumerate(sys.argv[1:]) if x == first_pos_arg]

        # Optional version args

        ver_args = [(i, arg) for i, arg in enumerate(sys.argv[1:])
                    if arg == '-v' or arg == '--version']

        if first_pos_arg is not None and first_pos_arg_index[0] < ver_args[0][0]:  # model version
            model = first_pos_arg
            print(model, "version", utils.get_version(model))
        else:  # mlhub version
            print(APP, "version", utils.get_version())

        return 0

    # --------------------------------------------------
    # Parse command line args for basic commands or model specific commands
    # --------------------------------------------------

    if first_pos_arg is not None and first_pos_arg not in COMMANDS:

        logger.info("Parse model specific dommands.")
        model_cmd_parser = argparse.ArgumentParser(
            prog=CMD,
            parents=[global_option_parser],
            add_help=False)  # Use custom help message
        model_cmd_parser.add_argument('cmd', metavar='command')
        model_cmd_parser.add_argument('model')
        args, extra_args = model_cmd_parser.parse_known_args(sys.argv[1:])
        logger.debug("args: {}".format(args))
        logger.debug("extra_args: {}".format(extra_args))

        # Simple help message for the model-specific command

        if '--help' in extra_args or '-h' in extra_args:
            info = utils.load_description(args.model)
            utils.print_model_cmd_help(info, args.cmd)
            return 0

        setattr(args, 'func', commands.dispatch)
        setattr(args, 'param', extra_args)
    else:

        logger.info("Parse basic common commands.")
        args = basic_cmd_parser.parse_args()
        logger.debug("args: {}".format(args))

    # Print usage for incorrect argument

    if "func" not in args:
        utils.print_usage()
        return 0

    # Ensure we have a trailing slash on the mlhub.

    if args.mlhub is not None:
        constants.MLHUB = os.path.join(args.mlhub, "")

    if args.mlmetavar is not None:
        constants.CMD = args.mlmetavar

    # --------------------------------------------------
    # Dispatch commands
    # --------------------------------------------------

    try:

        args.func(args)

    except utils.MLInitCreateException as e:
        msg = "The below '{}' init folder cannot be created:\n  {}"
        utils.print_error_exit(msg, APP, e.args[0])

    except utils.MalformedMLMFileNameException as e:
        msg = "Malformed {} file:\n  {}"
        utils.print_error_exit(msg, constants.EXT_MLM, e.args[0])

    except utils.ModelURLAccessException as e:
        msg = "URL access failed:\n  {}"
        utils.print_error_exit(msg, e.args[0])

    except utils.RepoAccessException as e:
        utils.print_error("Cannot access the ML Hub repository:\n  {}", e.args[0])
        if not args.quiet:  # Suggest check if any models installed, since mlhub repo not accessible
            utils.print_commands_suggestions_on_stderr('installed')
        sys.exit(1)

    except utils.ModelNotFoundOnRepoException as e:
        msg = "No model named '{}' was found on\n  {}"
        utils.print_error(msg, e.args[0], e.args[1])
        if not args.quiet:  # Suggest check if any models available, since specified model not found
            utils.print_commands_suggestions_on_stderr('available')
        sys.exit(1)

    except utils.ModelDownloadHaltException as e:
        msg = "URL - '{}' failed:\n  {}".format(e.args[0], e.args[1])
        utils.print_error_exit(msg)

    except utils.DescriptionYAMLNotFoundException as e:
        msg = "No '{}' found for '{}'.  The model package may be broken!"
        utils.print_error(msg, constants.DESC_YAML, e.args[0])
        if not args.quiet:  # Suggest remove broken package or install new model
            utils.print_commands_suggestions_on_stderr('remove', 'install')
        sys.exit(1)

    except utils.ModelNotInstalledException as e:
        msg = "model '{}' is not installed ({})."
        utils.print_error(msg, e.args[0], constants.MLINIT)
        if not args.quiet:  # Suggest install model package or check if any available
            utils.print_commands_suggestions_on_stderr('installed', 'available', 'install')
        sys.exit(1)

    except utils.ModelReadmeNotFoundException as e:
        msg = "The '{}' model does not have a '{}' file:\n  {}\n"
        utils.print_error(msg, e.args[0], constants.README, e.args[1])
        if not args.quiet:  # Suggest remove broken package or install new model
            utils.print_commands_suggestions_on_stderr('remove', 'install')
        sys.exit(1)

    except utils.UnsupportedScriptExtensionException as e:
        msg = "Could not determine an interpreter for extension '{}'"
        utils.print_error_exit(msg, e.args[0])

    except utils.CommandNotFoundException as e:
        msg = "The command '{}' was not found for this model '{}'."
        utils.print_error(msg, e.args[0], e.args[1])
        if not args.quiet:  # Suggest check if any available commands
            utils.print_commands_suggestions_on_stderr('commands')
        sys.exit(1)

    except utils.LackDependencyException as e:
        msg = "Required dependencies are not installed for this model: \n  ====> \033[31m{}\033[0m"
        utils.print_error(msg, e.args[0])
        if not args.quiet:  # Suggest install dependencies
            utils.print_commands_suggestions_on_stderr('configure')
        sys.exit(1)

    except utils.DataResourceNotFoundException:
        msg = "Some data or model files required by the model package are missing!"
        utils.print_error(msg)
        if not args.quiet:  # Suggest download data
            utils.print_commands_suggestions_on_stderr('configure')
        sys.exit(1)

    except utils.ConfigureFailedException:  # configure failed, then just quit
        sys.exit(1)

    except (KeyboardInterrupt, EOFError):  # Catch Ctrl-C and Ctrl-D
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
