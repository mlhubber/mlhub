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
import requests
import urllib.request
import urllib.error
import zipfile
import subprocess
import yaml
import textwrap
import locale
import importlib.util
import platform

from tempfile import TemporaryDirectory
from shutil import move, rmtree
from distutils.version import StrictVersion

import mlhub.utils as utils
from mlhub.constants import MLINIT, DESC_YAML, DESC_YML, APP, APPX, CMD, HUB_PATH, EXT_MLM, EXT_AIPK, META_YAML, README, META_YML, DEBUG

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
        msg = "\nInstall a model with:\n\n  $ {} install <model>\n"
        msg = msg.format(CMD)
        print(msg)

#------------------------------------------------------------------------
# INSTALLED
#------------------------------------------------------------------------

def list_installed(args):
    """List the installed models."""

    # Find installed models.

    if os.path.exists(MLINIT):
        msg = "in '{}'.".format(MLINIT)
        models = [f for f in os.listdir(MLINIT)
                  if os.path.isdir(os.path.join(MLINIT, f))]
    else:
        msg = "since '{}' does not exist.".format(MLINIT)
        models = []

    # Report on how many models we found installed.
        
    mcnt = len(models)
    plural = "s"
    if mcnt == 1: plural = ""
    print("Found {} model{} installed {}".format(mcnt, plural, msg))

    # Report on each of the installed models.
        
    if mcnt > 0: print("")
    
    for p in models:
        entry = utils.load_description(p)
        utils.print_meta_line(entry)

    # Suggest next step.
    
    if not args.quiet:
        msg = "\nRun a model's demonstration script with:\n\n  $ {} demo <model>\n"
        msg = msg.format(CMD)
        print(msg)

#-----------------------------------------------------------------------
# INSTALL

def install_model(args):
    """Install a model."""

    # Setup.

    # Identify local file name to install.
    
    if args.model.endswith(EXT_MLM):

        # Identify the local mlm file to install.

        local   = args.model
        mlmfile = local
        model   = local.split("_")[0]
        version = local.split("_")[1].replace(EXT_MLM, "")

        # Ensure the local init dir exists.
        
        init = utils.create_init()
        path = os.path.join(init, model)

    else:

        # Obtain the repository meta data from Packages.yaml.
        
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

        # Download the archive from the URL.

        try:
            urllib.request.urlretrieve(url, local)
        except urllib.error.HTTPError as error:
            msg = "{}'{}' {}."
            msg = msg.format(APPX, url, error.reason.lower())
            print(msg, file=sys.stderr)
            sys.exit(1)

        # Informative message about the model location and size.

        if not args.quiet: print("Model " + url + "\n")
        meta = requests.head(url)
        dsize = "{:,}".format(int(meta.headers.get("content-length")))
        if not args.quiet: print("Downloading '{}' ({} bytes) ...\n".
                                 format(mlmfile, dsize))

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
    
    zip = zipfile.ZipFile(local)
    zip.extractall(MLINIT)

    # Support either .yml or .yaml "cheaply". Should really try and
    # except but eventually will removethe yml file. The yaml authors
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
        print("Extracted '{}' into\n'{}' ({:,} bytes).\n".
              format(mlmfile, path, dsz))
            
    # Suggest next step. README or DOWNLOAD
    
    if not args.quiet:
        msg = "Read the model information with:\n\n  $ {} readme {}\n"
        msg = msg.format(CMD, model)
        print(msg)
    
#-----------------------------------------------------------------------
# DOWNLOAD

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
        msg = "Model information is available:\n\n  $ {} readme {}\n"
        msg = msg.format(CMD, model)
        print(msg)

#-----------------------------------------------------------------------
# README

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
        print(f.read())
    
    # Suggest next step.

    if not args.quiet:
        msg = "Model dependencies are listed using:\n\n  $ {} configure {}\n"
        msg = msg.format(CMD, model)
        print(msg)

#------------------------------------------------------------------------
# LICENSE
#------------------------------------------------------------------------

def license(args):
    """Display the mode's LICENSE information."""

    print("Please assist by implementing this command.")
    
#-----------------------------------------------------------------------
# COMMANDS

def list_model_commands(args):
    """ List the commands supported by this model."""

    model = args.model

    # Check that the model is installed.

    utils.check_model_installed(model)
    
    info = utils.load_description(model)

    msg = "The model '{}' ({}) supports the following commands:"
    msg = msg.format(model, info['meta']['title'])
    msg = textwrap.fill(msg, width=60)
    print(msg + "\n")
    
    yaml.dump(info['commands'], sys.stdout, default_flow_style = False)

    # Suggest next step.
    
    if not args.quiet:
        msg = "Model dependencies are listed using:\n\n  $ {} configure {}\n"
        msg = msg.format(CMD, model)
        print(msg)

#-----------------------------------------------------------------------
# CONFIGURE

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

    # If there is a configure script and this is a Ubuntu host, then
    # run the configure script.

    conf = os.path.join(path, "configure.sh")
    if platform.dist()[0] in set(['debian', 'Ubuntu']) and os.path.exists(conf):
        command = "bash configure.sh"
        if not args.quiet:
            msg = "Configuration will take place using '{}'.\n"
            msg = msg.format(conf)
            print(msg)
        proc = subprocess.Popen(command, shell=True, cwd=path, stderr=subprocess.PIPE)
        output, errors = proc.communicate()
        if proc.returncode != 0:
            print("An error was encountered:\n")
            print(errors.decode("utf-8"))
    else:
        # For now simply list the declared dependencies for the user to
        # make sure they have it all installed.

        if not args.quiet:
            msg = """
Configuration is yet to be automated. The following dependencies are required:
"""
            print(msg)

        info = utils.load_description(model)
        msg = info["meta"]["dependencies"]

        print("  ====> \033[31m" + msg + "\033[0m")

    # Suggest next step.
    
    if not args.quiet:
        msg = "\nOnce configured run the demonstration:\n\n  $ {} demo {}\n"
        msg = msg.format(CMD, model)
        print(msg)

#-----------------------------------------------------------------------
# DISPATCH

def dispatch(args):
    """Dispatch other commands to the appropriate model provided script."""
    
    cmd   = args.cmd
    model = args.model
    path  = MLINIT + model

    param = " ".join(args.param)

    # Check that the model is installed.

    utils.check_model_installed(model)
    
    desc = utils.load_description(model)
        
    # Obtain the specified script file.
    
    script  = desc["commands"][cmd]["script"].split(" ")[0] + " " + param

    # Determine the interpreter to use
    #
    # .R => Rscript; .py => python, etc.

    (root, ext) = os.path.splitext(script)
    ext = ext.strip()
    if ext == ".R":
        interpreter = "Rscript"
    elif ext == ".py":
        interpreter = "python"
    else:
        msg = "Could not determine an interpreter for extension '{}'".format(ext)
        print(msg, file=sys.stderr)
        sys.exit()

    command = "{} {}".format(interpreter, script)
    if args.debug:
        print(DEBUG + "(cd " + path + "; " + command + ")")
    proc = subprocess.Popen(command, shell=True, cwd=path, stderr=subprocess.PIPE)
    output, errors = proc.communicate()
    if proc.returncode != 0:
        print("An error was encountered:\n")
        print(errors.decode("utf-8"))
    
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

    print("Please assist by implementing this command.")
    
