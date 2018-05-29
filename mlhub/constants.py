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

#------------------------------------------------------------------------
# The default ML Hub can be overriden by an environment variable or by
# the command line option --mlhub.
#------------------------------------------------------------------------

MLHUB  = "https://mlhub.ai/"
if "MLHUB" in os.environ:
    # The following adds a trainling "/" as assumed in the code.
    MLHUB = os.path.join(os.getenv("MLHUB"), "")

HUB_PATH = "pool/main/"

#------------------------------------------------------------------------
# The MLINIT contains all of the locally installed models.
#------------------------------------------------------------------------

MLINIT = os.path.expanduser("~/.mlhub/")
if "MLINIT" in os.environ:
    # The following adds a trainling "/" as assumed in the code.
    MLINIT = os.path.join(os.getenv("MLINIT"), "")


#------------------------------------------------------------------------
# Application information.
#------------------------------------------------------------------------

APP  = "mlhub"            # The application name.
APPX = "{}: ".format(APP) # For error messages.
CMD  = "ml"               # The command line tool.

EXT_MLM  = ".mlm"         # Archive filename extension
EXT_AIPK = ".aipk"        # Backward compatibility

VERSION = "1.1.2" # DO NOT MODIFY. Managed from ../Makefile.

USAGE = """Usage: {} [<options>] <command> [<command options>] [<model>]

Access machine learning models from the ML Hub.

Global commands:

  available            List the models available from the repository.
  installed            List the models installed locally.
  clean                Remove any downloaded {} files from {}.

  install    <model>   Install the model.
  readme     <model>   View the model's README.
  commands   <model>   List the commands supported by the model.
  configure  <model>   Configure the model's dependencies.
  demo       <model>   Demostrate the model in action.
  print      <model>   Technical information about the model.
  display    <model>   Visual presentaiton of the model.
  remove    [<model>]  Remove a model or remove all models.

The ML Hub repository is '{}'.

Models are installed into '{}'.

This is version {} of {}."""

# Filenames.

README    = "README.txt"

DESC_YAML = "DESCRIPTION.yaml"
META_YAML = "Packages.yaml"

DESC_YML = "DESCRIPTION.yml"
META_YML = "Packages.yml"

# Debugging

debug = False
DEBUG = "--> " + APP + ": debug: "
