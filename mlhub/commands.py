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
import yaml
import textwrap
import locale
import importlib.util
import re

from tempfile import TemporaryDirectory
from shutil import move, rmtree
from distutils.version import StrictVersion

import mlhub.utils as utils
from mlhub.constants import (
    MLINIT,
    DESC_YAML,
    DESC_YML,
    APP,
    APPX,
    CMD,
    HUB_PATH,
    EXT_MLM,
    EXT_AIPK,
    META_YAML,
    README,
    META_YML,
    DEBUG,
)

# The commands are implemented here in a logical order with each
# command providing a suggesting of the following command.

#------------------------------------------------------------------------
# AVAILABLE
#------------------------------------------------------------------------

def list_available(args):
    """List the name and title of the models in the Hub."""

    # Setup.

    mlhub = utils.get_repo(args.mlhub)
    meta  = utils.get_repo_meta_data(mlhub)

    # Provide some context.

    if not args.quiet:
        print("The repository '{}' provides the following models:\n".format(mlhub))

    # List the meta data.
    
    for info in meta:
        utils.print_meta_line(info)

    # Suggest next step.
    
    if not args.quiet:
        utils.print_next_step('available')

#------------------------------------------------------------------------
# INSTALLED
#------------------------------------------------------------------------

def list_installed(args):
    """List the installed models."""

    # Find installed models, ignoring special folders like R.

    if os.path.exists(MLINIT):
        msg = " in '{}'.".format(MLINIT)
        models = [f for f in os.listdir(MLINIT)
                  if os.path.isdir(os.path.join(MLINIT, f)) and f != "R"]
    else:
        msg = ". '{}' does not exist.".format(MLINIT)
        models = []

    models.sort()
        
    # Report on how many models we found installed.
        
    mcnt = len(models)
    plural = "s"
    if mcnt == 1: plural = ""
    print("Found {} model{} installed{}".format(mcnt, plural, msg))

    # Report on each of the installed models.
        
    if mcnt > 0: print("")
    for p in models:
        entry = utils.load_description(p)
        utils.print_meta_line(entry)

    # Suggest next step.
    
    if not args.quiet:
        if mcnt > 0:
            utils.print_next_step('installed', scenario='exist')
        else:
            utils.print_next_step('installed', scenario='none')

#-----------------------------------------------------------------------
# INSTALL
#------------------------------------------------------------------------

