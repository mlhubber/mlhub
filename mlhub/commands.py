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
import glob
import requests
import urllib.request
import urllib.error
import zipfile
import subprocess
import textwrap
import logging
import re

from shutil import move, rmtree
from distutils.version import StrictVersion

import mlhub.utils as utils
from mlhub.constants import (
    MLINIT,
    DESC_YAML,
    DESC_YML,
    EXT_MLM,
    README,
    COMPLETION_MODELS,
    COMPLETION_COMMANDS,
    COMPLETION_SCRIPT,
    CACHE_DIR,
)

# The commands are implemented here in a logical order with each
# command providing a suggesting of the following command.

# ------------------------------------------------------------------------
# AVAILABLE
# ------------------------------------------------------------------------


def list_available(args):
    """List the name and title of the models in the Hub."""

    # Setup.

    logger = logging.getLogger(__name__)
    logger.info('List available models.')

    mlhub = utils.get_repo(args.mlhub)
    logger.debug('Get repo meta data from {}'.format(mlhub))
    meta = utils.get_repo_meta_data(mlhub)

    # List model name only.

    if args.name_only:
        models = [info["meta"]["name"] for info in meta]
        print('\n'.join(models))
        return

    # Provide some context.

    if not args.quiet:
        print("The repository '{}' provides the following models:\n".format(mlhub))

    # List the meta data.

    for info in meta:
        utils.print_meta_line(info)

    # Update bash tab completion

    utils.update_completion_list(COMPLETION_MODELS, {e['meta']['name'] for e in meta})

    # Suggest next step.
    
    if not args.quiet:
        utils.print_next_step('available')
        if not os.path.exists(MLINIT):
            print("Why not give the 'rain' model a go...\n\n" +
                  "  $ ml install rain\n")

# ------------------------------------------------------------------------
# INSTALLED
# ------------------------------------------------------------------------


def list_installed(args):
    """List the installed models."""

    logger = logging.getLogger(__name__)
    logger.info('List installed models.')

    # Find installed models, ignoring special folders like R.

    if os.path.exists(MLINIT):
        msg = " in '{}'.".format(MLINIT)
        models = [f for f in os.listdir(MLINIT)
                  if os.path.isdir(os.path.join(MLINIT, f))
                  and f != "R"
                  and not f.startswith('.')
                  and not f.startswith('_')]
    else:
        msg = ". '{}' does not exist.".format(MLINIT)
        models = []

    models.sort()

    # Only list model names

    if args.name_only:
        print('\n'.join(models))
        return
        
    # Report on how many models we found installed.
        
    mcnt = len(models)
    plural = "s" if mcnt != 1 else ""
    print("Found {} model{} installed{}".format(mcnt, plural, msg))

    # Report on each of the installed models.
        
    if mcnt > 0:
        print("")

    invalid_models = []
    for p in models:
        try:
            entry = utils.load_description(p)
            utils.print_meta_line(entry)
        except utils.DescriptionYAMLNotFoundException:
            mcnt -= 1
            invalid_models.append(p)
            continue

        # Update available commands for the model for fast bash tab completion.
        utils.update_completion_list(COMPLETION_COMMANDS, set(entry['commands']))

    #
    invalid_mcnt = len(invalid_models)
    if invalid_mcnt > 0:
        print("\nOf which {} model package{} {} broken:\n".format(
            invalid_mcnt,
            's' if invalid_mcnt > 1 else '',
            'are' if invalid_mcnt > 1 else 'is'))
        print("  ====> \033[31m" + ', '.join(invalid_models) + "\033[0m")
        print(utils.get_command_suggestion('remove'))

    # Suggest next step.
    
    if not args.quiet:
        if mcnt > 0:
            utils.print_next_step('installed', scenario='exist')
        else:
            utils.print_next_step('installed', scenario='none')

# -----------------------------------------------------------------------
# INSTALL
# ------------------------------------------------------------------------

