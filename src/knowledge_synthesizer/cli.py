"""Command-line interface for Knowledge Synthesizer."""

import sys
import argparse
from pathlib import Path
from .synthesizer import KnowledgeSynthesizer

def main(args=None):
    """Main entry point for the command-line interface."""
    if args is None:
        args = sys.argv[1:]
        
    parser = argparse.ArgumentParser(
        description='Knowledge Synthesizer - Apply Fabric patterns to your local content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single markdown file
  %(prog)s document.md

  # Process all markdown files in a directory
  %(prog)s docs/

  # Process files recursively with a specific pattern
  %(prog)s docs/ -r --pattern "*.txt"

  # Preview what would be processed without making changes
  %(prog)s docs/ --dry-run

  # Save each pattern's output separately
  %(prog)s docs/ --separate

  # Force regeneration of all outputs
  %(prog)s docs/ --force

  # Custom output directory and suffix
  %(prog)s docs/ --output "analysis" --suffix "_insights"

For more information, visit: https://github.com/edu-ap/knowledge-synthesizer
"""
    )

    # Input/Output options
    io_group = parser.add_argument_group('Input/Output Options')
    io_group.add_argument('path', 
                         help='File or directory to process')
    io_group.add_argument('--recursive', '-r', 
                         action='store_true',
                         help='Process directories recursively')
    io_group.add_argument('--pattern', 
                         default='*.md',
                         help='File pattern to match (default: %(default)s)')
    io_group.add_argument('--output', 
                         default='synthesis',
                         help='Output directory name (default: %(default)s)')
    io_group.add_argument('--suffix', 
                         default='_synthesis',
                         help='Output file suffix (default: %(default)s)')

    # Processing options
    proc_group = parser.add_argument_group('Processing Options')
    proc_group.add_argument('--dry-run', 
                          action='store_true',
                          help='Show what would be processed without making changes')
    proc_group.add_argument('--separate', 
                          action='store_true',
                          help='Save each pattern\'s output in a separate file')
    proc_group.add_argument('--force', 
                          action='store_true',
                          help='Force regeneration of existing outputs')

    # Cache options
    cache_group = parser.add_argument_group('Cache Options')
    cache_group.add_argument('--skip-cache', 
                           action='store_true',
                           help='Skip using cached patterns and download fresh copies')

    # Other options
    other_group = parser.add_argument_group('Other Options')
    other_group.add_argument('--version', 
                           action='version',
                           version='%(prog)s v0.1.0',
                           help='Show program\'s version number and exit')
    
    args = parser.parse_args(args)
    
    try:
        # Check if path exists
        path = Path(args.path)
        if not path.exists():
            print(f"Error: Path does not exist: {args.path}")
            return 1
            
        synthesizer = KnowledgeSynthesizer(
            output_dir=args.output,
            output_suffix=args.suffix,
            dry_run=args.dry_run,
            separate_files=args.separate,
            force_refresh=args.force,
            test_mode=False,
            skip_cache=args.skip_cache
        )
        
        if path.is_file():
            results = synthesizer.process_file(path, str(path.parent))
            if results:
                synthesizer.save_synthesis(results, str(path.parent), path.name)
        else:
            synthesizer.process_directory(
                str(path),
                file_pattern=args.pattern,
                test_mode=False
            )
            
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 