########################################################################
#
# Makefile for mlhub and the ml command line. 
#
########################################################################

APP=mlhub
VER=1.1.1# Support MLINIT environment variable. General cleanup.
VER=1.1.2# Longer package names in listings.
VER=1.1.3# Implement CLEAN and REMOVE.
VER=1.1.4# Message before downloading the archive.
VER=1.1.5# Explicitly use python3
VER=1.1.6# REMOVE with no arg removes whole mlhub installed base.

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
mlhub: version README.html $(TAR_GZ)
	chmod a+r README.html $(TAR_GZ)
	rsync -avzh README.html root@mlhub.ai:/var/www/html/index.html
	rsync -avzh $(TAR_GZ) root@mlhub.ai:/var/www/html/dist/

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

.PHONY: dist
dist: version $(TAR_GZ)

.PHONY: dsvm01
dsvm01: dist
	rsync -avzh $(TAR_GZ) dsvm01.southeastasia.cloudapp.azure.com:

.PHONY: clean
clean:
	rm -f README.html
