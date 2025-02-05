import os
import json
import argparse
from openai import OpenAI
from pathlib import Path
import time
import httpx
from typing import Dict
from dotenv import load_dotenv

class KnowledgeSynthesizer:
    GITHUB_API_BASE = "https://api.github.com/repos/danielmiessler/fabric/contents/patterns"
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/danielmiessler/fabric/main/patterns"
    
    def __init__(self, api_key=None, config_file='.env', model="gpt-4", 
                 output_dir="synthesis", output_suffix="_synthesis", dry_run=False,
                 separate_files=False, force_refresh=False):
        # Store settings
        self.dry_run = dry_run
        self.separate_files = separate_files
        self.force_refresh = force_refresh
        
        if self.dry_run:
            print("\n[DRY RUN] No files will be modified or API calls made\n")
        
        # Load environment variables
        load_dotenv(config_file)
        
        # Try to load API key from config file if not provided
        if api_key is None and not self.dry_run:
            api_key = self._load_api_key()
            if not api_key:
                raise ValueError("No OpenAI API key provided")
        
        # Store configuration
        self.output_dir = output_dir
        self.output_suffix = output_suffix
        
        # Initialize OpenAI client with custom http client (skip if dry run)
        if not self.dry_run:
            self.http_client = httpx.Client(timeout=30.0)
            self.client = OpenAI(
                api_key=api_key,
                http_client=self.http_client
            )
            self.model = self._select_model(model)
            self.all_patterns = self._load_patterns()
            self.selected_patterns = self._select_patterns()
        else:
            # In dry run, just show what would be loaded
            print("[DRY RUN] Would load patterns from GitHub")
            print("[DRY RUN] Would prompt for model selection")
            print("[DRY RUN] Would prompt for pattern selection")
    
    def _load_api_key(self):
        """Load API key from environment"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = input("Please enter your OpenAI API key: ").strip()
            # Save to .env file
            with open('.env', 'w') as f:
                f.write(f"OPENAI_API_KEY={api_key}")
        return api_key
        
    def _fetch_pattern_content(self, pattern_name: str) -> str:
        """Fetch a specific pattern's system.md content from GitHub"""
        url = f"{self.GITHUB_RAW_BASE}/{pattern_name}/system.md"
        try:
            response = self.http_client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching pattern {pattern_name}: {str(e)}")
            return None

    def _load_patterns(self) -> Dict[str, str]:
        """Load all available patterns from GitHub"""
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
                    print(f"✓ Loaded {pattern_name}")
                time.sleep(0.1)  # Rate limiting
                
        except Exception as e:
            print(f"Error loading patterns: {str(e)}")
            
        if not patterns:
            raise ValueError("No patterns could be loaded from GitHub")
            
        return patterns
    
    def _select_model(self, default_model):
        """Allow user to select the OpenAI model"""
        models = {
            "1": {
                "name": "gpt-4",
                "description": "Latest model, fastest and most cost-effective",
                "pricing": "$0.01/1K input, $0.03/1K output tokens"
            },
            "2": {
                "name": "gpt-4-turbo-preview",
                "description": "Latest GPT-4 Turbo model",
                "pricing": "$0.01/1K input, $0.03/1K output tokens"
            },
            "3": {
                "name": "gpt-3.5-turbo",
                "description": "Fast and cost-effective for simpler tasks",
                "pricing": "$0.0005/1K input, $0.0015/1K output tokens"
            }
        }
        
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
        """Make an API call to the selected OpenAI model"""
        try:
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
            print(f"Error calling {self.model}: {str(e)}")
            return None

    def _select_patterns(self):
        """Allow user to select which patterns to use"""
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
        """Check if output files already exist"""
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
        """Process a single file through selected patterns"""
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
            result = self._call_gpt(pattern_content, content)
            if result:
                results[pattern_name] = result
            time.sleep(1)  # Rate limiting
        
        return results

    def save_synthesis(self, results, output_dir, original_filename):
        """Save the synthesized results"""
        if not results:
            return
            
        if self.dry_run:
            output_path = Path(output_dir) / self.output_dir
            if self.separate_files:
                for pattern_name in results.keys():
                    output_file = output_path / f"{Path(original_filename).stem}_{pattern_name}.md"
                    print(f"[DRY RUN] Would save {pattern_name} results to: {output_file}")
            else:
                output_file = output_path / f"{Path(original_filename).stem}{self.output_suffix}.md"
                print(f"[DRY RUN] Would save combined results to: {output_file}")
            return
            
        # Create output directory if it doesn't exist
        output_path = Path(output_dir) / self.output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self.separate_files:
            # Save each pattern's results in a separate file
            for pattern_name, result in results.items():
                output_file = output_path / f"{Path(original_filename).stem}_{pattern_name}.md"
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(f"# {pattern_name.replace('_', ' ').title()} Analysis\n\n")
                        f.write(f"Source: {original_filename}\n\n")
                        f.write(f"{result}\n")
                    print(f"✓ Saved {pattern_name} results to {output_file}")
                except Exception as e:
                    print(f"Error saving {pattern_name} results to {output_file}: {str(e)}")
        else:
            # Save all results in a single file
            output_file = output_path / f"{Path(original_filename).stem}{self.output_suffix}.md"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Knowledge Synthesis for {original_filename}\n\n")
                    for pattern_name, result in results.items():
                        f.write(f"# {pattern_name.replace('_', ' ').title()}\n\n")
                        f.write(f"{result}\n\n")
                print(f"✓ Saved combined results to {output_file}")
            except Exception as e:
                print(f"Error saving results to {output_file}: {str(e)}")
    
    def process_directory(self, input_dir, file_pattern="*.md", test_mode=False):
        """Process files matching pattern in a directory"""
        input_path = Path(input_dir)
        
        # Get list of matching files
        matching_files = list(input_path.glob(file_pattern))
        if not matching_files:
            print(f"No files matching '{file_pattern}' found in {input_dir}")
            return
            
        if test_mode:
            # In test mode, just process the first file
            test_file = matching_files[0]
            print(f"\nTest mode: Processing only {test_file.name}")
            results = self.process_file(test_file, str(input_path))
            if results:
                self.save_synthesis(results, str(input_path), test_file.name)
        else:
            # Process all files
            for file_path in matching_files:
                results = self.process_file(file_path, str(input_path))
                if results:
                    self.save_synthesis(results, str(input_path), file_path.name)

def main():
    parser = argparse.ArgumentParser(description='Process files using AI patterns')
    parser.add_argument('input_dir', help='Directory containing input files')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--pattern', default='*.md', help='File pattern to match')
    parser.add_argument('--output', default='synthesis', help='Output directory name')
    parser.add_argument('--suffix', default='_synthesis', help='Output file suffix')
    parser.add_argument('--dry-run', action='store_true', 
                      help='Show what would be processed without making any changes')
    parser.add_argument('--separate', action='store_true',
                      help='Save each pattern\'s output in a separate file')
    parser.add_argument('--force', action='store_true',
                      help='Force regeneration of existing outputs')
    
    args = parser.parse_args()
    
    try:
        synthesizer = KnowledgeSynthesizer(
            output_dir=args.output,
            output_suffix=args.suffix,
            dry_run=args.dry_run,
            separate_files=args.separate,
            force_refresh=args.force
        )
        synthesizer.process_directory(
            args.input_dir,
            file_pattern=args.pattern,
            test_mode=args.test
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 