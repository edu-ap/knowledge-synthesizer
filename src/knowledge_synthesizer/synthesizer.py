"""Core functionality for the Knowledge Synthesizer."""

import os
import json
from pathlib import Path
import time
from typing import Dict, Optional
import httpx
from openai import OpenAI
from dotenv import load_dotenv
import google.generativeai as genai  # Add Google Generative AI import

class KnowledgeSynthesizer:
    """Main class for processing content using Fabric patterns."""
    
    GITHUB_API_BASE = "https://api.github.com/repos/danielmiessler/fabric/contents/patterns"
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/danielmiessler/fabric/main/patterns"
    CACHE_DIR = Path.home() / ".knowledge_synthesizer" / "cache"
    CACHE_EXPIRY = 24 * 60 * 60  # 24 hours in seconds
    
    # Define available models including Google's Gemini options
    MODELS = {
        "1": {"name": "gpt-4", "description": "Most capable model", "pricing": "Standard", "provider": "openai"},
        "2": {"name": "gpt-4-turbo-preview", "description": "Latest GPT-4", "pricing": "Lower cost", "provider": "openai"},
        "3": {"name": "gpt-3.5-turbo", "description": "Fast and efficient", "pricing": "Lowest cost", "provider": "openai"},
        "4": {"name": "models/gemini-1.5-pro", "description": "Google's flagship model (1M tokens)", "pricing": "Standard", "provider": "google"},
        "5": {"name": "models/gemini-1.5-flash", "description": "Google's faster model (1M tokens)", "pricing": "Lower cost", "provider": "google"},
        "6": {"name": "models/gemini-1.5-flash-8b", "description": "Google's efficient smaller model", "pricing": "Lowest cost", "provider": "google"}
    }
    
    def __init__(self, api_key=None, google_api_key=None, config_file='.env', model="gpt-4", 
                 output_dir="synthesis", output_suffix="_synthesis", dry_run=False,
                 separate_files=False, force_refresh=False, test_mode=False,
                 skip_cache=False, patterns_dir=None):
        # Store settings
        print("\nInitializing KnowledgeSynthesizer...")
        print(f"test_mode: {test_mode}")
        print(f"dry_run: {dry_run}")
        print(f"Initial api_key value: {'[PROVIDED]' if api_key else '[NONE]'}")  # Debug log
        self.dry_run = dry_run
        self.separate_files = separate_files
        self.force_refresh = force_refresh
        self.test_mode = test_mode
        self.skip_cache = skip_cache
        self.patterns_dir = patterns_dir  # Store the patterns directory
        self.using_google = False  # Flag to track if using Google models
        
        if self.patterns_dir:
            print(f"Using local patterns from: {self.patterns_dir}")
        
        if self.dry_run:
            print("\n[DRY RUN] No files will be modified or API calls made\n")
        
        # Get current working directory and create absolute path to .env file
        current_dir = os.getcwd()
        env_path = os.path.join(current_dir, config_file)
        print(f"\nLooking for .env file at: {env_path}")
        
        # Load environment variables from the local .env file with override=True
        if os.path.isfile(env_path):
            print(f"Found .env file at: {env_path}")
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            print(f"Warning: No .env file found at {env_path}")
            # Try default location as fallback
            load_dotenv(config_file, override=True)
        
        # Try to load API keys from config file if not provided
        if api_key is None:
            print("No OpenAI API key provided, checking environment variables...")
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                # Clean up the API key by removing any whitespace or newlines
                api_key = api_key.strip().replace('\n', '').replace('\r', '')
                print("Found API key in environment variables")
                print(f"API key length: {len(api_key)}")  # Debug log
                print(f"API key first 4 chars: {api_key[:4]}")  # Debug log
                print(f"API key last 3 chars: {api_key[-3:]}")  # Debug log to verify correct key
            else:
                print("No OpenAI API key found in environment variables")
        
        # Check for Google API key
        if google_api_key is None:
            print("No Google API key provided, checking environment variables...")
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if google_api_key:
                # Clean up the API key by removing any whitespace or newlines
                google_api_key = google_api_key.strip().replace('\n', '').replace('\r', '')
                print("Found Google API key in environment variables")
                print(f"Google API key length: {len(google_api_key)}")  # Debug log
                print(f"Google API key first 4 chars: {google_api_key[:4]}")  # Debug log
                print(f"Google API key last 3 chars: {google_api_key[-3:]}")  # Debug log to verify correct key
            else:
                print("No Google API key found in environment variables")
        
        if not api_key and not google_api_key and not self.dry_run and not self.test_mode:
            print("Attempting to load API keys interactively...")
            api_key, google_api_key = self._load_api_key()
            if not api_key and not google_api_key:
                raise ValueError("No API keys provided (either OpenAI or Google required)")
        
        # Store configuration
        self.output_dir = output_dir
        self.output_suffix = output_suffix
        
        # Initialize clients (skip if dry run)
        if not self.dry_run:
            self.http_client = httpx.Client(timeout=30.0)
            
            # Initialize OpenAI client if API key is provided
            self.openai_client = None
            if api_key:
                print(f"Initializing OpenAI client with API key: {'[PROVIDED]' if api_key else '[MISSING]'}")
                print(f"test_mode: {self.test_mode}")  # Debug log
                print(f"Final API key length: {len(api_key) if api_key else 0}")  # Debug log
                print(f"Final API key first 4 chars: {api_key[:4] if api_key else ''}")  # Debug log
                print(f"Final API key last 3 chars: {api_key[-3:] if api_key and len(api_key) > 3 else ''}")  # Debug log
                
                # Initialize OpenAI client with proper configuration for project-based keys
                try:
                    self.openai_client = OpenAI(
                        api_key=api_key,
                        # Add these parameters to better support all key types including project-based keys
                        # Uncomment if needed based on OpenAI API requirements
                        # base_url="https://api.openai.com/v1",
                    )
                    print("Successfully initialized OpenAI client")
                except Exception as e:
                    print(f"Error initializing OpenAI client: {str(e)}")
                    if not google_api_key:  # Only raise if we don't have Google as a fallback
                        raise
            
            # Initialize Google Generative AI if API key is provided
            self.google_configured = False
            if google_api_key:
                print(f"Initializing Google Generative AI with API key: {'[PROVIDED]' if google_api_key else '[MISSING]'}")
                try:
                    genai.configure(api_key=google_api_key)
                    self.google_configured = True
                    print("Successfully initialized Google Generative AI client")
                except Exception as e:
                    print(f"Error initializing Google Generative AI client: {str(e)}")
                    if not api_key:  # Only raise if we don't have OpenAI as a fallback
                        raise
            
            # Select model based on available clients
            self.model, self.model_provider = self._select_model(model)
            
        # Load patterns
        if self.test_mode:
            print("Using test patterns (test mode is enabled)")  # Debug log
            self.all_patterns = {"pattern1": "Test pattern 1", "pattern2": "Test pattern 2"}
            self.selected_patterns = self.all_patterns
        elif not self.dry_run:
            self.all_patterns = self._load_patterns()
            self.selected_patterns = self._select_patterns()
        else:
            self.all_patterns = {}
            self.selected_patterns = {}
            
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        self.CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(exist_ok=True)
        
    def _get_cached_pattern(self, pattern_name: str) -> Optional[str]:
        """Get a pattern from cache if it exists and is not expired."""
        if self.skip_cache:
            return None
            
        cache_file = self.CACHE_DIR / f"{pattern_name}.json"
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                
            # Check if cache is expired
            if time.time() - cached['timestamp'] > self.CACHE_EXPIRY:
                return None
                
            return cached['content']
        except Exception:
            return None
            
    def _cache_pattern(self, pattern_name: str, content: str):
        """Cache a pattern's content with timestamp."""
        if self.skip_cache:
            return
            
        self._ensure_cache_dir()
        cache_file = self.CACHE_DIR / f"{pattern_name}.json"
        
        try:
            cache_data = {
                'content': content,
                'timestamp': time.time()
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Warning: Failed to cache pattern {pattern_name}: {str(e)}")

    def _fetch_pattern_content(self, pattern_name: str) -> Optional[str]:
        """Fetch a specific pattern's system.md content from GitHub or cache."""
        # Try to get from cache first
        cached_content = self._get_cached_pattern(pattern_name)
        if cached_content is not None:
            if not self.test_mode:
                print(f"✓ Loaded {pattern_name} from cache")
            return cached_content
            
        # If not in cache or expired, fetch from GitHub
        url = f"{self.GITHUB_RAW_BASE}/{pattern_name}/system.md"
        try:
            response = self.http_client.get(url)
            response.raise_for_status()
            content = response.text
            
            # Cache the content
            self._cache_pattern(pattern_name, content)
            
            return content
        except Exception as e:
            if not self.test_mode:
                print(f"Error fetching pattern {pattern_name}: {str(e)}")
            return None

    def _load_api_key(self) -> tuple:
        """Load API keys from environment or prompt user."""
        # Try to find .env file in current directory
        current_dir = os.getcwd()
        env_path = os.path.join(current_dir, '.env')
        
        # Reload from local .env file if it exists
        if os.path.isfile(env_path):
            print(f"Reloading .env from: {env_path}")
            with open(env_path, 'r') as f:
                env_content = f.read()
                print(f"Found .env file with content length: {len(env_content)}")
            
            # Force reload environment variables from the local .env file
            load_dotenv(dotenv_path=env_path, override=True)
        
        # Try to get keys from environment
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            # Clean up the API key by removing any whitespace or newlines
            openai_key = openai_key.strip().replace('\n', '').replace('\r', '')
            print(f"Found OpenAI API key in environment variables (length: {len(openai_key)}, last 3 chars: {openai_key[-3:]})")
        
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            # Clean up the API key by removing any whitespace or newlines
            google_key = google_key.strip().replace('\n', '').replace('\r', '')
            print(f"Found Google API key in environment variables (length: {len(google_key)}, last 3 chars: {google_key[-3:]})")
        
        # If no keys found, prompt user
        if not openai_key and not google_key and not self.test_mode:
            print("No API keys found. You need at least one API key.")
            use_openai = input("Do you want to use OpenAI? (y/n): ").strip().lower() == 'y'
            use_google = input("Do you want to use Google Gemini? (y/n): ").strip().lower() == 'y'
            
            env_content = []
            
            if use_openai:
                openai_key = input("Please enter your OpenAI API key: ").strip()
                if openai_key:
                    env_content.append(f"OPENAI_API_KEY={openai_key}")
            
            if use_google:
                google_key = input("Please enter your Google API key: ").strip()
                if google_key:
                    env_content.append(f"GOOGLE_API_KEY={google_key}")
            
            # Save to .env file in current directory if we got any keys
            if env_content:
                with open(env_path, 'w') as f:
                    f.write("\n".join(env_content) + "\n")
                    print(f"Saved new API key(s) to {env_path}")
        
        return openai_key, google_key
        
    def _load_patterns(self) -> Dict[str, str]:
        """Load available patterns from GitHub or local directory."""
        patterns = {}
        
        # If a local patterns directory is specified, use that instead of GitHub
        if self.patterns_dir:
            print(f"\nLoading patterns from local directory: {self.patterns_dir}")
            try:
                # Get the absolute path to the patterns directory
                patterns_path = os.path.abspath(self.patterns_dir)
                
                # Check if the directory exists
                if not os.path.isdir(patterns_path):
                    raise ValueError(f"Patterns directory not found: {patterns_path}")
                
                # Get all subdirectories (each should be a pattern)
                pattern_dirs = [d for d in os.listdir(patterns_path) 
                               if os.path.isdir(os.path.join(patterns_path, d))]
                
                if not pattern_dirs:
                    raise ValueError(f"No pattern directories found in: {patterns_path}")
                
                # Load each pattern
                for pattern_name in pattern_dirs:
                    pattern_dir = os.path.join(patterns_path, pattern_name)
                    system_file = os.path.join(pattern_dir, "system.md")
                    
                    if os.path.isfile(system_file):
                        with open(system_file, 'r') as f:
                            content = f.read()
                        patterns[pattern_name] = content
                        print(f"✓ Loaded local pattern: {pattern_name}")
                    else:
                        print(f"Warning: No system.md found in pattern directory: {pattern_dir}")
                
                if not patterns:
                    raise ValueError(f"No valid patterns found in: {patterns_path}")
                
                return patterns
                
            except Exception as e:
                print(f"Error loading local patterns: {str(e)}")
                if self.test_mode:
                    return {"pattern1": "Test pattern 1", "pattern2": "Test pattern 2"}
                raise
        
        # If no local patterns directory or it failed, fall back to GitHub
        if not self.test_mode:
            print("\nFetching available patterns from GitHub...")
        
        try:
            # Fetch list of pattern directories
            response = self.http_client.get(self.GITHUB_API_BASE)
            response.raise_for_status()
            pattern_dirs = [item['name'] for item in response.json() 
                          if item['type'] == 'dir']
            
            # Load each pattern
            for pattern_name in pattern_dirs:
                content = self._fetch_pattern_content(pattern_name)
                if content:
                    patterns[pattern_name] = content
                    if not self.test_mode:
                        print(f"✓ Loaded {pattern_name}")
                time.sleep(0.1)  # Rate limiting
                
        except Exception as e:
            if not self.test_mode:
                print(f"Error loading patterns: {str(e)}")
            if self.test_mode:
                # In test mode, return test patterns if GitHub API fails
                return {"pattern1": "Test pattern 1", "pattern2": "Test pattern 2"}
            
        if not patterns and not self.test_mode:
            raise ValueError("No patterns could be loaded from GitHub")
            
        return patterns
    
    def _select_model(self, default_model):
        """Allow user to select the model to use."""
        # Only show models for configured clients
        available_models = {}
        
        for key, model_info in self.MODELS.items():
            if (model_info["provider"] == "openai" and self.openai_client) or \
               (model_info["provider"] == "google" and self.google_configured):
                available_models[key] = model_info
        
        if not available_models:
            raise ValueError("No API clients configured correctly")
        
        if self.test_mode:
            # In test mode, use the first available model
            model_key = next(iter(available_models.keys()))
            return available_models[model_key]["name"], available_models[model_key]["provider"]
        
        # Group models by provider
        openai_models = {k: v for k, v in available_models.items() if v["provider"] == "openai"}
        google_models = {k: v for k, v in available_models.items() if v["provider"] == "google"}
        
        print("\nAvailable models:")
        
        if openai_models:
            print("\nOPENAI MODELS:")
            print("-" * 50)
            for key, info in openai_models.items():
                print(f"{key}: {info['name']}")
                print(f"   Description: {info['description']}")
                print(f"   Pricing: {info['pricing']}")
                print("-" * 50)
        
        if google_models:
            print("\nGOOGLE MODELS:")
            print("-" * 50)
            for key, info in google_models.items():
                print(f"{key}: {info['name']}")
                print(f"   Description: {info['description']}")
                print(f"   Pricing: {info['pricing']}")
                print("-" * 50)
        
        choice = input(f"\nSelect a model (1-{len(available_models)}) [default: 1]: ").strip()
        
        if not choice or choice not in available_models:
            # Default to first available model
            first_key = next(iter(available_models.keys()))
            return available_models[first_key]["name"], available_models[first_key]["provider"]
        
        selected_model = available_models[choice]
        return selected_model["name"], selected_model["provider"]

    def _call_gpt(self, system_prompt, user_content):
        """Make an API call to the selected OpenAI model."""
        try:
            print(f"Making API call with model: {self.model}")
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            if not self.test_mode:
                print(f"Error calling {self.model}: {str(e)}")
            return None

    def _call_gemini(self, system_prompt, user_content):
        """Make an API call to the selected Google Gemini model."""
        try:
            print(f"Making API call with model: {self.model}")
            
            # Gemini doesn't have separate system and user prompts, so combine them
            combined_prompt = f"{system_prompt}\n\n{user_content}"
            
            # Create a generative model
            model = genai.GenerativeModel(model_name=self.model)
            
            # Generate content
            response = model.generate_content(combined_prompt)
            
            # Return the response text
            return response.text
        except Exception as e:
            if not self.test_mode:
                print(f"Error calling {self.model}: {str(e)}")
            return None

    def _select_patterns(self):
        """Allow user to select which patterns to use."""
        if self.test_mode:
            return self.all_patterns
            
        print("\nAvailable patterns:")
        print("-" * 50)
        for i, pattern_name in enumerate(self.all_patterns.keys(), 1):
            print(f"{i}: {pattern_name.replace('_', ' ').title()}")
        print("-" * 50)
        print("Enter pattern numbers to use (comma-separated, or 'all')")
        print("Example: 1,3,5 or all")
        
        while True:
            choice = input("Select patterns: ").strip().lower()
            if choice == 'all':
                return self.all_patterns
            
            try:
                selected_indices = [int(x.strip()) for x in choice.split(',')]
                selected_patterns = {}
                pattern_list = list(self.all_patterns.keys())
                
                for idx in selected_indices:
                    if 1 <= idx <= len(pattern_list):
                        pattern_name = pattern_list[idx-1]
                        selected_patterns[pattern_name] = self.all_patterns[pattern_name]
                
                if selected_patterns:
                    return selected_patterns
                print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas or 'all'")

    def _output_files_exist(self, output_path, original_filename, pattern_names):
        """Check if output files already exist."""
        if self.separate_files:
            # Check if all pattern files exist
            return all(
                (output_path / f"{Path(original_filename).stem}_{pattern_name}.md").exists()
                for pattern_name in pattern_names
            )
        else:
            # Check if combined file exists
            return (output_path / f"{Path(original_filename).stem}{self.output_suffix}.md").exists()

    def process_file(self, file_path, output_dir):
        """Process a single file through selected patterns."""
        if self.dry_run:
            print(f"[DRY RUN] Would process: {file_path}")
            print(f"[DRY RUN] Would apply selected patterns and save results")
            return {"dry_run": True}
            
        # Check if output already exists
        output_path = Path(output_dir) / self.output_dir
        if not self.force_refresh and self._output_files_exist(output_path, file_path.name, self.selected_patterns.keys()):
            print(f"\nSkipping {file_path} - output already exists")
            print("(Use --force to regenerate existing outputs)")
            return None
            
        print(f"\nProcessing: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return None
        
        results = {}
        for pattern_name, pattern_content in self.selected_patterns.items():
            print(f"Applying pattern: {pattern_name}")
            if self.test_mode:
                # In test mode, just use pattern name as result
                results[pattern_name] = f"Test result for {pattern_name}"
            else:
                # Call the appropriate API based on the selected model provider
                if self.model_provider == "openai":
                    result = self._call_gpt(pattern_content, content)
                elif self.model_provider == "google":
                    result = self._call_gemini(pattern_content, content)
                else:
                    raise ValueError(f"Unknown model provider: {self.model_provider}")
                
                if result:
                    results[pattern_name] = result
                time.sleep(1)  # Rate limiting
        
        return results

    def save_synthesis(self, results, output_dir, original_filename):
        """Save the synthesized results."""
        if not results:
            return
            
        # Create output directory if it doesn't exist
        output_path = Path(output_dir) / self.output_dir
        output_path.mkdir(parents=True, exist_ok=True)
            
        if self.dry_run:
            if self.separate_files:
                for pattern_name in results.keys():
                    output_file = output_path / f"{Path(original_filename).stem}_{pattern_name}.md"
                    print(f"[DRY RUN] Would save {pattern_name} results to: {output_file}")
            else:
                output_file = output_path / f"{Path(original_filename).stem}{self.output_suffix}.md"
                print(f"[DRY RUN] Would save combined results to: {output_file}")
            return

        if self.separate_files:
            # Save individual files for each pattern
            for pattern_name, result in results.items():
                output_file = output_path / f"{Path(original_filename).stem}_{pattern_name}.md"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                if not self.test_mode:
                    print(f"Saved {pattern_name} results to: {output_file}")
        else:
            # Save combined file
            output_file = output_path / f"{Path(original_filename).stem}{self.output_suffix}.md"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                for pattern_name, result in results.items():
                    f.write(f"\n## {pattern_name}\n\n{result}\n")
            if not self.test_mode:
                print(f"Saved combined results to: {output_file}")

    def process_directory(self, input_dir, file_pattern="*.md", test_mode=False):
        """Process all markdown files in a directory."""
        input_path = Path(input_dir)
        output_path = Path(input_dir) / self.output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all markdown files
        markdown_files = list(input_path.glob(file_pattern))
        if not markdown_files:
            print(f"\nNo files matching '{file_pattern}' found in {input_dir}")
            return output_path
            
        # Process each file
        for file_path in markdown_files:
            results = self.process_file(file_path, input_dir)
            if results and not self.dry_run:
                self.save_synthesis(results, input_dir, file_path.name)
                
        # In test mode, create a dummy output file if none exists
        if self.test_mode and not list(output_path.glob("*.md")):
            test_file = output_path / "test_synthesis.md"
            test_file.write_text("Test synthesis content")
            
        return output_path 