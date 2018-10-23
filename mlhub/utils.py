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
import yaml
import yamlordereddictloader
import urllib.request
import platform
import subprocess

from mlhub.constants import (
    APPX,
    MLINIT,
    CMD,
    MLHUB,
    META_YAML,
    META_YML,
    DESC_YAML,
    DESC_YML,
    debug,
    DEBUG,
    USAGE,
    EXT_MLM,
    VERSION,
    APP,
    COMMANDS,
    COMPLETION_DIR,
    COMPLETION_COMMANDS,
    COMPLETION_MODELS,
)

def print_usage():
    print(CMD)
    print(USAGE.format(CMD, EXT_MLM, MLINIT, MLHUB, MLINIT, VERSION, APP))

def create_init():
    """Check if the init dir exists and if not then create it."""

    if not os.path.exists(MLINIT): os.makedirs(MLINIT)

    return(MLINIT)

def update_completion_list(completion_file, new_words):
    """Update specific completion list.
    Args:
        completion_file (str): full path of the completion file
        new_words (set): set of new words
    """

    if not os.path.exists(COMPLETION_DIR):
        os.makedirs(COMPLETION_DIR)

    if os.path.exists(completion_file):
        with open(completion_file, 'r') as file:
            old_words = {line.strip() for line in file if line.strip()}

        models = old_words | new_words
    else:
        models = new_words

    with open(completion_file, 'w') as file:
        file.write('\n'.join(models))

def get_completion_list(completion_file):
    """Get the list of available words from cached completion file."""

    words = set()
    if os.path.exists(completion_file):
        with open(completion_file) as file:
            words = {line.strip() for line in file if line.strip()}

    print('\n'.join(words))

def get_repo(repo):
    """Determine the repository to use: command line, environment, default."""

    if repo is None:
        repo = MLHUB
    else:
        repo = os.path.join(repo, "") # Ensure trailing slash.

    return repo

def get_repo_meta_data(repo):
    """Read the repositories meta data file and return as a list."""

    try:
        url  = repo + META_YAML
        meta = list(yaml.load_all(urllib.request.urlopen(url).read()))
    except:
        try: 
            url  = repo + META_YML
            meta = list(yaml.load_all(urllib.request.urlopen(url).read()))
        except:
            msg = """Cannot access the Internet.

To list the models available from an ML Hub you will need an Internet connection.

You can list the models already installed locally with:

  $ ml installed
"""
            print(msg, file=sys.stderr)
            sys.exit()
        
    return(meta)

def print_meta_line(entry):
    name    = entry["meta"]["name"]
    version = entry["meta"]["version"]
    try:
        title   = entry["meta"]["title"]
    except:
        title   = entry["meta"]["description"]

    # One line message.

    MAX_TITLE = 24
    MAX_DESCR = 44
    
    if len(title) > MAX_DESCR:
        long = "..."
    else:
        long = ""

    FORMATTER = "{0:<TITLE.TITLE} {1:^6} {2:<DESCR.DESCR}{3}".replace("TITLE", str(MAX_TITLE)).replace("DESCR", str(MAX_DESCR))
    print(FORMATTER.format(name, version, title, long))

#------------------------------------------------------------------------
# CHECK MODEL INSTALLED
    
def check_model_installed(model):

    path = MLINIT + model
    if not os.path.exists(path):
        model = os.path.basename(path)
        msg = """{}model '{}' is not installed ({}).

Check for the model name amongst those installed:

  $ {} installed

Models can be installed from the ML Hub:

  $ {} install {}

Available pakages on the ML Hub can be listed with:

  $ {} available
"""
        msg = msg.format(APPX, model, MLINIT, CMD, CMD, model, CMD)
        print(msg, file=sys.stderr)
        sys.exit(1)
        
    return(True)

#-----------------------------------------------------------------------
# LOAD DESCRIPTION

def load_description(model):

    desc = os.path.join(MLINIT, model, DESC_YAML)
    if os.path.exists(desc):
        entry = yaml.load(open(desc), Loader=yamlordereddictloader.Loader)
    else:
        desc = os.path.join(MLINIT, model, DESC_YML)
        if os.path.exists(desc):
            entry = yaml.load(open(desc), Loader=yamlordereddictloader.Loader)
        else:
            msg = "{}no '{}' found for '{}'."
            msg = msg.format(APPX, DESC_YAML, model)
            print(msg, file=sys.stderr)
            sys.exit(1)
    return(entry)
    
#-----------------------------------------------------------------------
# RUN CONFIGURE SCRIPT

def configure(path, script, quiet):
    """Run the provided configure scripts and handle errors and output."""

    configured = False
    
    # For now only tested/working with Ubuntu
    
    if platform.dist()[0] in set(['debian', 'Ubuntu']):
        conf = os.path.join(path, script)
        if os.path.exists(conf):
            interp = interpreter(script)
            if not quiet:
                msg = "Configuring using '{}'...".format(conf)
                print(msg)
            cmd = "{} {}".format(interp, script)
            proc = subprocess.Popen(cmd, shell=True, cwd=path, stderr=subprocess.PIPE)
            output, errors = proc.communicate()
            if proc.returncode != 0:
                print("An error was encountered:\n")
                print(errors.decode("utf-8"))
            configured = True

    return(configured)