def install_model(args):
    """Install a model.

    Args:
        args.model (str): mlm file path, or mlm file url, or model name.
    """

    # Setup.  And ensure the local init dir exists.

    logger = logging.getLogger(__name__)
    logger.info("Install model")
    logger.debug("args: {}".format(args))

    url = None
    init = utils.create_init()

    # Identify if it is a local file name to install.
    
    if utils.ends_with_mlm(args.model) and not utils.is_url(args.model):

        # Identify the local mlm file to install.

        local = args.model  # model package file local path
        logger.debug("Local mlm file: {}".format(local))
        mlmfile, model, version = utils.interpret_mlm_name(local)

    else:
        if utils.is_url(args.model):

            # A specific URL was provided.

            url = args.model
            logger.debug("Provided URL: {}".format(url))

        else:

            # Or obtain the repository meta data from Packages.yaml.

            url, meta = utils.get_model_url_from_repo(args.model, args.mlhub)
            logger.debug("URL from repo: {}".format(url))

            utils.update_completion_list(  # Update bash completion word list of available models.
                COMPLETION_MODELS,
                {e['meta']['name'] for e in meta})

        # Further setup.

        mlmfile, model, version = utils.interpret_mlm_name(url)
        local = os.path.join(init, mlmfile)  # model package file local path
            
    # Check if model is already installed.

    logger.debug('mlmfile: {}, model: {}, version: {}'.format(mlmfile, model, version))
    path = os.path.join(init, model)  # Installation path
    if os.path.exists(path):
        info = utils.load_description(model)
        installed_version = info['meta']['version']
        if StrictVersion(installed_version) > StrictVersion(version):
            yes = utils.yes_or_no("Downgrade '{}' from version '{}' to version '{}'",
                                  model, installed_version, version)
        elif StrictVersion(installed_version) == StrictVersion(version):
            yes = utils.yes_or_no("Replace '{}' version '{}' with version '{}'",
                                  model, installed_version, version)
        else:
            yes = utils.yes_or_no("Upgrade '{}' from version '{}' to version '{}'",
                                  model, installed_version, version)

        if not yes:
            sys.exit(0)
        else:
            print()

        logger.info('Remove installed model: {}'.format(model))
        rmtree(path)

    # Download the model now if not a local file.
        
    if url is not None:

        # Informative message about the model location and size.

        logger.info('Download mlm file from {}.'.format(url))
        if not args.quiet:
            print("Package " + url + "\n")
        meta = requests.head(url)
        if meta.status_code != requests.codes.ok:
            raise utils.ModelURLAccessException(url)
        dsize = "{:,}".format(int(meta.headers.get("content-length")))
        if not args.quiet:
            print("Downloading '{}' ({} bytes) ...\n".format(mlmfile, dsize))

        # Download the archive from the URL.

        try:
            urllib.request.urlretrieve(url, local)
        except urllib.error.HTTPError as error:
            logger.error("Downloading mlm file from URL failed: '{}'".format(url, exc_info=True))
            raise utils.ModelDownloadHaltException(url, error.reason.lower())

    logger.info('Extract mlm file.')
    if not os.path.exists(local):
        msg = "File is not found: {}"
        utils.print_error_exit(msg, local)

    zipfile.ZipFile(local).extractall(MLINIT)

    # Support either .yml or .yaml "cheaply". Should really try and
    # except but eventually will remove the yml file. The yaml authors
    # suggest .yaml.

    desc_yml = os.path.join(path, DESC_YML)
    desc_yaml = os.path.join(path, DESC_YAML)
    if (not os.path.exists(desc_yaml)) and os.path.exists(desc_yml):
        move(desc_yml, desc_yaml)

    utils.update_completion_list(  # Update bash completion word list of available commands.
        COMPLETION_COMMANDS,
        set(utils.load_description(model)['commands']))
    
    if not args.quiet:
        # Informative message about the size of the installed model.
        
        print("Extracted '{}' into\n'{}' ({:,} bytes).".format(mlmfile, path, utils.dir_size(path)))
            
        # Suggest next step. README or DOWNLOAD

        utils.print_next_step('install', model=model)

# -----------------------------------------------------------------------
# DOWNLOAD
# ------------------------------------------------------------------------


def download_model(args):
    """Download the large pre-built model."""

    # TODO: Will this be a url in the DESCRIPTION file or will it be a
    # download.sh script. Which ever (maybe either), if it is present
    # then this command is available and will download the required
    # file, perhaps from the actual source of the model.
    
    model = args.model
   
    # Check that the model is installed.

    utils.check_model_installed(model)
    
    if not args.quiet:
        utils.print_next_step('download', model=model)

# ------------------------------------------------------------------------
# README
# ------------------------------------------------------------------------


def readme(args):
    """Display the model's README information."""

    # Setup.
    logger = logging.getLogger(__name__)

    model = args.model
    path = MLINIT + model
    readme_file = os.path.join(path, README)
    logger.info("Get README of {}.".format(model))

    # Check that the model is installed.

    utils.check_model_installed(model)
    
    # Display the README.

    if not os.path.exists(readme_file):
        raise utils.ModelReadmeNotFoundException(model, readme_file)

    with open(readme_file, 'r') as f:
        print(utils.drop_newline(f.read()))

    # Suggest next step.

    if not args.quiet:
        utils.print_next_step('readme', model=model)

# ------------------------------------------------------------------------
# LICENSE
# ------------------------------------------------------------------------


