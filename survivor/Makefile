#######################################################################
#
# MLHub Book Makefile
#
# Time-stamp: <Tuesday 2021-03-16 09:22:19 AEDT Graham Williams>
#
# Copyright (c) Graham.Williams@togaware.com
#
# License: Creative Commons Attribution-ShareAlike 4.0 International.
#
########################################################################

APP=mlhub
VER=0.0.0

RSYNC   = rsync --archive --compress
TWUSER	= gjw
TWHOST	= mlhub.ai
TWLOGIN	= $(TWUSER)@$(TWHOST)
TWPATH	= webapps/$(APP)2/survivor/

########################################################################
# Makefile Support

INC_BASE    = $(HOME)/.local/share/make
INC_R       = $(INC_BASE)/r.mk
INC_PDF     = $(INC_BASE)/pdf.mk
INC_KNITR   = $(INC_BASE)/knitr.mk
INC_PANDOC  = $(INC_BASE)/pandoc.mk
INC_GIT     = $(INC_BASE)/git.mk
INC_AZURE   = $(INC_BASE)/azure.mk
INC_LATEX   = $(INC_BASE)/latex.mk
INC_CLEAN   = $(INC_BASE)/clean.mk

ifneq ("$(wildcard $(INC_R))","")
  include $(INC_R)
endif
ifneq ("$(wildcard $(INC_PDF))","")
  include $(INC_PDF)
endif
ifneq ("$(wildcard $(INC_KNITR))","")
  include $(INC_KNITR)
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
ifneq ("$(wildcard $(INC_LATEX))","")
  include $(INC_LATEX)
endif
ifneq ("$(wildcard $(INC_CLEAN))","")
  include $(INC_CLEAN)
endif

define HELP
$(APP):

  book     Build the gitbook HTML documents.
  preview  Load the book into the browser.

  chaNNN   Process only chapter NNN to html.
  pdfNNN   Process chapter NNN to PDF.

  install  Install to $(TWHOST):$(TWPATH)

endef
export HELP

help::
	@echo "$$HELP"

########################################################################
# BOOKDOWN 20210313

book:
	Rscript -e "bookdown::render_book('index.Rmd', 'bookdown::gitbook')"

preview:
	brave-browser _book/index.html

pdfbook:
	Rscript -e "bookdown::render_book('index.Rmd', 'bookdown::pdf_book')"

pdfview: pdfbook
	evince _book/_main.pdf

cha%: CHAPTER=$(wildcard cha_$*_*.Rmd)
cha%:
	Rscript -e "bookdown::preview_chapter(c('index.Rmd', '$(CHAPTER)'), 'bookdown::gitbook')"

pdf%: CHAPTER=$(wildcard cha_$*_*.Rmd)
pdf%:
	Rscript -e "bookdown::preview_chapter(c('index.Rmd', '$(CHAPTER)'), 'bookdown::pdf_book')"
	evince _book/_main.pdf &

install: realclean book
	rsync -vazh --exclude '_main.pdf' _book/ $(TWHOST):$(TWPATH)/
	ssh $(TWHOST) chmod -R go+rX $(TWPATH)/

clean::
	rm -f *.tmp _main.Rmd _main.pdf _main.tex

realclean::
	rm -rf _book/ _main_cache/ _main_files/
