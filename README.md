# DKP

## Design decisions

### Platform
- choosing App Runner over Elastic Beanstalk over EC2 over ECS (managed Kubernetes)
- outsourcing the platform management, just giving the application code and configuration
- cheap, easy to setup and manage

### Database
- dealing with json data only, so no relational database needed
- using AWS nosql database, mostly for educational reasons
- choosing DynamoDB over DocumentDB, because its cheap and easy to setup

### Database backup
- saving production data as files in github directory once a day, because no sensitive data exists
- can be reused for development, testing and database initialization
- using GitHub API for educational reasons

## Setup local environment

### Python
```bash
conda create -n dkp python=3.12 -y
conda activate dkp

pip install pip-tools
pip-compile --all-extras pyproject.toml
pip-sync
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

### Start in terminal
```bash
cd ~/Projects/private/dkp  # path to repository root dir
python -m streamlit run frontend/01_overview.py
```

### Start in docker
```bash
cd ~/Projects/private/dkp  # path to repository root dir
```

#### Build image
```bash
docker build -t dkp .
```

#### Start detached
```bash
docker run --name dkp -p 8080:8501 -d dkp  # start
docker stop dkp && docker rm dkp           # stop and remove
```

#### Start interactive
```bash
docker run --name dkp -p 8080:8501 -it --rm dkp /bin/bash
```