def install_model(args):
    """Install a model."""

    # Setup.

    url = None

    # Identify if it is a local file name to install.
    
    if args.model.endswith(EXT_MLM) and not re.findall('http[s]?:', args.model):

        # Identify the local mlm file to install.

        local   = args.model
        mlmfile = local
        model   = local.split("_")[0]
        version = local.split("_")[1].replace(EXT_MLM, "")

        # Ensure the local init dir exists.
        
        init = utils.create_init()
        path = os.path.join(init, model)

    else:

        if re.findall('http[s]?:', args.model):

            # A specific URL was provided.
            
            url = args.model
            model = url.split("/")[-1].split("_")[0]

            # Check that the URL exists.
            
            r = requests.head(url)
            if not r.status_code == requests.codes.ok:
                msg = "{}the url '{}' was not found."
                msg = msg.format(APPX, url)
                print(msg, file=sys.stderr)
                sys.exit(1)
            
        else:
            
            # Or obtain the repository meta data from Packages.yaml.

            model = args.model
        
            mlhub = utils.get_repo(args.mlhub)
            meta  = utils.get_repo_meta_data(mlhub)

            # Find the first matching entry in the meta data.

            url = None
            for entry in meta:
                if model == entry["meta"]["name"]:
                    url = mlhub + entry["meta"]["filename"]
                    break

        # If not found suggest how a model might be installed.

        if url is None:
            msg = "{}no model named '{}' was found on '{}'."
            msg = msg.format(APPX, model, mlhub)
            print(msg, file=sys.stderr)
            if not args.quiet:
                msg = "\nYou can list available models with:\n\n  $ {} available\n"
                msg = msg.format(CMD)
                print(msg, file=sys.stderr)
            sys.exit(1)
            
        if args.debug: print(DEBUG + "model file url is: " + url)

        # Ensure file to be downloaded has the expected filename extension.

        if not url.endswith(EXT_MLM) and not url.endswith(EXT_AIPK):
            msg = "{}the below url is not a {} file. Malformed '{}' from the repository?\n  {}"
            msg = msg.format(APPX, EXT_MLM, META_YAML, url)
            print(msg, file=sys.stderr)
            sys.exit(1)

        # Further setup.

        init    = utils.create_init()
        mlmfile = url.split("/")[-1]
        version = mlmfile.split("_")[1].replace(EXT_MLM, "").replace(EXT_AIPK, "")

        local   = os.path.join(init, mlmfile)
        path    = os.path.join(init, model)

    # Check if model is already installed.
        
    if os.path.exists(path):
        info = utils.load_description(model)
        installed_version = info['meta']['version']
        if StrictVersion(installed_version) > StrictVersion(version):
            msg = "Installed version '{}' of '{}' to be downgraded to version '{}'. Continue [Y/n]? "
            msg = msg.format(installed_version, model, version)
            sys.stdout.write(msg)
            choice = input().lower()
            if choice == 'n': sys.exit(1)
        elif StrictVersion(installed_version) == StrictVersion(version):
            msg = "Installed version '{}' of '{}' to be overwritten. Continue [Y/n]? "
            msg = msg.format(installed_version, model, version)
            sys.stdout.write(msg)
            choice = input().lower()
            if choice == 'n': sys.exit(1)
        else:
            msg = "Replacing '{}' version '{}' with '{}'."
            msg = msg.format(model, installed_version, version)
            print(msg)
        rmtree(path)
        print()

    # Download the model now if not a local file.
        
    if not url is None:

        # Informative message about the model location and size.

        if not args.quiet: print("Model " + url + "\n")
        meta = requests.head(url)
        dsize = "{:,}".format(int(meta.headers.get("content-length")))
        if not args.quiet: print("Downloading '{}' ({} bytes) ...\n".
                                 format(mlmfile, dsize))

        # Download the archive from the URL.

        try:
            urllib.request.urlretrieve(url, local)
        except urllib.error.HTTPError as error:
            msg = "{}'{}' {}."
            msg = msg.format(APPX, url, error.reason.lower())
            print(msg, file=sys.stderr)
            sys.exit(1)

    zip = zipfile.ZipFile(local)
    zip.extractall(MLINIT)

    # Support either .yml or .yaml "cheaply". Should really try and
    # except but eventually will remove the yml file. The yaml authors
    # suggest .yaml.

    desc_yml  = os.path.join(path, DESC_YML)
    desc_yaml = os.path.join(path, DESC_YAML)
    if (not os.path.exists(desc_yaml)) and os.path.exists(desc_yml):
        move(desc_yml, desc_yaml)

    # Informative message about the size of the installed model.
    
    if not args.quiet:
        dsz = 0
        for (pth, dir, files) in os.walk(path):
            for f in files:
                tfilename = os.path.join(pth, f)
                dsz += os.path.getsize(tfilename)
        print("Extracted '{}' into\n'{}' ({:,} bytes).".
              format(mlmfile, path, dsz))
            
    # Suggest next step. README or DOWNLOAD
    
    if not args.quiet:
        utils.print_next_step('install', model=model)
    
#-----------------------------------------------------------------------
# DOWNLOAD
#------------------------------------------------------------------------

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

#------------------------------------------------------------------------
# README
#------------------------------------------------------------------------

def readme(args):
    """Display the model's README information."""

    # Setup.
    
    model  = args.model
    path   = MLINIT + model
    readme = os.path.join(path, README)

    # Check that the model is installed.

    utils.check_model_installed(model)
    
    # Display the README.
    
    with open(readme, 'r') as f:
        print(utils.drop_newline(f.read()))
    
    # Suggest next step.

    if not args.quiet:
        utils.print_next_step('readme', model=model)

#------------------------------------------------------------------------
# LICENSE
#------------------------------------------------------------------------

def license(args):
    """Display the mode's LICENSE information."""

    print("Please assist by implementing this command.")
    
#-----------------------------------------------------------------------
# COMMANDS
#------------------------------------------------------------------------

def list_model_commands(args):
    """ List the commands supported by this model."""

    # Setup.
    
    model = args.model

    # Check that the model is installed.

    utils.check_model_installed(model)
    
    info = utils.load_description(model)

    msg = "The model '{}' "
    if 'title' not in info['meta']:
        title = None
    else:
        title = utils.lower_first_letter(utils.dropdot(info['meta']['title']))
        msg += "({}) "

    msg += "supports the following commands:"
    msg = msg.format(model, title)
    msg = textwrap.fill(msg, width=75)
    print(msg)

    for c in info['commands']:
        print("\n$ {} {} {}".format(CMD, c, model))
        print("  " + info['commands'][c])

    # Suggest next step.
    
    if not args.quiet:
        utils.print_next_step('commands', description=info, model=model)

