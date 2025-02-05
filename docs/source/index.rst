.. Knowledge Synthesizer documentation master file, created by
   sphinx-quickstart on Wed Feb  5 21:51:38 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Knowledge Synthesizer's documentation!
==========================================

Knowledge Synthesizer is a Python tool that integrates with Daniel Miessler's Fabric project, allowing you to apply its powerful AI patterns to your local content.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api
   contributing
   changelog
   security

Features
--------

* Direct integration with Fabric's pattern repository
* Support for multiple OpenAI models (GPT-4, GPT-4 Turbo, GPT-3.5)
* Interactive pattern selection from Fabric's collection
* Configurable input/output formats
* Rate limiting and error handling
* Automated GitHub-based pattern updates

Quick Start
----------

Installation
^^^^^^^^^^^

.. code-block:: bash

   pip install knowledge-synthesizer

Basic Usage
^^^^^^^^^^

.. code-block:: python

   from knowledge_synthesizer import Synthesizer

   synthesizer = Synthesizer()
   synthesizer.process_file("your_document.md")

For more detailed information, check out the :doc:`usage` section.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

