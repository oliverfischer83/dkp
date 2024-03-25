# DKP

## Design decisions

### Platform
- outsourcing the platform management, just giving the application code and configuration
- sadly cant use AWS App Runner, because websockets are not supported (needed by Streamlit)
- choosing Streamlit Community Cloud over Elastic Beanstalk
- cheap, easy to setup and manage

### Database
- dealing with json data only, so no relational database needed
- using AWS nosql database, mostly for educational reasons
- choosing DynamoDB over DocumentDB, because its cheap and easy to setup

### Database backup
- saving production data as files in github directory once a day, because no sensitive data exists
- can be reused for development, testing and database initialization
- using GitHub API for educational reasons

### Architecture
- form data validation happens in app, not in views
- clients don't contain any business logic
- data formats
  - dataframes for views
  - dataframes and list of dics for transformation/data-manipulation
  - json as storage format of data files (should be converted right before pushing to github.com)

## Setup local environment

### Python
```bash
conda create -n dkp python=3.12 -y
conda activate dkp

pip install pip-tools
pip-compile --all-extras pyproject.toml
pip-sync
pip install --editable=.[dev]
```

### Configuration
Dotenv file at "<workspace>/.env" with following content:
```bash
WCL_CLIENT_ID=...
WCL_CLIENT_SECRET=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=eu-central-1
```

### Start locally
```bash
cd ~/Projects/private/dkp
python -m streamlit run src/dkp/01_overview.py
```

# TODO
- GO live
  - test run
    - process if new char is in raid and gets loot
    - process cleaning up data
  - adding player and characters via admin page
  - manage raid list in separate json file
  - extract raids from config
  - extract player from config
  - remove reload button
  - before uploading loot data in admin page, validate values:
    - if response=Gebot, then note=[0-9]+
    - characters are known
  - checklist (video on, live log on, loot-council uptodate, ...)
  - status sign, e.g. traffic jam lights: green=raid active, red=raid still active need to close, none=ok
  - scenario:
    - cannot do master looter (because ID already taken), so cannot loot, so cannot use RCLootCouncil
    - do auction like bidding, and note down winner
    - manually add entries afterwards
    - use Excel sheet if necessary
- code quality
  - unit tests for balance functions
  - constants for string names
- nice to have
  - fix: m+ chars in raid report, test with report vF2C8crAdja1QKhD
    - or show warning and abort if m+ logs in report
