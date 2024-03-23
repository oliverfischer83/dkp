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



