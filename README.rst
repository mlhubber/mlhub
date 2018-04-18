========================
The Machine Learning Hub
========================

The machine learning hub is an open source project and resource for
distributing pre-built machine learning models. The models are
accessed and managed using the *ml* command from the *mlhub* package.

The models collected in the ML Hub archive are listed in
`<https://mlhub.ai/Packages.yaml>`_ and can be browsed from
`<https://mlhub.ai/pool/>`_.

The command line tool source package is available as
`<https://mlhub.ai/dist/mlhub_1.0.4.tar.gz>`_ within
`<https://mlhub.ai/dist/>`_

To install::

  $ wget https://mlhub.ai/dist/mlhub_1.0.4.tar.gz
  $ pip install mlhub_1.0.4.tar.gz
  $ ml

Once installed you will be able to run the sample rain-tomorrow
model::

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
  
A model is a zip file archived as .mlm files and hosted in a
repository. The public repository is `<https://mlhub.ai>`_. The *ml*
command can install the pre-built model locally, ready to run a demo,
to print and display the model, and to score new data using the
model. Some models provide ability to retrain the model with user
provided data.

