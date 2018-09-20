========================
The Machine Learning Hub
========================

.. class:: center
	   
*--Under Development--*

Introduction
------------

The machine learning hub is an `open source project
<https://github.com/mlhubber/mlhub>`_ sharing `pre-built machine
learning models <https://github.com/mlhubber/mlmodels>`_. The models
are accessed and managed using the *ml* command from the *mlhub*
package.

Visit the `Repository Index <https://mlhub.ai/Packages.html>`_ on
`MLHub.ai <https://mlhub.ai/>`_ where the models themselves can be
browsed from the `main pool <https://mlhub.ai/pool/main/>`_.

Quick Start
-----------

The command line interface can be installed using `PyPi
<https://pypi.org/project/mlhub/>`_::

  $ pip3 install mlhub
  
Once installed you will be able to run the sample rain-tomorrow model
assuming that you have the free and open source `R statistical
software package <https://cran.r-project.org>`_ installed. The TL;DR
version is below. Note that you type the command ``ml ...`` and that
everything from the ``#`` to the end of the line is ignored (it's a
comment)::

  $ ml install   rain-tomorrow # Install the model named rain-tomorrow.
  $ ml demo      rain-tomorrow # Run the demonstration of the model
  $ ml display   rain-tomorrow # Graphical display of pre-built model.

The following commands are available and below is a brief description
of each command::

  $ ml                         # Show a usage message.
  $ ml available               # List of pre-buld models on the MLHub.
  $ ml installed               # List of pre-built models installed locally
  $ ml install   rain-tomorrow # Install the model named rain-tomorrow.
  $ ml readme    rain-tomorrow # View background information about the model.
  $ ml commands  rain-tomorrow # List of commands supported by the model.
  $ ml configure rain-tomorrow # Install required dependencies.
  $ ml demo      rain-tomorrow # Run the demonstration of the model
  $ ml print     rain-tomorrow # Textual summary of the model.
  $ ml display   rain-tomorrow # Graphical display of pre-built model.
  $ ml score     rain-tomorrow # Run model on your own data.

Different model packages will have different dependencies and these
will be installed by the *configure* command.
  
Quick Start: Azure DSVM
-----------------------

A particularly attractive and simple way to get started with exploring
the mlhub functionality is to fire up a `Ubuntu Data Science Virtual
Machine <https://aka.ms/dsvm>`_ (DSVM) on Azure for as little as USD10
per month for quite a small server or USD90 for a reasonable one.  You
can get free credit (USD200) from Microsoft to `trial the DSVM
<https://aka.ms/free>`_.

Using this virtual machine will save a lot of time compared with
setting up your own machine with the required dependencies, which of
course you can do if you wish as all the dependencies are open source.

To set up the virtual machine, with an Azure subscription log in to
the `portal <https://portal.azure.com/>`_ and add a new Data Science
Virtual Machine for Linux (Ubuntu). You need to provide a name (for
the virtual machine), a user name and a password, and then create a
new resource group and give it a name, and finally choose a
location. Go with all the defaults for everything else, except choose
a size to suit the budget (B1s is cheap though a D2s is a better
interactive experience). Note that you are only charged whilst the
machine is fired up so USD90 per month is no where near what you will
spend if you only fire up the server when you need.

Once the DSVM is set up go to its Overview page and click on DNS name
Configure and provide a name by which to refer to the server publicly
(e.g., myml.westus2.cloudapp.azure.com).

We now have a server ready to showcase the pre-built Machine Learning
models. There are several options to connect to the server but a
recommended one is to use `X2Go <http://x2go.org/>`_ which supports
Linux, Windows, and Mac. Install it and point it to your server (e.g.,
myml.westus2.cloudapp.azure.com) in the setup.

Connect to the DSVM.  Close the Firefox window that pops up. Click on
the terminal icon down the bottom, and you are ready to go::

  $ pip install mlhub
  $ ml
  $ ml available

etc.
  
Pre-Built Model Archives
------------------------

A model is a zip file archived as .mlm files and hosted in a
repository. The public repository is `<https://mlhub.ai>`_. The *ml*
command can install the pre-built model locally, ready to run a demo,
to print and display the model, and to score new data using the
model. Some models provide ability to retrain the model with user
provided data.

Contributing Models to ML Hub
-----------------------------

Anyone is welcome to contribute a pre-built model package to ML
Hub. Please submit a pull request through
`github<https://github.com/mlhubber/mlmodels>`_.

Installing Pip3
---------------

On Ubuntu this is as simple as::

  $ sudo apt install python3-pip

Alternative pip Install
-----------------------

Depending on your setup of pip, you may need to use::

  $ pip3 install mlhub

The executable may be placed into ``~/.local/bin`` which will need to
be on your path. Edit your shell startup which is either ``.profile``
or ``.bashrc``, etc::

  PATH="$HOME/.local/bin:$PATH"
  
Alternative Install
-------------------

A tar.gz containing the mlhub package and the command line interface
is available as `mlhub_1.3.0.tar.gz
<https://mlhub.ai/dist/mlhub_1.3.0.tar.gz>`_ within the `distribution
<https://mlhub.ai/dist/>`_ folder of the MLHub.

To install from the tar.gz file::
  
  $ wget https://mlhub.ai/dist/mlhub_1.3.0.tar.gz
  $ pip install mlhub_1.3.0.tar.gz
  $ ml

Or extract the above downloaded .tar.gz and install::

  $ wget https://mlhub.ai/dist/mlhub_1.3.0.tar.gz
  $ tar xvf mlhub_1.3.0.tar.gz
  $ cd mlhub
  $ python3 setup.py install --user


Contributions
-------------

The open source mlhub command line tool (ml) and sample models are
being hosted on `GitHub <https://github.com/mlhubber>`_ and contributions to
both the command line tool and contributions of new open source
pre-built machine learning models are most welcome. Feel free to
submit pull requests.
