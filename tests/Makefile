########################################################################
#
# Makefile for mlhub testing.
#
# Time-stamp: <Wednesday 2021-04-28 08:34:45 AEST Graham Williams>
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
mlhub testing:

  The tests are handled by ../Makefile.

  test		Run series of tests using exactly.
  testNNN	Run an individual test by number.
  actNNN	Run an individual with act but not assert.

endef
export HELP

help::
	@echo "$$HELP"

.PHONY: test
test:
	(cd ..; make $@)

.PHONY: testc
testc:
	(cd ..; make $@)

test%: 
	(cd ..; make $@)

act%:
	(cd ..; make $@)
