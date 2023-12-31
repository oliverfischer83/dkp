# DKP
- GO live
  - steps (use copilot)
    - setup local dev dynamodb
    - import/export data into/from dynamodb
    - create GUI to insert data
    - create docker image
    - test app runner manually
    - create build/deployment pipelines
    - test app runner automatically
  - provide data on dynamodb (not local dir anymore)
  - how to auto-update the browser?
    - periodically reload page or webhooks using github actions and display warning?
    - show "last update since" big on screen (Timestamp, last boss)
  - admin function to filter rclootcouncil data and get only new entries (use case: update data during raid)
  - test run
    - process if new char is in raid and gets loot
    - process cleaning up data
    - load testing, caching needed?
  - deployment
  - safety
  - security
- code quality
  - unit tests for balance functions
  - constants for string names
- nice to have
  - show item link: feature coming Jan 2024
  - fix: m+ chars in raid report, test with report vF2C8crAdja1QKhD
    - or show warning and abort if m+ logs in report
  - fix: when passing invalid report ids
- safety
  - database backup on github (/data/backup/<tablename>-<timestamp>.json)
    - delete backups older than 90d
    - deletion protection for prod tables on
    - ... or just pay 4 cents per month for aws backup
  - automated setup for environments  
- security:
  - pen test?
  - always validate input data, to secure against code injection
  - inspect AWS Web Application Firewall
  - AWS access keys
    - cloud
      - technical AWS user, credentials stored in github secrets
        - limit access to dynamodb and app runner
        - script to create automatically
      - use service linked roles for app-runner to have managed access-keys included: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html?icmpid=docs_iam_console
    - local
      - use aws-toolkit to have managed temporary access keys
  - basic auth for admin section

# Github actions
- create-env
  - select env and artifact
  - create and init dynamodb tables
  - create app runner
  - smoke test
- delete-env
  - select env
  - delete app runner
  - delete dynamodb tables
- test
  - automatically
  - checkout + test
- build
  - manually, to save costs
  - checkout + test + tag + push
  - tag: create build number and tag commit
  - push: push tagged artifact to ECR
- deploy
  - manually, to save costs
  - select env and artifact

# AWS
- access key management
  - should not be necessary to manage them manually anymore
  - local development
    - setup IAM Identity Center User > use via AWS toolkit inside of VSCode
    - how to: https://www.youtube.com/watch?v=_KhrGFV_Npw
    - cannot create permision set: see support issue
    - workaround:
      - use manually created access key
      - remove key and ~/.aws/credentials file when not needed anymore
  - app runner
    - use service-linked roles for temporary access keys

