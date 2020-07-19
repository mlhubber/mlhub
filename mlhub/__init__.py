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

import argparse
import logging
import mlhub.commands as commands
import mlhub.constants as constants
import mlhub.utils as utils
import os
import sys

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

logger.info('---------- {} {} ----------'.format(os.path.basename(sys.argv[0]), ' '.join(sys.argv[1:])))

# ----------------------------------------------------------------------
# Set up command line parser and dispatch commands.
# ----------------------------------------------------------------------


def main():
    """Main program for the command line script."""

    # --------------------------------------------------
    # Global option parser.  See mlhub.constants.OPTIONS
    # --------------------------------------------------

    logger.info("Create global option parser.")
    global_option_parser = argparse.ArgumentParser(
        add_help=False  # Disable -h or --help.  Use custom help msg instead.
    )
    utils.OptionAdder(global_option_parser, constants.OPTIONS).add_alloptions()

    # --------------------------------------------------
    # Parse version
    # --------------------------------------------------

    logger.info("Parse global options.")
    args, extras = global_option_parser.parse_known_args(sys.argv[1:])

    if args.debug:  # Add console log handler to log debug message to console
        logger.info('Enable printing out debug log on console.')
        utils.add_log_handler(
            logger,
            logging.StreamHandler(),
            logging.DEBUG,
            constants.LOG_CONSOLE_FORMAT)

    logger.debug(f'args: {args}, extra_args: {extras}')

    # Get the first positional argument.

    pos_args = [(i, arg) for i, arg in enumerate(sys.argv[1:]) if not arg.startswith('-')]
    first_pos_arg_index, first_pos_arg = pos_args[0] if len(pos_args) != 0 else (None, None)
    logger.debug(f'First positional argument: {first_pos_arg}')

    if args.version:
        logger.info('Query version.')

        # --------------------------------------------------
        # Query the version of the model, for example
        #   $ ml rain -v
        #   $ ml -v rain
        # Otherwise, output the version of ml
        #   $ ml -v
        # --------------------------------------------------

        if first_pos_arg is not None:  # Print model version
            print(first_pos_arg, "version", utils.get_version(first_pos_arg))
        else:  # Print mlhub version
            print(constants.APP, "version", utils.get_version())

        return 0

    # --------------------------------------------------
    # Parse command line args for basic commands or model specific commands
    # --------------------------------------------------

    # Correct misspelled command if possible.

    if first_pos_arg is not None:

        # Only match basic commands since model pkg commands are more
        # specific which would be better to be checked after the model
        # pkg name is known.

        # 20200719 Check for aliases here as a temporary hack since
        # aliases are not currently dealt with in the call to
        # get_misspelled_command().

        if first_pos_arg == "remove":
            matched_cmd = "uninstall"
        else:
            matched_cmd = utils.get_misspelled_command(first_pos_arg,
                                                       list(constants.COMMANDS))

        if matched_cmd is not None:
            sys.argv[first_pos_arg_index + 1] = matched_cmd
            first_pos_arg = matched_cmd

    # Dispatch commands.

    if first_pos_arg is not None and first_pos_arg not in constants.COMMANDS:

        # Model specific commands, such as demo, display.

        logger.info("Parse model specific dommands.")
        model_cmd_parser = argparse.ArgumentParser(
            prog=constants.CMD,
            parents=[global_option_parser],
            add_help=False  # Use custom help message
        )
        model_cmd_parser.add_argument('cmd', metavar='command')
        model_cmd_parser.add_argument('model')
        args, extras = model_cmd_parser.parse_known_args()
        logger.debug(f"args: {args}")
        logger.debug(f"extra_args: {extras}")

        # Simple help message for the model-specific command

        if '--help' in extras or '-h' in extras:
            logger.debug(f"Help for command '{args.cmd}' of '{args.model}'")
            utils.print_model_cmd_help(utils.load_description(args.model), args.cmd)
            print()
            return 0

        setattr(args, 'func', commands.dispatch)
        setattr(args, 'param', extras)

    else:

        # Basic commands, such as install, readme.  See mlhub.constants.COMMANDS

        logger.info("Parse basic common commands.")
        basic_cmd_parser = argparse.ArgumentParser(
            prog=constants.CMD,
            description="Access models from the ML Hub.",
            parents=[global_option_parser])
        subparsers = basic_cmd_parser.add_subparsers(title='subcommands', dest="cmd")
        utils.SubCmdAdder(subparsers, commands, constants.COMMANDS).add_allsubcmds()
        args = basic_cmd_parser.parse_args()
        logger.debug(f"args: {args}")

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
        utils.print_error_exit(msg, constants.APP, e.args[0])

    except utils.MLTmpDirCreateException as e:
        msg = "The below '{}' tmp folder cannot be created:\n  {}"
        utils.print_error_exit(msg, constants.APP, e.args[0])

    except utils.MalformedMLMFileNameException as e:
        msg = "Malformed {} file:\n  {}"
        utils.print_error_exit(msg, constants.EXT_MLM, e.args[0])

    except utils.MalformedYAMLException as e:
        name = e.args[0]
        if os.path.sep in name or '/' in name:
            msg = "Malformed YAML file:\n  {}"
        else:
            msg = "Malformed description for model package '{}'!"
        utils.print_error_exit(msg, e.args[0])

    except utils.ModelURLAccessException as e:
        msg = "URL access failed:\n  {}"
        utils.print_error_exit(msg, e.args[0])

    except utils.YAMLFileAccessException as e:
        msg = "YAML file access failed:\n  {}"
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
        msg = f"URL - '{e.args[0]}' failed:\n  {e.args[1]}"
        utils.print_error_exit(msg)

    except utils.DescriptionYAMLNotFoundException as e:
        msg = "No MLHUB description file found: {}"

        location = e.args[0]
        if not utils.is_url(location):
            msg += "\n  The model package may be broken!"
            utils.print_error(msg, location)
            if not args.quiet:  # Suggest remove broken package or install new model
                utils.print_commands_suggestions_on_stderr('remove', 'install')
        else:
            msg += "\n  The given location may be wrong!"
            utils.print_error(msg, location)

        sys.exit(1)

    except utils.ModelNotInstalledException as e:
        msg = "model '{}' is not installed ({})."
        utils.print_error(msg, e.args[0], utils.get_init_dir())
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
        msg = "Required {} dependencies are not installed for this model: \n  ====> \033[31m{}\033[0m"
        utils.print_error(msg, 'R' if e.args[1] else 'Python',  e.args[0])
        if not args.quiet:  # Suggest install dependencies
            utils.print_commands_suggestions_on_stderr('configure')
        sys.exit(1)

    except utils.LackPrerequisiteException as e:
        msg = "Required pre-requisite not found: \n  ====> \033[31m{}\033[0m"
        utils.print_error(msg, e.args[0])
        if not args.quiet:  # Suggest install dependencies
            msg = "\nTo install required pre-requisites:\n\n  $ ml configure\n"
            utils.print_on_stderr(msg)
        sys.exit(1)

    except utils.DataResourceNotFoundException:
        msg = "Some data or model files required by the model package are missing!"
        utils.print_error(msg)
        if not args.quiet:  # Suggest download data
            utils.print_commands_suggestions_on_stderr('configure')
        sys.exit(1)

    except utils.MalformedPackagesDotYAMLException as e:
        msg = ("There is no '{}' available for the model package '{}' which may be under maintenance now.\n"
               "Please try again later.")
        utils.print_error(msg, e.args[0], e.args[1])
        if not args.quiet:  # Suggest check if any models available, since specified model not available
            utils.print_commands_suggestions_on_stderr('available')
        sys.exit(1)

    except utils.ModelPkgInstallationFileNotFoundException as e:
        msg = "No such package file: {}\n  The model package may be broken!"
        utils.print_error_exit(msg, e.args[0])

    except utils.ModelPkgDependencyFileNotFoundException as e:
        msg = "Failed to get file dependency: {}\n"
        utils.print_error_exit(msg, e.args[0])

    except utils.ModelPkgDependencyFileTypeUnknownException as e:
        msg = "Unknown file dependency type: {}\n"
        utils.print_error_exit(msg, e.args[0])

    except utils.ConfigureFailedException as e:  # configure failed, then just quit
        msg = "An error was encountered:\n{}\n"
        utils.print_error_exit(msg, e.args[0])

    except utils.InstallFailedException as e:
        msg = "An error was encountered:\n{}\n"
        utils.print_error_exit(msg, e.args[0])

    except (KeyboardInterrupt, EOFError):  # Catch Ctrl-C and Ctrl-D
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
