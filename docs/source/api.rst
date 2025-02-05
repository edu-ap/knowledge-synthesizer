API Reference
============

This section provides detailed API documentation for the Knowledge Synthesizer package.

Synthesizer Class
---------------

.. autoclass:: knowledge_synthesizer.synthesizer.Synthesizer
   :members:
   :undoc-members:
   :show-inheritance:

CLI Module
---------

.. automodule:: knowledge_synthesizer.cli
   :members:
   :undoc-members:
   :show-inheritance:

Configuration
-----------

Model Selection
^^^^^^^^^^^^^

The following models are available for use:

.. code-block:: python

   models = {
       "1": {"name": "gpt-4"},
       "2": {"name": "gpt-4-turbo-preview"},
       "3": {"name": "gpt-3.5-turbo"}
   }

You can select a model either through the CLI interface or programmatically:

.. code-block:: python

   synthesizer = Synthesizer(model="gpt-4")

Pattern Management
---------------

Patterns are automatically fetched from the Fabric repository. You can also use custom patterns:

.. code-block:: python

   synthesizer = Synthesizer()
   synthesizer.add_custom_pattern(
       name="my_pattern",
       prompt="Your custom prompt here"
   )

Error Handling
------------

The package includes comprehensive error handling for:

* API rate limits
* Token limits
* Network issues
* Invalid inputs

Example error handling:

.. code-block:: python

   try:
       synthesizer.process_file("document.md")
   except RateLimitError:
       print("Rate limit exceeded. Please wait before trying again.")
   except TokenLimitError:
       print("Input too long for selected model.")

Advanced Usage
------------

For advanced usage scenarios and examples, please refer to the :doc:`usage` section. 