#-----------------------------------------------------------------------
# CONFIGURE
#------------------------------------------------------------------------

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
    
    # Setup.
    
    model = args.model
    path  = MLINIT + model
   
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
        except:
            print("No configuration provided (maybe none is required).")
            
    # Suggest next step.
    
    if not args.quiet:
        utils.print_next_step('configure', model=model)

#-----------------------------------------------------------------------
# DISPATCH
#------------------------------------------------------------------------

def dispatch(args):
    """Dispatch other commands to the appropriate model provided script."""

    cmd   = args.cmd
    model = args.model
    path  = MLINIT + model

    param = " ".join(args.param)

    # Check that the model is installed.

    utils.check_model_installed(model)
    
    desc = utils.load_description(model)

    # Check if cmd needs to use graphic display indicated in DESCRIPTION.yaml.

    if 'display' in desc['meta'] and cmd in desc['meta']['display'] and os.environ.get('DISPLAY', '') == '':
        msg = "Graphic display is required but not available for command '{}'. Continue [y/N]? "
        msg = msg.format(cmd)
        sys.stdout.write(msg)
        choice = input().lower()
        if choice != 'y':
            msg = """
To enable DISPLAY be sure to connect to the server using 'ssh -X'
or else connect to the server's desktop using a local X server like X2Go.

"""
            sys.stdout.write(msg)
            sys.exit(1)

    # Obtain the default/chosen language for the package.

    lang = desc["meta"]["languages"]
        
    # Obtain the specified script file.
    
    script  = cmd + "." + lang
    
    if args.debug:
        print(DEBUG + "execute the script: " + os.path.join(path, script))
     
    if not os.path.exists(os.path.join(path, script)):
        msg = """{}The command '{}' was not found for this model.

Try using 'commands' to list all supported commands:

  $ {} commands {}
""".format(APPX, cmd, CMD, model)
        print(msg, file=sys.stderr)
        sys.exit(1)

    # Determine the interpreter to use
    #
    # .R => Rscript; .py => python, etc.

    interpreter = utils.interpreter(script)

    command = "{} {} {}".format(interpreter, script, param)

    if args.debug:
        print(DEBUG + "(cd " + path + "; " + command + ")")
    proc = subprocess.Popen(command, shell=True, cwd=path, stderr=subprocess.PIPE)
    output, errors = proc.communicate()
    if proc.returncode != 0:
        print("An error was encountered:\n")
        print(errors.decode("utf-8"))
    else:
        # Suggest next step

        if not args.quiet:
            utils.print_next_step(cmd, description=desc, model=model)
    
#------------------------------------------------------------------------
# DONATE
#------------------------------------------------------------------------

def donate(args):
    """Consider a donation to the author."""

    print("Please assist by implementing this command: support donations to the author.")
    
#------------------------------------------------------------------------
# CLEAN
#------------------------------------------------------------------------

def remove_mlm(args):
    """Remove downloaded {} files.""".format(EXT_MLM)

    mlm = glob.glob(os.path.join(MLINIT, "*.mlm"))
    mlm.sort()
    for m in mlm:
        msg = "Remove model package archive '{}' [Y/n]? ".format(m)
        sys.stdout.write(msg)
        choice = input().lower()
        if choice == 'y' or choice == '': os.remove(m)

#------------------------------------------------------------------------
# REMOVE
#------------------------------------------------------------------------

def remove_model(args):
    """Remove installed model."""

    # Setup.
    
    model  = args.model
    if model is None:
        if os.path.exists(MLINIT):
            path = MLINIT
            msg  = "*Completely* remove all installed models in '{}' [y/N]? "
        else:
            msg = "The local model folder '{}' does not exist. Nothing to do."
            msg = msg.format(MLINIT)
            print(msg)
            sys.exit(1)
    else:
        path = MLINIT + model
        msg = "Remove '{}' [y/N]? "
        
        # Check that the model is installed.

        utils.check_model_installed(model)

    sys.stdout.write(msg.format(path))
    choice = input().lower()
    if choice == 'y':
        rmtree(path)
    else:
        if model is None and not args.quiet:
            utils.print_next_step('remove')
