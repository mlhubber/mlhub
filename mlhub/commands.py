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
from shutil import copyfile

import mlhub.utils as utils
from mlhub.constants import INIT_DIR, DESC_YAML, DESC_YML, APP, APPX, CMD, HUB_PATH, EXT_MLM, META_YAML, README, META_YML

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
        msg = "\nList the installed models with:\n\n  $ {} installed\n"
        msg = msg.format(CMD)
        print(msg)

#------------------------------------------------------------------------
# INSTALLED
#------------------------------------------------------------------------

def list_installed(args):
    """List the installed models."""

    # Find installed models.

    if os.path.exists(INIT_DIR):
        msg = "in '{}'.".format(INIT_DIR)
        models = [f for f in os.listdir(INIT_DIR)
                  if os.path.isdir(os.path.join(INIT_DIR, f))]
    else:
        msg = "since '{}' does not exist.".format(INIT_DIR)
        models = []

    # Report on how many models we found installed.
        
    mcnt = len(models)
    plural = "s"
    if mcnt == 1: plural = ""
    print("Found {} model{} installed {}".format(mcnt, plural, msg))

    # Report on each of the installed models.
        
    if mcnt > 0: print("")
    
    for p in models:
        desc_yaml = os.path.join(INIT_DIR, p, DESC_YAML)
        if os.path.exists(desc_yaml):
            entry = yaml.load(open(desc_yaml))
        else:
            msg = "{}no '{}' found for '{}'."
            msg = msg.format(APPX, DESC_YAML, p)
            print(msg, file=sys.stderr)
            sys.exit(1)
        utils.print_meta_line(entry)

    # Suggest next step.
    
    if not args.quiet:
        msg = "\nInstall a model using:\n\n  $ {} install <name>\n"
        msg = msg.format(CMD)
        print(msg)

#-----------------------------------------------------------------------
# INSTALL

def install_model(args):
    """Install a model."""

    # Setup.

    model = args.model
    mlhub = utils.get_repo(args.mlhub)
    meta  = utils.get_repo_meta_data(mlhub)

    # Check preconditions.
    
    if model.endswith(EXT_MLM):
        msg = "{}please assist by implementing this command."
        msg = msg.format(APPX)
        print(msg, file=sys.stderr)
        sys.exit(1)

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
            msg = "\nYou can list available models with:\n\n  $ {} available.\n"
            msg = msg.format(CMD)
            print(msg, file=sys.stderr)
        sys.exit(1)

    if args.debug: print(DEBUG + "model file url is: " + url)

    # Ensure file to be downloaded has the expected filename extension.

    if not url.endswith(EXT_MLM):
        msg = "{}the below url is not a {} file. Malformed '{}' from the repository?\n  {}"
        msg = msg.format(APPX, EXT_MLM, META_YAML, url)
        print(msg, file=sys.stderr)
        sys.exit(1)

    # Further setup.
    
    init    = utils.create_init()
    mlmfile = url.split("/")[-1]
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

    zip = zipfile.ZipFile(local)
    zip.extractall(INIT_DIR)

    # Support either .yml or .yaml "cheaply". Should really try and except. 

    if (not os.path.exists(DESC_YAML)) and os.path.exists(DESC_YML):
        copyfile(os.path.join(path, DESC_YML), os.path.join(path, DESC_YAML))

    # Informative message about the size of the installed model.
    
    if not args.quiet:
        dsz = 0
        for (pth, dir, files) in os.walk(path):
            for f in files:
                tfilename = os.path.join(pth, f)
                dsz += os.path.getsize(tfilename)
        print("Extracted '{}' into\n'{}' ({:,} bytes).\n".
              format(mlmfile, local.split("_")[0], dsz))
            
    # Suggest next step. README or DOWNLOAD
    
    if not args.quiet:
        msg = "Model information is available:\n\n  $ {} readme {}\n"
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
    path  = INIT_DIR + model
    desc  = os.path.join(path, DESC_YAML)
   
    # Check that the model is installed.

    utils.check_model_installed(path)
    
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
    path   = INIT_DIR + model
    readme = os.path.join(path, README)

    # Check that the model is installed.

    utils.check_model_installed(path)
    
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
    path  = INIT_DIR + model
    desc  = os.path.join(path, DESC_YAML)

    # Check that the model is installed.

    utils.check_model_installed(path)
    
    # If DESC_YAML does not exist then throw an error.
    
    if not os.path.exists(desc):
        msg = "{}'{}' does not exist which suggests this model archive is broken."
        msg - msg.format(APPX, desc)
        print(msg, file=sys.stderr)
        sys.exit(1)

    info = yaml.load(open(desc, 'r'))

    msg = "The model '{}' ({})) supports the following commands:"
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
    """For now print the list of dependencies."""
    
    model = args.model
    path  = INIT_DIR + model
    desc  = os.path.join(path, DESC_YAML)
   
    # Check that the model is installed.

    utils.check_model_installed(path)

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

        info = yaml.load(open(desc, 'r'))
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
    path  = INIT_DIR + model

    param = " ".join(args.param)

    # Check that the model is installed.

    utils.check_model_installed(path)
    
    # If DESC_YAML does not exist then throw an error.
    
    if not os.path.exists(os.path.join(path, DESC_YAML)):
        msg = "{}'{}' does not exist."
        msg.format(APPX, DESC_YAML)
        print(msg, file=sys.stderr)
        sys.exit(1)

    desc = yaml.load(open(os.path.join(path, DESC_YAML), 'r'))
        
    language = desc["meta"]["language"]

    # Rscript => score.R; python => score.py etc.

    script  = desc["commands"][cmd]["script"].split(" ")[0] + " " + param
    command = "{} {}".format(language, script)
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
    
