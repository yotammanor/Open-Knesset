==================================
Working on CSS and Documentation
==================================

CSS
=========

We're using LESS_ (no direct editing of CSS). If you'd like to contribute to the
design efforts:

Before first run, and only once, you'll need::

    git submodule init
    git submodule update

We recommend to use nvm to install the correct node version (so that all the developers get consistent css results)::

    install nvm, see: https://github.com/creationix/nvm
    then, run:
    $ cd OpenKnesset
    OpenKnesset$ nvm install

If you encounter problems using nvm, you can install the node another way, you need node in the version specified in .nvmrc file

Install less using the version specified in package.json::

    $ cd OpenKnesset
    OpenKnesset$ nvm use
    OpenKnesset$ npm install

Make your changes to the files in the ``less`` directory, and compile
(assuming you're in the ``Open-Knesset`` directory)::

    $ cd OpenKnsset
    OpenKnesset$ nvm use
    OpenKnesset$ npm run less

.. _Node.js: http://nodejs.org/
.. _LESS: http://lesscss.org/#-server-side-usage


Documentation
=================

Our documentation is written with Sphinx_, install it with the virtualenv
activated::

    pip install sphinx


.. _Sphinx: http://sphinx-doc.org/

Edit the relevant docs under the ``docs`` directory, and once done, run
``make html``. You'll have the resulting documentation in ``build/html``
directory.

We have 2 documentation directories:

* api --- API and Embedding for 3rd party apps/services developers
* devel --- Developer guide for the OpenKnesset project (TBD)

e.g: To work on the devel docs, edit the files under ``docs/devel/source``, once
ready to build::

    cd docs/devel
    make html

You'll have the result under::

    docs/devel/build/html

