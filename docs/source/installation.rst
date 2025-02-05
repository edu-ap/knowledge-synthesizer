Installation
============

Prerequisites
------------

Before installing Knowledge Synthesizer, ensure you have:

* Python 3.9 or higher
* pip (Python package installer)
* An OpenAI API key

Basic Installation
----------------

You can install Knowledge Synthesizer using pip:

.. code-block:: bash

   pip install knowledge-synthesizer

Development Installation
----------------------

For development purposes, you can clone the repository and install in editable mode:

.. code-block:: bash

   git clone https://github.com/edu-ap/knowledge-synthesizer.git
   cd knowledge-synthesizer
   pip install -e ".[dev]"

This will install all development dependencies as well.

Setting Up Your API Key
---------------------

You'll need to set up your OpenAI API key. There are two ways to do this:

1. Using a .env file (recommended):

   Create a file named `.env` in your project directory:

   .. code-block:: bash

      OPENAI_API_KEY=your-key-here

2. Using environment variables:

   .. code-block:: bash

      export OPENAI_API_KEY=your-key-here

Verifying Installation
--------------------

To verify that everything is working correctly:

.. code-block:: bash

   knowledge-synthesizer --version

This should display the version number of your installation.

Troubleshooting
-------------

Common Issues
^^^^^^^^^^^^

1. **ImportError: No module named 'knowledge_synthesizer'**
   
   - Ensure you're using the correct Python environment
   - Try reinstalling the package

2. **API Key Issues**
   
   - Check that your .env file is in the correct location
   - Verify the API key is valid
   - Ensure the environment variable is set correctly

Getting Help
^^^^^^^^^^

If you encounter any issues:

1. Check the :doc:`troubleshooting` section
2. Search existing GitHub issues
3. Create a new issue if needed 