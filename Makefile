########################################################################
#
# Makefile for mlhub and the ml command line. 
#
########################################################################

APP=mlhub

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
VER=1.2.7# Check version overwrite before downloading. 

APP_FILES = 			\
	setup.py		\
	setup.cfg		\
	mlhub/__init__.py	\
	mlhub/commands.py	\
	mlhub/utils.py		\
	mlhub/constants.py	\
	README.rst		\
	LICENSE	

TAR_GZ = $(APP)_$(VER).tar.gz

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
mlhub: version $(TAR_GZ)
	chmod a+r $(TAR_GZ)
	rsync -avzh $(TAR_GZ) mlhub.ai:webapps/mlhub2/

.PHONY: version
version:
	perl -pi -e "s|^    version='.*'|    version='$(VER)'|" setup.py 
	perl -pi -e 's|^VERSION = ".*"|VERSION = "$(VER)"|' mlhub/constants.py
	perl -pi -e 's|$(APP)_\d+.\d+.\d+|$(APP)_$(VER)|g' README.rst

$(TAR_GZ): $(APP_FILES)
	tar cvzf $@ $^

.PHONY: pypi
pypi: version
	python setup.py sdist
	twine upload dist/$(APP)-$(VER).tar.gz

.PHONY: pypi.test
pypi.test: version
	python setup.py sdist
	twine upload --repository-url https://test.pypi.org/legacy/ dist/$(APP)-$(VER).tar.gz

.PHONY: dist
dist: version $(TAR_GZ)

.PHONY: dsvm01
dsvm01: dist
	rsync -avzh $(TAR_GZ) dsvm01.southeastasia.cloudapp.azure.com:

.PHONY: clean
clean:
	rm -f README.html

realclean:: clean
	rm -f mlhub_*.tar.gz