def license(args):
    """Display the mode's LICENSE information."""

    print("Please assist by implementing this command.")
    
# -----------------------------------------------------------------------
# COMMANDS
# ------------------------------------------------------------------------


def list_model_commands(args):
    """ List the commands supported by this model."""

    # Setup.

    logger = logging.getLogger(__name__)
    model = args.model
    logger.info("List available commands of '{}'".format(model))

    # Check that the model is installed.

    utils.check_model_installed(model)
    
    info = utils.load_description(model)

    if args.name_only:
        print('\n'.join(list(info['commands'])))
        return
    
    msg = "The '{}' model "
    if 'title' not in info['meta']:
        title = None
    else:
        title = utils.lower_first_letter(utils.dropdot(info['meta']['title']))
        msg += "({}) "

    msg += "supports the following commands:"
    msg = msg.format(model, title)
    msg = textwrap.fill(msg, width=75)
    print(msg)

    for cmd in info['commands']:
        utils.print_model_cmd_help(info, cmd)

    # Update available commands for the model for fast bash tab completion.
    utils.update_completion_list(COMPLETION_COMMANDS, set(info['commands']))

    # Suggest next step.
    
    if not args.quiet:
        utils.print_next_step('commands', description=info, model=model)

# -----------------------------------------------------------------------
# CONFIGURE
# ------------------------------------------------------------------------


def configure_model(args):
    """Ensure the user's environment is configured."""

    # TODO: Install packages natively for those listed in
    # dependencies. Then if there is also a configure.sh, then run
    # that for additoinal setup.

    # Other ideas re cofiguration
    #
    # 1 Construct mlhub container (from Ubuntu) with known starting point
    #
    # 2 Assume the user is on a DSVM with free Azure account to test out.
    #
    # 3 Read dependencies: and language: and then install as required:
    #
    # 4 Assume model packager provides a configure.R script. This is a
    #   override and no other configuration happens if this is
    #   supplied. Alternatively this is viewed as a cop-out prividing
    #   no support from mlhub for the model packager. The preference
    #   would be to use the dependencies: tag to list the required R
    #   or python packages.
    #
    # So the meta-code might be
    #
    #   if file.exists(configure.XX):
    #     XX configure.XX
    #   else if language: == "Rscript":
    #     packages <- dependencies:
    #     install  <- packages[!(packages %in% installed.packages()[,"Package"])]
    #     if(length(new.packages)) install.packages(install)
    #   else if language: == "python":
    #     packages = dependencies:
    #     cat pacakges > requirements.txt
    #     pip install -r requirements.txt
    #

    if not args.model:

        # Configure ml.  Currently only bash completion.

        import platform
        sys_version = platform.uname().version.lower()
        if 'debian' in sys_version or 'ubuntu' in sys_version:
            path = os.path.dirname(__file__)
            commands = [
                'sudo install -m 0644 {} /etc/bash_completion.d'.format(COMPLETION_SCRIPT),
                'ml available > /dev/null',
                'ml installed > /dev/null', ]

            for cmd in commands:
                print('Executing: ', cmd)
                subprocess.run(cmd, shell=True, cwd=path, stderr=subprocess.PIPE)
                
            print("\nFor tab completion to take immediate effect: \n\n  $ source /etc/bash_completion.d/ml.bash\n")

        return
    
    # Setup.
    
    model = args.model
    path = MLINIT + model
   
    # Check that the model is installed.

    utils.check_model_installed(model)

    # If there are any configure scripts then run them, else print the
    # list of supplied dependencies if any. Note that Python's 'or' is
    # lazy evaluation.

    conf = utils.configure(path, "configure.sh", args.quiet)
    conf = utils.configure(path, "configure.R", args.quiet) or conf
    conf = utils.configure(path, "configure.py", args.quiet) or conf

    if not conf:
        try:
            info = utils.load_description(model)
            deps = info["meta"]["dependencies"]

            if not args.quiet:
                msg = "No configuration script provided for this model. "
                msg = msg + "The following dependencies are required:\n"
                print(msg)

            print("  ====> \033[31m" + deps + "\033[0m")
        except KeyError:
            print("No configuration provided (maybe none is required).")
            
    # Suggest next step.
    
    if not args.quiet:
        utils.print_next_step('configure', model=model)

# -----------------------------------------------------------------------
# DISPATCH
# ------------------------------------------------------------------------


