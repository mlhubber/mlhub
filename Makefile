########################################################################
#
# Makefile for mlhub and the ml command line. 
#
# Time-stamp: <Tuesday 2021-04-27 08:29:28 AEST Graham Williams>
#
# Copyright (c) Graham.Williams@togaware.com
#
# License: Creative Commons Attribution-ShareAlike 4.0 International.
#
########################################################################

# App version numbers
#   Major release
#   Minor update
#   Bug fix

APP=mlhub
VER=3.7.10
DATE=$(shell date +%Y-%m-%d)

TAR_GZ = dist/$(APP)-$(VER).tar.gz

BASH_COMPLETION = $(APP)/bash_completion.d/ml.bash

SOURCE = setup.py			\
	 docs/README.md			\
	 setup.cfg			\
	 MANIFEST.in			\
	 LICENSE			\
	 mlhub/constants.py		\
	 mlhub/commands.py		\
	 mlhub/utils.py			\
	 mlhub/pkg.py			\
	 mlhub/__init__.py		\
	 mlhub/bash_completion.d/ml.bash \
	 mlhub/scripts/dep/python.sh \
	 mlhub/scripts/dep/r.R \
	 mlhub/scripts/dep/system.sh \
	 mlhub/scripts/dep/mlhub.sh \
	 mlhub/scripts/convert_readme.sh \
	 mlhub/scripts/dep/utils.sh

INC_BASE    = $(HOME)/.local/share/make
INC_R       = $(INC_BASE)/r.mk
INC_PANDOC  = $(INC_BASE)/pandoc.mk
INC_GIT     = $(INC_BASE)/git.mk
INC_AZURE   = $(INC_BASE)/azure.mk
INC_DOCKER  = $(INC_BASE)/docker.mk
INC_CLEAN   = $(INC_BASE)/clean.mk

ifneq ("$(wildcard $(INC_CLEAN))","")
  include $(INC_CLEAN)
endif
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
ifneq ("$(wildcard $(INC_R))","")
  include $(INC_R)
endif

define HELP
mlhub:

  install	Local install for dev testing cycle.
  version	Update the version number across appropriate files.
  pypi 		Upload new package for pip install.
  dist		Build the .tar.gz for distribution or pip install.
  mlhub		Update mlhub.ai with index and .tar.gz

  test		Run series of tests using exactly.
  testNNN	Run an individual test by number.
  actNNN	Run an individual with act but not assert.

endef
export HELP

help::
	@echo "$$HELP"

.PHONY: mlhub
mlhub: version $(TAR_GZ) $(BASH_COMPLETION)
	chmod a+r $(TAR_GZ)
	rsync -avzh $(TAR_GZ) $(BASH_COMPLETION) mlhub.ai:webapps/mlhub2/

.PHONY: version
version:
	sed -i -e "s|^    version='.*'|    version='$(VER)'|" setup.py 
	sed -i -e 's|^VERSION = ".*"|VERSION = "$(VER)"|' mlhub/constants.py
	sed -i -e 's|$(APP)_\d+.\d+.\d+|$(APP)_$(VER)|g' docs/README.md
	sed -i -e 's|^Version: .*|Version: $(VER)|' DESCRIPTION
	sed -i -e 's|^Date: .*|Date: $(shell date +%Y-%m-%d)|' DESCRIPTION

.PHONY: worthy
worthy:
	@echo "-------------------------------------------------------"
	git checkout worthy
	@echo "-------------------------------------------------------"

logo-mlhub.png: logo-mlhub.svg
	convert $^ -resize 256x256 -transparent white -negate -fuzz 40% -fill '#ff9966' -opaque white $@

favicon.ico: logo-mlhub.png
	convert $^ -define icon:auto-resize="256,128,96,64,48,32,16" $@

favicon.install: favicon.ico
	scp $^ togaware.com:webapps/mlhub2/
	ssh togaware.com chmod a+r webapps/mlhub2/$^

$(TAR_GZ): $(SOURCE)
	python3 setup.py sdist

.PHONY: tgz
tgz: $(TAR_GZ)

.PHONY: pypi
pypi: docs/README.md version tgz 
	twine upload $(TAR_GZ)

.PHONY: pypi.test
pypi.test: version $(TAR_GZ)
	twine upload --repository-url https://test.pypi.org/legacy/ dist/$(TAR_GZ)

.PHONY: dist
dist: version $(TAR_GZ)

.PHONY: dl03
dl03: dist
	rsync -avzh $(TAR_GZ) $@:

.PHONY: test
test:
	PYTHONPATH=$(PWD) exactly suite tests

.PHONY: testc
testc:
	PYTHONPATH=$(PWD) exactly suite tests/curated.suite

test%: TEST=$(wildcard tests/$*_*.case)
test%: $(TEST)
	PYTHONPATH=$(PWD) exactly $(TEST)

act%: TEST=$(wildcard tests/$*_*.case)
act%: $(TEST)
	PYTHONPATH=$(PWD) exactly $(TEST) --act

DESTDIR ?= /home/$(USER)
PREFIX ?= /.local

LIBDIR = $(DESTDIR)$(PREFIX)/lib/python3.8/site-packages/$(APP)

install: version
	rsync -avzh $(APP)/  $(LIBDIR)/

.PHONY: clean
clean:
	rm -f docs/README.html tests/*~

realclean:: clean
	rm -f mlhub_*.tar.gz favicon.ico logo-mlhub.png 
