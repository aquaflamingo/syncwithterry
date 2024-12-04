from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import os
import json
from datetime import datetime
from pathlib import Path
try:
    from github import Github
except ImportError:
    raise ImportError(
        "PyGithub package not found. Please install it with: pip install PyGithub"
    )

CACHE_DIR = Path("/var/tmp/terry_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class IssueCache:
    """Handle caching of failed issue creation attempts."""
    
    @staticmethod
    def cache_issue(tracker_type: str, ticket_data: Dict[str, Any]) -> str:
        """Cache a failed issue creation attempt."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cache_file = CACHE_DIR / f"issue_{timestamp}.json"
        
        cache_data = {
            "tracker_type": tracker_type,
            "ticket_data": ticket_data,
            "timestamp": timestamp
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
            
        return str(cache_file)

    @staticmethod
    def list_cached_issues() -> List[Dict[str, Any]]:
        """List all cached issues."""
        cached_issues = []
        for file in CACHE_DIR.glob("issue_*.json"):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    data['cache_file'] = str(file)
                    cached_issues.append(data)
            except Exception as e:
                print(f"Warning: Failed to read cache file {file}: {e}")
        
        return sorted(cached_issues, key=lambda x: x['timestamp'], reverse=True)

    @staticmethod
    def remove_cache_file(cache_file: str) -> None:
        """Remove a cache file after successful issue creation."""
        try:
            Path(cache_file).unlink()
        except Exception as e:
            print(f"Warning: Failed to remove cache file {cache_file}: {e}")

class IssueTracker(ABC):
    """Base class for issue tracker integrations."""
    
    @abstractmethod
    async def create_issue(self, ticket_data: Dict[str, Any]) -> str:
        """Create an issue in the tracking system and return its URL."""
        pass

    @abstractmethod
    async def get_status(self) -> bool:
        """Check if the integration is properly configured and accessible."""
        pass

    async def create_issue_with_cache(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an issue with local caching for failure recovery."""
        try:
            issue_url = await self.create_issue(ticket_data)
            return {
                "success": True,
                "url": issue_url,
                "cache_file": None
            }
        except Exception as e:
            # Cache the failed attempt
            cache_file = IssueCache.cache_issue(self.__class__.__name__, ticket_data)
            return {
                "success": False,
                "error": str(e),
                "cache_file": cache_file
            }

class GitHubTracker(IssueTracker):
    def __init__(self, token: Optional[str] = None, repo: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token not found. Set GITHUB_TOKEN environment variable.")
        
        self.repo_name = repo or os.getenv("GITHUB_REPO")
        if not self.repo_name:
            raise ValueError("GitHub repository not specified. Set GITHUB_REPO environment variable.")
        
        self.client = Github(self.token)
        self.repo = self.client.get_repo(self.repo_name)

    async def create_issue(self, ticket_data: Dict[str, Any]) -> str:
        """Create an issue in GitHub."""
        # Convert Terry's priority to GitHub labels
        priority_labels = {
            "P0": "priority:critical",
            "P1": "priority:high",
            "P2": "priority:medium",
            "P3": "priority:low"
        }
        
        # Extract priority key from full priority string
        priority_key = ticket_data['priority'].split()[0]
        
        # Clean and format the impact area for label
        impact_area = ticket_data['impact_area']
        # Remove everything in parentheses and special characters
        impact_area = impact_area.split('(')[0].strip()
        # Convert to lowercase and replace spaces with hyphens
        impact_area = impact_area.lower().replace(' ', '-')
        
        # Prepare labels
        labels = [
            priority_labels.get(priority_key, "priority:medium"),
            f"area:{impact_area}",
            "generated-by-terry"
        ]
        
        try:
            # Create issue
            issue = self.repo.create_issue(
                title=ticket_data['title'],
                body=self._format_description_for_github(ticket_data),
                labels=labels
            )
            return issue.html_url
        except Exception as e:
            # Add more context to the error
            raise ValueError(f"Failed to create GitHub issue: {str(e)}\nLabels: {labels}")

    def _format_description_for_github(self, ticket_data: Dict[str, Any]) -> str:
        """Format the description for GitHub's markdown format."""
        # Extract scores safely with defaults
        scores = ticket_data.get('scores', {})
        if not isinstance(scores, dict):
            scores = {
                'revenue_potential': 50,
                'user_impact': 50,
                'technical_complexity': 50,
                'strategic_alignment': 50
            }
        
        return f"""{ticket_data['description']}

---
> Generated by Terry 🤖"""

    async def get_status(self) -> bool:
        """Check if GitHub integration is working."""
        try:
            # Try to access the repo to verify permissions
            self.repo.full_name
            return True
        except Exception:
            return False

    async def retry_cached_issue(self, cache_file: str) -> Dict[str, Any]:
        """Retry creating an issue from a cache file."""
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Create the issue
            issue_url = await self.create_issue(cache_data['ticket_data'])
            
            # Remove the cache file on success
            IssueCache.remove_cache_file(cache_file)
            
            return {
                "success": True,
                "url": issue_url,
                "cache_file": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cache_file": cache_file
            }

class IssueTrackerFactory:
    """Factory for creating issue tracker instances."""
    
    @staticmethod
    def create_tracker(tracker_type: str, **kwargs) -> IssueTracker:
        """Create and return an issue tracker instance."""
        if tracker_type.lower() == 'github':
            # Filter only GitHub-relevant parameters
            github_params = {
                'token': kwargs.get('token'),
                'repo': kwargs.get('repo')
            }
            return GitHubTracker(**github_params)
        else:
            raise ValueError(f"Unsupported issue tracker type: {tracker_type}")

    @staticmethod
    async def retry_cached_issues(tracker_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Retry all cached issues for a specific tracker type."""
        tracker = IssueTrackerFactory.create_tracker(tracker_type, **kwargs)
        results = []
        
        for cached_issue in IssueCache.list_cached_issues():
            if cached_issue['tracker_type'] == tracker.__class__.__name__:
                result = await tracker.retry_cached_issue(cached_issue['cache_file'])
                results.append(result)
        
        return results 