########################################################################
#
# Makefile for mlhub and the ml command line. 
#
########################################################################

APP=mlhub

# Version numbers
#   Major release
#   Minor update
#   Bug fix

# VER=1.1.1 Support MLINIT environment variable. General cleanup.
# VER=1.1.2 Longer package names in listings.
# VER=1.1.3 Implement CLEAN and REMOVE.
# VER=1.1.4 Message before downloading the archive.
# VER=1.1.5 Explicitly use python3
# VER=1.1.6 REMOVE with no arg removes whole mlhub installed base.
# VER=1.1.7 Fix bug in general script execution with params.
# VER=1.1.8 Output format updates. Allow multiple configure scripts.
# VER=1.1.9 Format updates.
# VER=1.2.0 Add languages - one package supports multiple languages.
# VER=1.2.1 Add R_LIBS for local installed libraries.
# VER=1.2.2# Ignore R folder in INSTALLED.
# VER=1.2.3# Place R_LIBS within model folder.
# VER=1.2.4# Handle missing title in COMMANDS.
# VER=1.2.5# Allow for URL in INSTALL.
# VER=1.2.6# Check DISPLAY in MLHUB rather than model.
# VER=1.2.7# Check version overwrite before downloading. 
# VER=1.2.8# 20180919 Handle REMOVE when MLINIT does not exist.
# VER=1.3.0# 20180919 Re-engineer the whats-next management.
# VER=1.3.1# 20180921 Ensure yaml keys remain in same order as on file.
# VER=1.3.2# 20180921 COMMANDS output is now formatted.
# VER=1.3.5# 20180921 Try README.md for pypi
# VER=1.3.6# 20180924 Back to README.rst? Improve formatting.
# VER=1.3.9# 20180924 Get README.rst formatted on PyPi.
# VER=1.3.10# 20180925 Improve COMMANDS output.
# VER=1.4.0# 20180927 Auto-complete model names.
# VER=1.4.1# 20180930 Improve auto-complete of commands.
# VER=1.4.2# 20181015 Speed up auto-complete and automate setup.
# VER=1.4.3# 20181018 Handle languages more flexibly.
# VER=1.4.4# 20181020 Improve handling of score command.
# VER=1.4.5# 20181020 Add --version.
# VER=1.4.6# 20181024 Bug fix argparse handling
# VER=1.4.7# 20181024 Minor tab completion fix
# VER=1.4.8# 20181024 Bug fix for demo cmd
VER=1.4.9# 20181027 model version and model command help

TAR_GZ = dist/$(APP)-$(VER).tar.gz

BASH_COMPLETION = mlhub/bash_completion.d/ml.bash

INC_BASE    = .
INC_PANDOC  = $(INC_BASE)/pandoc.mk
INC_GIT     = $(INC_BASE)/git.mk
INC_AZURE   = $(INC_BASE)/azure.mk
INC_CLEAN   = $(INC_BASE)/clean.mk

define HELP
MLHUB Makefile

  Local targets:

  dist		Build the .tar.gz for distribution or pip install.
  mlhub		Update mlhub.ai with index and .tar.gz
  version	Update the version number across appropriate files.
  pypi 		Upload new package for pip install.

endef
export HELP

help::
	@echo "$$HELP"

ifneq ("$(wildcard $(INC_PANDOC))","")
  include $(INC_PANDOC)
endif
ifneq ("$(wildcard $(INC_GIT))","")
  include $(INC_GIT)
endif
ifneq ("$(wildcard $(INC_AZURE))","")
  include $(INC_AZURE)
endif
ifneq ("$(wildcard $(INC_CLEAN))","")
  include $(INC_CLEAN)
endif

.PHONY: mlhub
mlhub: version $(TAR_GZ) $(BASH_COMPLETION)
	chmod a+r $(TAR_GZ)
	rsync -avzh $(TAR_GZ) $(BASH_COMPLETION) mlhub.ai:webapps/mlhub2/

.PHONY: version
version:
	perl -pi -e "s|^    version='.*'|    version='$(VER)'|" setup.py 
	perl -pi -e 's|^VERSION = ".*"|VERSION = "$(VER)"|' mlhub/constants.py
	perl -pi -e 's|$(APP)_\d+.\d+.\d+|$(APP)_$(VER)|g' README.rst

$(TAR_GZ):
	python setup.py sdist

.PHONY: pypi
pypi: README.md version $(TAR_GZ)
	twine upload $(TAR_GZ)

.PHONY: pypi.test
pypi.test: version $(TAR_GZ)
	twine upload --repository-url https://test.pypi.org/legacy/ dist/$(TAR_GZ)

.PHONY: dist
dist: version $(TAR_GZ)

.PHONY: dsvm01
dsvm01: dist
	rsync -avzh $(TAR_GZ) dsvm01.southeastasia.cloudapp.azure.com:

.PHONY: clean
clean:
	rm -f README.html README.md

realclean:: clean
	rm -f mlhub_*.tar.gz
