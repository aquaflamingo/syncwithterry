# Terry - Your AI Product Manager 🤖

![terry](https://github.com/user-attachments/assets/dc9c79a7-3f02-4b2f-a474-5ac28b50fcb1)

Terry is an AI product manager that developers actually love. With a dry sense of humor and a knack for corporate satire, Terry helps create well-structured tickets while keeping the team entertained.


https://github.com/user-attachments/assets/9ec11360-399f-44e1-8eee-faf440f8534d


## Features

- 🎯 Natural language ticket creation
- 😄 Sarcastic corporate humor
- 📊 Smart priority and impact scoring
- 🔗 GitHub Issues integration
- 💾 Local caching for failed tickets
- 🔄 Automatic retry mechanism

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your credentials
   vim .env
   ```

## Configuration

### 1. OpenAI Setup

```bash
# Set your OpenAI API key
export OPENAI_API_KEY='your-key-here'
python terry.py config --llm-provider openai
```

### 2. GitHub Setup

```bash
# Set your GitHub token and repo
export GITHUB_TOKEN='your-token-here'
python terry.py config --tracker-provider github --github-repo "org/repo"
```

## Usage

### Create Tickets Using Natural Language

Simply describe your needs to Terry:

```bash
python terry.py nl "We need to scale the Aurora DB and Sidekiq memory because the birthday service is hitting performance issues"
```

### Handle Failed Ticket Creation

If GitHub is unavailable or rate-limited, Terry will cache the ticket locally:

```bash
# List cached tickets
python terry.py cache list

# Retry all cached tickets
python terry.py cache retry --all

# Retry specific ticket
python terry.py cache retry --file /var/tmp/terry_cache/issue_123.json
```

### Configuration Management

```bash
# View current config
python terry.py config

# Update GitHub repo
python terry.py config --github-repo "new-org/new-repo"
```

## Environment Variables

Configure these in your `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_REPO=org/repo_name  # e.g., "your-org/your-repo"
```

## Cache Location

Failed tickets are cached in `/var/tmp/terry_cache/` and can be retried later when GitHub is available.

## Example Output

Terry generates tickets with:
- Clear technical titles
- Detailed descriptions
- Priority levels (P0-P3)
- Impact areas
- Acceptance criteria
- Witty remarks about corporate life
- Automatic GitHub issue creation

## Coming Soon

- Integration with more issue tracking systems
- Project and sprint management
- Enhanced natural language capabilities
- More corporate buzzwords and sarcastic templates

## Troubleshooting

1. If ticket creation fails:
   - Check your GitHub token permissions
   - Verify your repo name is correct
   - Look for cached tickets: `terry cache list`

2. If OpenAI fails:
   - Verify your API key
   - Check your OpenAI account status

3. For other issues:
   - Check your configuration: `terry config`
   - Verify environment variables are set
   - Look for error messages in Terry's output

## Contributing

Feel free to contribute more corporate buzzwords, sarcastic templates, or actual code improvements. Terry appreciates your synergy in leveraging our collective bandwidth to move the needle on this project.
