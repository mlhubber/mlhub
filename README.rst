========================
The Machine Learning Hub
========================

**This site is under development.**

The machine learning hub is an open source project and resource for
distributing pre-built machine learning models. The models are
accessed and managed using the *ml* command from the *mlhub* package.

The models collected in the ML Hub archive are listed in
`<https://mlhub.ai/Packages.yaml>`_ and can be browsed from
`<https://mlhub.ai/pool/>`_.

The command line tool source package is available as
`<https://mlhub.ai/dist/mlhub_1.0.12.tar.gz>`_ within
`<https://mlhub.ai/dist/>`_

To install using PyPi::

  $ pip install mlhub

To install from the tar.gz file::
  
  $ wget https://mlhub.ai/dist/mlhub_1.0.12.tar.gz
  $ pip install mlhub_1.0.12.tar.gz
  $ ml

Once installed you will be able to run the sample rain-tomorrow
model::

  $ ml
  $ ml available
  $ ml installed
  $ ml install   rain-tomorrow
  $ ml readme    rain-tomorrow
  $ ml license   rain-tomorrow
  $ ml commands  rain-tomorrow
  $ ml configure rain-tomorrow
  $ ml demo      rain-tomorrow
  $ ml print     rain-tomorrow
  $ ml display   rain-tomorrow
  $ ml score     rain-tomorrow
  $ ml donate    rain-tomorrow
  
A model is a zip file archived as .mlm files and hosted in a
repository. The public repository is `<https://mlhub.ai>`_. The *ml*
command can install the pre-built model locally, ready to run a demo,
to print and display the model, and to score new data using the
model. Some models provide ability to retrain the model with user
provided data.

If you find the model useful, either as is to score your own data or
as a learning experience, please consider donating to the model's
author through the **donate** command.

The open source mlhub command line tool (ml) and sample models are
being hosted on `<https://github.com/mlhubber>`_ and contributoins to
both the command line tool and contributions of new open source
pre-built machine learning models are most welcome. Feel free to
submit pull requests.
