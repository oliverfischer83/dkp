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
pip install --editable=.[dev]  # installs dkp app incl. dev extras in edit mode (. indicates, where to find the setup file)
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

## page reload
- auto refresh page
- on loot data upload, clients get signal to refresh or waning banner that data outdated
- make optional

## Scenarios:
- RCLootCouncil not useable at all (through bug, or similiar)
  - add entries by hand on admin page, define simple default values for other fields of RawLoot
- No Masterlooter (ID already taken, cant distribute loot)
  - do auction like bidding and note down winner
  - manually add entries afterwards
- Normal use case:
  - click Raid button: raid entry, status "started"
  - add report id (live log)
  - add loot: -> failed: unknown character
  - add character in editor
  - try again add loot: -> failed: invalid note
  - fix note in editor
  - try again add loot: -> succeeded
  - click on raid button: status "finished" (adds 50pt. to balance)
- use case "Same Day"
  - add loot: raid entry, status "started"
- use case "Next Day"
  - add loot: raid entry, status "finished"

## misc
- fix: m+ chars in raid report, test with report vF2C8crAdja1QKhD
  - or show warning and abort if m+ logs in report
- find other cloud hosting as backup
- after uploading a loot log, show entries in raid day below (select date automatically)
- code quality
  - unit tests for balance functions
  - constants for string names
  - remove "# type: ignore"
- add status flag to Player
  - paused: dont show on balance view
- unify data validation on export upload and loot editor changes

## Checklist
- Raid button
  - start Raid:
    - create raid entry, set status started
    - show checklist, show warning for each open checklist item
  - finish Raid:
    - set status finished
    - get attendees from report one last time
    - add 50 pt. to balance
    - ends automatically on next day (german timezone)
- checklist items
  - video started
  - live log started
  - all attendees have RCLootCouncil started
  - add new attendees

## Info Page
- rules (copy from Excel Sheet)
- how to install and configure Addon RCLootCouncil using screenshots

## Character Editor
- on loot upload or raid finished ...
  - if character missing
    - don't save, show warning for every character missing, keep input data in field
    - try getting name
- on adding new player (chars optional)
  - should be shown on balance view with 100 pt.
- disable function to remove player somehow

## Raid Editor
- status
  - started (log added same day or raid started manually)
  - finished (log added from past or raid stopped manually)
- report id
  - show warning if raid finished and attendees/report id missing
  - (maybe) if unknown character

