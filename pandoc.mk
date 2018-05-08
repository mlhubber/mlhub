########################################################################
#
# Makefile template for Document Format Conversion - pandoc
#
# Copyright 2018 (c) Graham.Williams@togaware.com
#
# License: Creative Commons Attribution-ShareAlike 4.0 International.
#
########################################################################

# I think the geometry for LaTeX should be a4 rather than a4paper to
# work with newer LaTeX. Should only need lang which pandoc should
# underneath also set babel-lang but that does not seem to be working
# 20171230 (reference man page).

PANDOC_PDF_OPTIONS=-V urlcolor=cyan -V geometry=a4paper -V lang=british -V babel-lang=british --number-sections
PANDOC_TEX_OPTIONS=$(PANDOC_PDF_OPTIONS) --standalone

PANDOC_CSS=pandoc.css
PANDOC_HTML_OPTIONS=--standalone --self-contained
ifneq ("$(wildcard $(PANDOC_CSS))","")
  PANDOC_HTML_OPTIONS := $(PANDOC_HTML_OPTIONS) --include-in-header=$(PANDOC_CSS)
endif

define PANDOC_HELP
Conversion of document formats using pandoc:

  Inpute formats:
    org   Emacs org mode (the original);
    rst   Attempt to improve markdown;
    md    Mardown documents;

  Output foramts:
    html
    pdf
    view  View the generated PDF document.

Example:

  $ make README.view  # Generate and display .pdf from .org.

Default conversion options:

  PDF:  $(PANDOC_PDF_OPTIONS)
  TEX:  $(PANDOC_TEX_OPTIONS)
  HTML: $(PANDOC_HTML_OPTIONS)

endef
export PANDOC_HELP

help::
	@echo "$$PANDOC_HELP"

%.txt: %.rst
	pandoc $< -o $@

%.txt: %.md
	pandoc $< -o $@

%.docx: %.org
	pandoc $(PANDOC_PDF_OPTIONS) $< -o $@

%.html: %.org
	pandoc -o $@ $<

%.html: %.rst
	pandoc $(PANDOC_HTML_OPTIONS) -o $@ $<

%.tex: %.org
	pandoc $(PANDOC_TEX_OPTIONS) $< -o $@

%.tex: %.rst
	pandoc $(PANDOC_TEX_OPTIONS) $< -o $@

%.pdf: %.org
	pandoc $(PANDOC_PDF_OPTIONS) $< -o $@

%.pdf: %.rst
	pandoc $(PANDOC_PDF_OPTIONS) $< -o $@

%.pdf: %.md
	pandoc $(PANDOC_PDF_OPTIONS) $< -o $@

%.view: %.pdf
	atril $<

