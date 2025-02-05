"""Core functionality for the Knowledge Synthesizer."""

import os
import json
from pathlib import Path
import time
from typing import Dict, Optional
import httpx
from openai import OpenAI
from dotenv import load_dotenv

class KnowledgeSynthesizer:
    """Main class for processing content using Fabric patterns."""
    
    GITHUB_API_BASE = "https://api.github.com/repos/danielmiessler/fabric/contents/patterns"
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/danielmiessler/fabric/main/patterns"
    CACHE_DIR = Path.home() / ".knowledge_synthesizer" / "cache"
    CACHE_EXPIRY = 24 * 60 * 60  # 24 hours in seconds
    
    def __init__(self, api_key=None, config_file='.env', model="gpt-4", 
                 output_dir="synthesis", output_suffix="_synthesis", dry_run=False,
                 separate_files=False, force_refresh=False, test_mode=False,
                 skip_cache=False):
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
        
        if self.dry_run:
            print("\n[DRY RUN] No files will be modified or API calls made\n")
        
        # Load environment variables
        print("\nLoading environment variables...")
        load_dotenv(config_file, override=True)
        
        # Try to load API key from config file if not provided
        if api_key is None:
            print("No API key provided, checking environment variables...")
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                # Clean up the API key by removing any whitespace or newlines
                api_key = api_key.strip().replace('\n', '').replace('\r', '')
                print("Found API key in environment variables")
                print(f"API key length: {len(api_key)}")  # Debug log
                print(f"API key first 4 chars: {api_key[:4]}")  # Debug log
            else:
                print("No API key found in environment variables")
            
        if not api_key and not self.dry_run and not self.test_mode:
            print("Attempting to load API key interactively...")
            api_key = self._load_api_key()
            if not api_key:
                raise ValueError("No OpenAI API key provided")
        
        # Store configuration
        self.output_dir = output_dir
        self.output_suffix = output_suffix
        
        # Initialize OpenAI client (skip if dry run)
        if not self.dry_run:
            print(f"Initializing OpenAI client with API key: {'[PROVIDED]' if api_key else '[MISSING]'}")
            print(f"test_mode: {self.test_mode}")  # Debug log
            print(f"Final API key length: {len(api_key) if api_key else 0}")  # Debug log
            print(f"Final API key first 4 chars: {api_key[:4] if api_key else ''}")  # Debug log
            self.http_client = httpx.Client(timeout=30.0)
            if not api_key:
                raise ValueError("OpenAI API key is required for non-dry-run mode")
            self.client = OpenAI(api_key=api_key)
            self.model = self._select_model(model)
            
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

    def _load_api_key(self) -> Optional[str]:
        """Load API key from environment."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            # Clean up the API key by removing any whitespace or newlines
            api_key = api_key.strip().replace('\n', '').replace('\r', '')
            
        if not api_key and not self.test_mode:
            api_key = input("Please enter your OpenAI API key: ").strip()
            # Save to .env file
            with open('.env', 'w') as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")
        return api_key
        
    def _load_patterns(self) -> Dict[str, str]:
        """Load all available patterns from GitHub."""
        if not self.test_mode:
            print("\nFetching available patterns from GitHub...")
        patterns = {}
        
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
        """Allow user to select the OpenAI model."""
        models = {
            "1": {
                "name": "gpt-4"
            },
            "2": {
                "name": "gpt-4-turbo-preview"
            },
            "3": {
                "name": "gpt-3.5-turbo"
            }
        }
        
        if self.test_mode:
            return default_model
        
        print("\nAvailable models:")
        print("-" * 50)
        for key, info in models.items():
            print(f"{key}: {info['name']}")
            print(f"   Description: {info['description']}")
            print(f"   Pricing: {info['pricing']}")
            print("-" * 50)
        
        choice = input(f"\nSelect a model (1-3) [default: {default_model}]: ").strip()
        
        if not choice:
            return default_model
        
        return models.get(choice, {"name": default_model})["name"]

    def _call_gpt(self, system_prompt, user_content):
        """Make an API call to the selected OpenAI model."""
        try:
            print(f"Making API call with model: {self.model}")
            response = self.client.chat.completions.create(
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
                result = self._call_gpt(pattern_content, content)
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