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

### Start locally
```bash
cd ~/Projects/private/dkp
python -m streamlit run src/dkp/streamlit/01_overview.py
```

### Start in docker

#### Build image
```bash
cd ~/Projects/private/dkp
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

#### Upload image
```bash
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 243351289711.dkr.ecr.eu-central-1.amazonaws.com
BUILD_TAG=1234  # some build number
docker tag dkp:latest 243351289711.dkr.ecr.eu-central-1.amazonaws.com/dkp:$BUILD_TAG
docker push 243351289711.dkr.ecr.eu-central-1.amazonaws.com/dkp:$BUILD_TAG
```

