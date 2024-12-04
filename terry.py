import argparse
import json
import os
import sys
import yaml
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from pm import ProductManager, Priority, ImpactArea
from llm_processor import OpenAIProcessor, LlamaProcessor, LLMProcessor
from issue_trackers import IssueTrackerFactory

# Load environment variables from .env file
load_dotenv()

class TerryCLI:
    def __init__(self):
        self.config_path = os.path.expanduser("~/.terry_config.yaml")
        self.terry = None
        self.llm_processor = None
        self.issue_tracker = None
        self.config = {}  # Initialize empty config
        self.load_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings."""
        return {
            'team_context': {
                'current_sprint_focus': 'General Development',
                'quarter_objectives': 'Improve Product Quality'
            },
            'llm_config': {
                'provider': 'openai',
                'model_path': None,
                'api_key': None
            },
            'issue_tracker': {
                'provider': None,  # 'github'
                'repo': None      # for GitHub
            }
        }

    def load_config(self) -> None:
        """Load team and project configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                    
                    # Ensure all required sections exist
                    default_config = self.get_default_config()
                    if 'team_context' not in self.config:
                        self.config['team_context'] = default_config['team_context']
                    if 'llm_config' not in self.config:
                        self.config['llm_config'] = default_config['llm_config']
                    if 'issue_tracker' not in self.config:
                        self.config['issue_tracker'] = default_config['issue_tracker']
                    
                    # Initialize components
                    self.terry = ProductManager(team_context=self.config['team_context'])
                    self.setup_llm_processor(self.config['llm_config'])
                    self.setup_issue_tracker(self.config['issue_tracker'])
            else:
                # Create default config
                self.config = self.get_default_config()
                with open(self.config_path, 'w') as f:
                    yaml.dump(self.config, f)
                self.terry = ProductManager(team_context=self.config['team_context'])
                self.setup_llm_processor(self.config['llm_config'])
                
            # Save any updates made to config
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f)
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)

    def setup_issue_tracker(self, config: Dict[str, Any]) -> None:
        """Set up the issue tracker based on configuration."""
        provider = config.get('provider')
        if not provider:
            return  # No issue tracker configured
            
        try:
            self.issue_tracker = IssueTrackerFactory.create_tracker(
                provider,
                repo=config.get('repo'),
                team_id=config.get('team_id')
            )
        except Exception as e:
            print(f"Warning: Failed to initialize issue tracker: {e}")
            self.issue_tracker = None

    async def create_ticket_from_nl(self, args) -> None:
        """Create a ticket from natural language input."""
        print("\n🤖 Terry is analyzing your request...")
        
        try:
            # Process the natural language input
            ticket_data = await self.process_natural_language(args.description)
            
            # Create the ticket using the processed data
            ticket = self.terry.create_ticket(
                title=ticket_data.get('title', 'Untitled'),
                description=ticket_data.get('description', args.description),
                context={
                    'revenue_potential': ticket_data.get('scores', {}).get('revenue_potential', 50),
                    'user_impact': ticket_data.get('scores', {}).get('user_impact', 50),
                    'technical_complexity': ticket_data.get('scores', {}).get('technical_complexity', 50),
                    'strategic_alignment': ticket_data.get('scores', {}).get('strategic_alignment', 50)
                }
            )

            # Output ticket details
            print("\n🎫 Generated Ticket:")
            print("-" * 40)
            print(f"Ticket ID:      {ticket.ticket_id}")
            print(f"Priority:       {ticket.priority.name}")
            print(f"Impact Area:    {ticket.impact_area.value}")
            print("\n📝 Description:")
            print(ticket.description)

            # Create issue in configured tracker if available
            if self.issue_tracker and not args.no_tracker:
                print("\n📋 Creating issue in tracking system...")
                try:
                    result = await self.issue_tracker.create_issue_with_cache({
                        'title': ticket.title,
                        'description': ticket.description,
                        'priority': ticket.priority.name,
                        'impact_area': ticket.impact_area.value,
                        'scores': ticket_data.get('scores', {})
                    })
                    
                    if result['success']:
                        print(f"✅ Issue created: {result['url']}")
                    else:
                        print(f"❌ Failed to create issue: {result['error']}")
                        print(f"💾 Issue cached at: {result['cache_file']}")
                        print("You can retry later with: terry cache retry --file", result['cache_file'])
                except Exception as e:
                    print(f"❌ Failed to create issue: {e}")

            # Optional: Save ticket to a file
            if args.output:
                output_file = f"{ticket.ticket_id}.yaml"
                ticket_dict = {
                    'id': ticket.ticket_id,
                    'title': ticket.title,
                    'priority': ticket.priority.name,
                    'impact_area': ticket.impact_area.value,
                    'description': ticket.description,
                    'scores': ticket_data.get('scores', {})
                }
                with open(output_file, 'w') as f:
                    yaml.dump(ticket_dict, f)
                print(f"\n💾 Ticket saved to {output_file}")
                
        except Exception as e:
            print(f"\n❌ Error creating ticket: {e}")
            print("\nPlease make sure your configuration is correct:")
            print("  - For OpenAI: Set your API key with --openai-api-key or OPENAI_API_KEY environment variable")
            print("  - For Llama: Set the model path with --llm-model-path")
            print("  - For GitHub: Set GITHUB_TOKEN and GITHUB_REPO environment variables")
            sys.exit(1)

    def update_config(self, args) -> None:
        """Update Terry's configuration."""
        try:
            # Load current config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            else:
                self.config = self.get_default_config()

            # Ensure required sections exist
            if 'team_context' not in self.config:
                self.config['team_context'] = self.get_default_config()['team_context']
            if 'llm_config' not in self.config:
                self.config['llm_config'] = self.get_default_config()['llm_config']
            if 'issue_tracker' not in self.config:
                self.config['issue_tracker'] = self.get_default_config()['issue_tracker']
            
            # Update team context
            if args.sprint_focus:
                self.config['team_context']['current_sprint_focus'] = args.sprint_focus
            if args.quarter_objectives:
                self.config['team_context']['quarter_objectives'] = args.quarter_objectives
            
            # Update LLM config
            if args.llm_provider:
                self.config['llm_config']['provider'] = args.llm_provider
            if args.llm_model_path:
                self.config['llm_config']['model_path'] = args.llm_model_path
            if args.openai_api_key:
                self.config['llm_config']['api_key'] = args.openai_api_key
                
            # Update issue tracker config
            if args.tracker_provider:
                self.config['issue_tracker']['provider'] = args.tracker_provider
            if args.github_repo:
                self.config['issue_tracker']['repo'] = args.github_repo
            
            # Save updated config
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f)
            
            print("✅ Configuration updated successfully!")
            print("\nCurrent configuration:")
            print(json.dumps(self.config, indent=2))
            
            # Reinitialize components with new config
            self.terry = ProductManager(team_context=self.config['team_context'])
            self.setup_llm_processor(self.config['llm_config'])
            self.setup_issue_tracker(self.config['issue_tracker'])
            
        except Exception as e:
            print(f"Error updating configuration: {e}")
            sys.exit(1)

    def setup_cli(self) -> argparse.ArgumentParser:
        """Set up command-line argument parser."""
        parser = argparse.ArgumentParser(
            description="Terry: Your Sarcastic AI Product Manager CLI"
        )
        subparsers = parser.add_subparsers(dest='command')

        # Natural language ticket creation
        nl_parser = subparsers.add_parser('nl', help='Create ticket from natural language')
        nl_parser.add_argument('description', help='Natural language description of the ticket')
        nl_parser.add_argument('-o', '--output', action='store_true', 
                             help='Save ticket to a file')
        nl_parser.add_argument('--no-tracker', action='store_true',
                             help='Skip creating issue in tracking system')

        # Traditional ticket creation
        ticket_parser = subparsers.add_parser('create', help='Create a new ticket')
        ticket_parser.add_argument('title', help='Ticket title')
        ticket_parser.add_argument('description', help='Ticket description')
        ticket_parser.add_argument('--revenue', type=int, 
            help='Revenue potential score (0-100)', default=50)
        ticket_parser.add_argument('--user-impact', type=int, 
            help='User impact score (0-100)', default=50)
        ticket_parser.add_argument('--complexity', type=int, 
            help='Technical complexity score (0-100)', default=50)
        ticket_parser.add_argument('--alignment', type=int, 
            help='Strategic alignment score (0-100)', default=50)
        ticket_parser.add_argument('-o', '--output', action='store_true', 
            help='Save ticket to a file')
        ticket_parser.add_argument('--no-tracker', action='store_true',
                                 help='Skip creating issue in tracking system')

        # Cache management
        cache_parser = subparsers.add_parser('cache', help='Manage cached issues')
        cache_subparsers = cache_parser.add_subparsers(dest='cache_command')
        
        # List cached issues
        cache_list = cache_subparsers.add_parser('list', help='List cached issues')
        
        # Retry cached issues
        cache_retry = cache_subparsers.add_parser('retry', help='Retry creating cached issues')
        cache_retry.add_argument('--all', action='store_true', 
                               help='Retry all cached issues')
        cache_retry.add_argument('--file', help='Retry specific cache file')

        # Config update
        config_parser = subparsers.add_parser('config', help='Update Terry\'s configuration')
        config_parser.add_argument('--sprint-focus', help='Update current sprint focus')
        config_parser.add_argument('--quarter-objectives', help='Update quarter objectives')
        config_parser.add_argument('--llm-provider', choices=['openai', 'llama'],
                                 help='Set LLM provider (openai or llama)')
        config_parser.add_argument('--llm-model-path', help='Set path to Llama model')
        config_parser.add_argument('--openai-api-key', help='Set OpenAI API key')
        config_parser.add_argument('--tracker-provider', choices=['github'],
                                 help='Set issue tracker provider')
        config_parser.add_argument('--github-repo', help='Set GitHub repository (org/repo)')

        return parser

    async def handle_cache_command(self, args) -> None:
        """Handle cache-related commands."""
        from issue_trackers import IssueCache, IssueTrackerFactory
        
        if args.cache_command == 'list':
            cached_issues = IssueCache.list_cached_issues()
            if not cached_issues:
                print("No cached issues found.")
                return
                
            print("\n📋 Cached Issues:")
            print("-" * 40)
            for issue in cached_issues:
                print(f"Timestamp: {issue['timestamp']}")
                print(f"Type: {issue['tracker_type']}")
                print(f"Title: {issue['ticket_data'].get('title', 'Untitled')}")
                print(f"Cache File: {issue['cache_file']}")
                print("-" * 40)
                
        elif args.cache_command == 'retry':
            if not self.issue_tracker:
                print("❌ No issue tracker configured.")
                return
                
            if args.file:
                # Retry specific file
                print(f"\n🔄 Retrying cached issue from: {args.file}")
                result = await self.issue_tracker.retry_cached_issue(args.file)
                if result['success']:
                    print(f"✅ Successfully created issue!")
                    print(f"🔗 Issue URL: {result['url']}")
                else:
                    print(f"❌ Failed to create issue: {result['error']}")
            elif args.all:
                # Retry all cached issues
                print("\n🔄 Retrying all cached issues...")
                tracker_config = self.config.get('issue_tracker', {})
                results = await IssueTrackerFactory.retry_cached_issues(
                    tracker_config.get('provider', 'github'),
                    repo=tracker_config.get('repo')
                )
                
                success_count = sum(1 for r in results if r['success'])
                print(f"\n📊 Retry Results:")
                print(f"Successfully created: {success_count}/{len(results)} issues")
                
                if success_count > 0:
                    print("\n✅ Successfully created issues:")
                    for result in results:
                        if result['success']:
                            print(f"🔗 {result['url']}")
                
                if success_count < len(results):
                    print("\n❌ Failed issues:")
                    for result in results:
                        if not result['success']:
                            print(f"- {result['cache_file']}: {result['error']}")
                            print(f"  Retry with: terry cache retry --file {result['cache_file']}")
            else:
                print("Please specify --all to retry all issues or --file to retry a specific issue.")

    async def run_async(self, args):
        """Run the Terry CLI with async support."""
        if not args.command:
            self.setup_cli().print_help()
            return

        if args.command == 'nl':
            await self.create_ticket_from_nl(args)
        elif args.command == 'create':
            self.create_ticket(args)
        elif args.command == 'config':
            self.update_config(args)
        elif args.command == 'cache':
            await self.handle_cache_command(args)

    def run(self):
        """Run the Terry CLI."""
        parser = self.setup_cli()
        args = parser.parse_args()
        
        # Run async commands in event loop
        if args.command == 'nl':
            asyncio.run(self.run_async(args))
        else:
            if args.command == 'create':
                self.create_ticket(args)
            elif args.command == 'config':
                self.update_config(args)
            elif args.command == 'cache':
                asyncio.run(self.handle_cache_command(args))
            else:
                parser.print_help()

    async def process_natural_language(self, text: str) -> dict:
        """Process natural language input using the configured LLM."""
        if not self.llm_processor:
            print("Error: LLM processor not configured")
            sys.exit(1)
        
        try:
            return await self.llm_processor.process_input(text)
        except Exception as e:
            print(f"Error processing natural language input: {e}")
            sys.exit(1)

    def setup_llm_processor(self, llm_config: dict) -> None:
        """Set up the LLM processor based on configuration."""
        provider = llm_config.get('provider', 'openai')
        
        try:
            if provider == 'openai':
                api_key = llm_config.get('api_key') or os.getenv("OPENAI_API_KEY")
                self.llm_processor = OpenAIProcessor(api_key=api_key)
            elif provider == 'llama':
                model_path = llm_config.get('model_path')
                if not model_path:
                    print("Warning: model_path not specified for Llama, defaulting to OpenAI")
                    self.llm_processor = OpenAIProcessor()
                else:
                    self.llm_processor = LlamaProcessor(model_path)
            else:
                print(f"Warning: Unknown LLM provider: {provider}, defaulting to OpenAI")
                self.llm_processor = OpenAIProcessor()
        except Exception as e:
            print(f"Warning: Error setting up LLM processor: {e}, defaulting to OpenAI")
            self.llm_processor = OpenAIProcessor()

def main():
    terry_cli = TerryCLI()
    terry_cli.run()

if __name__ == "__main__":
    main()
