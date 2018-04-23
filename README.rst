========================
The Machine Learning Hub
========================

**Under Development**

Introduction
------------

The machine learning hub is an open source project and resource for
sharing pre-built machine learning models. The models are accessed and
managed using the *ml* command from the *mlhub* package.

The models collected in the ML Hub archive are listed in
`<https://mlhub.ai/Packages.yaml>`_ and the models themselves can be
browsed from `<https://mlhub.ai/pool/main/>`_.

Quick Start
-----------

The command line interface can be installed using PyPi::

  $ pip install mlhub

Once installed you will be able to run the sample rain-tomorrow
model::

  $ ml
  $ ml available
  $ ml installed
  $ ml install   rain-tomorrow
  $ ml readme    rain-tomorrow
  $ ml commands  rain-tomorrow
  $ ml configure rain-tomorrow
  $ ml demo      rain-tomorrow
  $ ml print     rain-tomorrow
  $ ml display   rain-tomorrow
  $ ml score     rain-tomorrow

Alternative Install
-------------------

A tar.gz containing the mlhub package and the command line interface
is available as `<https://mlhub.ai/dist/mlhub_1.0.12.tar.gz>`_ within
`<https://mlhub.ai/dist/>`_

To install from the tar.gz file::
  
  $ wget https://mlhub.ai/dist/mlhub_1.0.12.tar.gz
  $ pip install mlhub_1.0.12.tar.gz
  $ ml


Pre-Built Model Archives
------------------------

A model is a zip file archived as .mlm files and hosted in a
repository. The public repository is `<https://mlhub.ai>`_. The *ml*
command can install the pre-built model locally, ready to run a demo,
to print and display the model, and to score new data using the
model. Some models provide ability to retrain the model with user
provided data.

Contributions
-------------

The open source mlhub command line tool (ml) and sample models are
being hosted on `<https://github.com/mlhubber>`_ and contributoins to
both the command line tool and contributions of new open source
pre-built machine learning models are most welcome. Feel free to
submit pull requests.
