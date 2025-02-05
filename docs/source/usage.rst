Usage Guide
===========

This guide will help you get started with Knowledge Synthesizer and show you how to use its main features.

Basic Usage
----------

Command Line Interface
^^^^^^^^^^^^^^^^^^

The simplest way to use Knowledge Synthesizer is through its command-line interface:

.. code-block:: bash

   # Process a single file
   knowledge-synthesizer document.md

   # Process all markdown files in a directory
   knowledge-synthesizer docs/

   # Process files recursively
   knowledge-synthesizer docs/ -r

   # Specify a particular pattern
   knowledge-synthesizer document.md --pattern summary

Python API
^^^^^^^^

You can also use Knowledge Synthesizer programmatically:

.. code-block:: python

   from knowledge_synthesizer import Synthesizer

   # Initialize the synthesizer
   synthesizer = Synthesizer()

   # Process a single file
   synthesizer.process_file("document.md")

   # Process multiple files
   synthesizer.process_files(["doc1.md", "doc2.md"])

   # Process a directory
   synthesizer.process_directory("docs/")

Advanced Features
--------------

Custom Patterns
^^^^^^^^^^^^

You can create and use custom patterns:

.. code-block:: python

   # Define a custom pattern
   custom_pattern = {
       "name": "technical_review",
       "description": "Technical code review with security focus",
       "prompt": "Analyze this code from a security perspective..."
   }

   # Add the pattern
   synthesizer.add_custom_pattern(**custom_pattern)

   # Use the custom pattern
   synthesizer.process_file("code.py", pattern="technical_review")

Model Selection
^^^^^^^^^^^^

Choose different OpenAI models based on your needs:

.. code-block:: python

   # Use GPT-4
   synthesizer = Synthesizer(model="gpt-4")

   # Use GPT-4 Turbo
   synthesizer = Synthesizer(model="gpt-4-turbo-preview")

   # Use GPT-3.5 Turbo
   synthesizer = Synthesizer(model="gpt-3.5-turbo")

Output Formats
^^^^^^^^^^^

Control how the synthesized content is saved:

.. code-block:: python

   # Save as markdown
   synthesizer.process_file("input.md", output_format="md")

   # Save as JSON
   synthesizer.process_file("input.md", output_format="json")

   # Custom output directory
   synthesizer.process_file("input.md", output_dir="synthesized/")

Batch Processing
^^^^^^^^^^^^^

Process multiple files efficiently:

.. code-block:: python

   # Process all markdown files in a directory
   synthesizer.process_directory(
       "docs/",
       pattern="summary",
       recursive=True,
       file_pattern="*.md"
   )

   # Process with multiple patterns
   synthesizer.process_file(
       "document.md",
       patterns=["summary", "analysis", "action_items"]
   )

Error Handling
^^^^^^^^^^^

Implement robust error handling:

.. code-block:: python

   from knowledge_synthesizer.exceptions import (
       RateLimitError,
       TokenLimitError,
       APIError
   )

   try:
       synthesizer.process_file("large_document.md")
   except TokenLimitError:
       print("Document too large for model context window")
   except RateLimitError:
       print("API rate limit reached")
   except APIError as e:
       print(f"API error occurred: {e}")

Configuration
^^^^^^^^^^^

Customize the behavior through configuration:

.. code-block:: python

   synthesizer = Synthesizer(
       model="gpt-4",
       max_tokens=8000,
       temperature=0.7,
       cache_patterns=True,
       rate_limit=60
   )

Best Practices
------------

1. **Pattern Selection**
   - Choose patterns appropriate for your content type
   - Use multiple patterns for comprehensive analysis

2. **Model Selection**
   - Use GPT-4 for complex tasks
   - Use GPT-3.5-Turbo for simpler tasks or when speed is priority

3. **Error Handling**
   - Always implement proper error handling
   - Consider retries for rate limits

4. **Performance**
   - Use batch processing for multiple files
   - Enable caching when appropriate

5. **Output Management**
   - Use consistent output directories
   - Implement version control for outputs

For more detailed information about specific features, check the :doc:`api` documentation. 