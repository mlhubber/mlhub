########################################################################
#
# Makefile for mlhub and the ml command line. 
#
########################################################################

APP=mlhubdev

# Version numbers
#   Major release
#   Minor update
#   Bug fix

VER=3.3.1

TAR_GZ = dist/$(APP)-$(VER).tar.gz

SOURCE = setup.py			\
	 README.md			\
	 setup.cfg			\
	 MANIFEST.in			\
	 LICENSE			\
	 mlhub/constants.py		\
	 mlhub/commands.py		\
	 mlhub/utils.py			\
	 mlhub/__init__.py		\
	 mlhub/bash_completion.d/ml.bash \
	 mlhub/scripts/dep/python.sh \
	 mlhub/scripts/dep/r.R \
	 mlhub/scripts/dep/system.sh \
	 mlhub/scripts/dep/mlhub.sh \
	 mlhub/scripts/convert_readme.sh \
	 mlhub/scripts/dep/utils.sh

BASH_COMPLETION = mlhub/bash_completion.d/ml.bash

INC_BASE    = $(HOME)/.local/share/make
INC_PANDOC  = $(INC_BASE)/pandoc.mk
INC_GIT     = $(INC_BASE)/git.mk
INC_AZURE   = $(INC_BASE)/azure.mk
INC_DOCKER  = $(INC_BASE)/docker.mk
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
ifneq ("$(wildcard $(INC_DOCKER))","")
  include $(INC_DOCKER)
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
	perl -pi -e 's|$(APP)_\d+.\d+.\d+|$(APP)_$(VER)|g' README.md

.PHONY: worthy
worthy:
	@echo "-------------------------------------------------------"
	git checkout worthy
	@echo "-------------------------------------------------------"

$(TAR_GZ): $(SOURCE)
	python3 setup.py sdist

.PHONY: pypi
pypi: README.md version $(TAR_GZ)
	twine upload $(TAR_GZ)

.PHONY: pypi.test
pypi.test: version $(TAR_GZ)
	twine upload --repository-url https://test.pypi.org/legacy/ dist/$(TAR_GZ)

.PHONY: dist
dist: version $(TAR_GZ)

.PHONY: dl03
dl03: dist
	rsync -avzh $(TAR_GZ) $@:

.PHONY: clean
clean:
	rm -f README.html

realclean:: clean
	rm -f mlhub_*.tar.gz