def dispatch(args):
    """Dispatch other commands to the appropriate model provided script."""

    cmd = args.cmd
    model = args.model
    path = MLINIT + model

    param = " ".join(args.param)

    # Check that the model is installed.

    utils.check_model_installed(model)
    
    desc = utils.load_description(model)

    # Check if cmd needs to use graphic display indicated in DESCRIPTION.yaml.

    if 'display' in desc['meta'] and cmd in desc['meta']['display'] and os.environ.get('DISPLAY', '') == '':
        msg = "Graphic display is required but not available for command '{}'. Continue"
        yes = utils.yes_or_no(msg, cmd, yes=False)
        if not yes:
            msg = """
To enable DISPLAY be sure to connect to the server using 'ssh -X'
or else connect to the server's desktop using a local X server like X2Go.

"""
            sys.stdout.write(msg)
            sys.exit(1)

    # Obtain the default/chosen language for the package.

    lang = desc["meta"]["languages"]

    # Deal with malformed 'languages' field
    
    lang_opts = {"python": "py", "R": "R"}
    for k in list(lang_opts):
        if lang in k:
            lang = lang_opts[k]
            break
        
    # Obtain the specified script file.
    
    script = cmd + "." + lang

    logger = logging.getLogger(__name__)
    logger.debug("Execute the script: " + os.path.join(path, script))
     
    if cmd not in list(desc['commands']) or not os.path.exists(os.path.join(path, script)):
        raise utils.CommandNotFoundException(cmd, model)

    # Determine the interpreter to use
    #
    # .R => Rscript; .py => python, etc.

    interpreter = utils.interpreter(script)

    # _MLHUB_CMD_CWD: a environment variable indicates current working
    #          directory where command `ml xxx` is invoked.
    # _MLHUB_MODEL_NAME: env variable indicates the name of the model.
    # 
    # The above two env vars can be obtained by helper function, such
    # as utils.get_cmd_cwd().  And model package developer should be
    # use the helper function instead of the env vars directly.

    command = "export _MLHUB_CMD_CWD='{}'; export _MLHUB_MODEL_NAME='{}'; {} {} {}".format(
        os.getcwd(), model, interpreter, script, param)

    logger.debug("(cd " + path + "; " + command + ")")

    proc = subprocess.Popen(command, shell=True, cwd=path, stderr=subprocess.PIPE)
    output, errors = proc.communicate()
    if proc.returncode != 0:
        errors = errors.decode("utf-8")

        # Check if it is Python dependency unsatisfied

        dep_required = re.compile(r"ModuleNotFoundError: No module named '(.*)'").search(errors)

        # Check if R dependency unsatisified

        if dep_required is None:
            dep_required = re.compile(r"there is no package called ‘(.*)’").search(errors)

        # Check if required data resource not found

        data_required = re.compile(r"mlhub.utils.DataResourceNotFoundException").search(errors)

        if dep_required is not None:  # Dependency unsatisfied
            dep_required = dep_required.group(1)
            logger.error("Dependency unsatisfied: {}\n{}".format(dep_required, errors))
            raise utils.LackDependencyException(dep_required, model)
        elif data_required is not None:  # Data not found
            raise utils.DataResourceNotFoundException()
        else:  # Other unknown errors
            print("An error was encountered:\n")
            print(errors)

    else:
        # Suggest next step

        if not args.quiet:
            utils.print_next_step(cmd, description=desc, model=model)
    
# ------------------------------------------------------------------------
# DONATE
# ------------------------------------------------------------------------


def donate(args):
    """Consider a donation to the author."""

    print("Please assist by implementing this command: support donations to the author.")
    
# ------------------------------------------------------------------------
# CLEAN
# ------------------------------------------------------------------------


def remove_mlm(args):
    """Remove downloaded {} files.""".format(EXT_MLM)

    mlm = glob.glob(os.path.join(MLINIT, "*.mlm"))
    mlm.sort()
    for m in mlm:
        if utils.yes_or_no("Remove model package archive '{}'", m):
            os.remove(m)

# ------------------------------------------------------------------------
# REMOVE
# ------------------------------------------------------------------------


def remove_model(args):
    """Remove installed model."""

    # Setup.
    
    model = args.model
    path = MLINIT
    cache = None
    if model is None:
        if os.path.exists(MLINIT):
            msg = "*Completely* remove all installed models in '{}'"
        else:
            msg = "The local model folder '{}' does not exist. Nothing to do."
            msg = msg.format(MLINIT)
            print(msg)
            return
    else:
        path = os.path.join(path, model)
        if os.path.exists(utils.get_package_cache_dir(model)):
            cache = utils.get_package_cache_dir(model)
        msg = "Remove '{}'"
        
        # Check that the model is installed.

        utils.check_model_installed(model)

    if utils.yes_or_no(msg, path, yes=False):
        rmtree(path)
        if cache is not None and utils.yes_or_no("Remove cache '{}' as well", cache, yes=False):
            rmtree(cache)
    else:
        if model is None and not args.quiet:
            utils.print_next_step('remove')