#-----------------------------------------------------------------------
# DETERMINE THE CORRECT INTERPRETER FOR THE GIVEN SCRIPT NAME

def interpreter(script):
    
    (root, ext) = os.path.splitext(script)
    ext = ext.strip()
    if ext == ".sh":
        interpreter = "bash"
    elif ext == ".R":
        interpreter = "R_LIBS=./R Rscript"
    elif ext == ".py":
        interpreter = "python3"
    else:
        msg = "Could not determine an interpreter for extension '{}'".format(ext)
        print(msg, file=sys.stderr)
        sys.exit()

    return(interpreter)

#-----------------------------------------------------------------------
# ADD SUBCOMMAND

class SubCmdAdder(object):
    """Add the subcommands described in <commands> into <subparsers> with
corresponding functions defined in <module>."""

    def __init__(self, subparsers, module, commands):
        """
        Args:
            subparsers (argparse.ArgumentParser): to which the subcommand is added.
            module: the module which defines the actual function for the subcommand.
            commands (dict): meta info for the subcommand.
        """
        self.subparsers = subparsers
        self.module = module
        self.commands = commands

    def add_subcmd(self, subcommand):
        """Add <subcommand> to subparsers."""
    
        cmd_meta = self.commands[subcommand]
        parser = self.subparsers.add_parser(
            subcommand,
            aliases=cmd_meta.get('alias', ()),
            description=cmd_meta['description'],
        )
    
        if 'argument' in cmd_meta:
            args = cmd_meta['argument']
            for name in args:
                parser.add_argument(name, **args[name])
    
        if 'func' in cmd_meta:
            parser.set_defaults(func=getattr(self.module, cmd_meta['func']))

    def add_allsubcmds(self):
        """Add all subcommands described in <self.commands> into <self.subparsers>."""
        for cmd in self.commands:
            self.add_subcmd(cmd)

#-----------------------------------------------------------------------
# ADD GLOBAL OPTIONS ARGUMENT

class OptionAdder(object):
    """Add the global options described in <options> into <parser>."""

    def __init__(self, parser, options):
        self.parser = parser
        self.options = options

    def add_option(self, option):
        opt = self.options[option]
        self.parser.add_argument(option, **opt)

    def add_alloptions(self):
        for opt in self.options:
            self.add_option(opt)

# -----------------------------------------------------------------------
# DROP THE PERIOD AFTER A SENTENCE

def dropdot(sentence):
    import re
    return(re.sub("\.$", "", sentence))

# -----------------------------------------------------------------------
# DROP TRAINLING NEWLINES

def drop_newline(paragraph):
    import re
    return(re.sub("\n$", "", paragraph))

# -----------------------------------------------------------------------
# LOWERCASE THE FIRST LETTER OF A SENTENCE

def lower_first_letter(sentence):
    return(sentence[:1].lower() + sentence[1:] if sentence else '')


#-----------------------------------------------------------------------
# SUGGEST NEXT STEP FOR COMMAND 

def print_next_step(current, description={}, scenario=None, model=''):
    """Print next step suggestions for the command.

    Args:
        current (str): the command needs to be given next step suggestion.
        description(dict): yaml object from DESCRIPTION.yaml
        scenario (str): certain scenario for the next step.
        model (str): the model name if needed.
    """

    if description == {}:

        # Use the order for common commands

        if 'next' not in COMMANDS[current]:
            return

        steps = COMMANDS[current]['next']

        if scenario != None:
            steps = steps[scenario]

        for next in steps:
            meta = COMMANDS[next]
    
            # If there is customized suggestion, use it; otherwise
            # generate from description.

            if 'argument' in meta and model == '':
                model = '<model>'

            msg = meta.get('suggestion',
                           "\nTo " + lower_first_letter(meta['description']) + ":"
                           "\n\n  $ {} {} {}")
            msg = msg.format(CMD, next, model)
            print(msg)
    else:

        # Use the order in DESCRIPTION.yaml

        avail_cmds = list(description['commands'])

        try:
            next_index = avail_cmds.index(current) + 1 if current != 'commands' else 0
        except:
            # The command is not described in DESCRIPTION.yaml, ignore it.
            next_index = len(avail_cmds)

        if next_index < len(avail_cmds):
            next = avail_cmds[next_index]
            next_meta = description['commands'][next]

            if type(next_meta) is str:
                msg = dropdot(lower_first_letter(next_meta))
            else:
                # Handle malformed DESCRIPTION.yaml like
                # --
                # commands:
                #   print:
                #     description: print a textual summary of the model
                #   score:
                #     equired: the name of a CSV file containing a header and 6 columns
                #     description: apply the model to a supplied dataset

                msg = next_meta.pop('description', None)

            if msg is not None:
                msg = "\nTo " + msg
            else:
                msg = "You may try"
            msg += ":\n\n  $ {} {} {}"
            msg = msg.format(CMD, next, model)
        else:
            msg = "\nThank you for exploring the '{}' model.".format(model)

        print(msg)

    print("")
