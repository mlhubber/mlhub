########################################################################
#
# Makefile template for Version Control - git
#
# Copyright 2018 (c) Graham.Williams@togaware.com
#
# License: Creative Commons Attribution-ShareAlike 4.0 International.
#
########################################################################

define GIT_HELP
Support the usual git commands as make targets:

  info	  Identify the git repository;
  status  Status listing untracked files;
  qstatus A quieter status ignoring untracked files;
  push
  pull
  master  Checkout the master branch;
  dev     Checkout the dev branch;
  log
  flog	  Show the full log;
  diff
  vdiff	  Show a visual diff using meld.

endef
export GIT_HELP

help::
	@echo "$$GIT_HELP"

info:
	@echo "-------------------------------------------------------"
	git config --get remote.origin.url
	@echo "-------------------------------------------------------"

status:
	@echo "-------------------------------------------------------"
	git status
	@echo "-------------------------------------------------------"

qstatus:
	@echo "-------------------------------------------------------"
	git status --untracked-files=no
	@echo "-------------------------------------------------------"

push:
	@echo "-------------------------------------------------------"
	git push
	@echo "-------------------------------------------------------"

pull:
	@echo "-------------------------------------------------------"
	git pull
	@echo "-------------------------------------------------------"

master:
	@echo "-------------------------------------------------------"
	git checkout master
	@echo "-------------------------------------------------------"

dev:
	@echo "-------------------------------------------------------"
	git checkout dev
	@echo "-------------------------------------------------------"

log:
	@echo "-------------------------------------------------------"
	git --no-pager log --stat --max-count=10
	@echo "-------------------------------------------------------"

flog:
	@echo "-------------------------------------------------------"
	git --no-pager log
	@echo "-------------------------------------------------------"

diff:
	@echo "-------------------------------------------------------"
	git --no-pager diff --color
	@echo "-------------------------------------------------------"

vdiff:
	git difftool --tool=meld
