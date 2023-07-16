## PR-vigilante

### Description:
Python application to track down and automatically mark pull request messages  
in Slack channel as approved or merged after reviewing/merging  
associated pull request in GitHub. If multiple PRs are found in a single message   
it will be marked as approved or merged after all the pull requests will be approved/merged.  

Application is built around [Python Slack SDK](https://slack.dev/python-slack-sdk/).  
GitHub API caching is implemented based on conditional requests and local cache client.

### Required Slack token permissions:
`channels:history`, `groups:history`, `im:history`, `mpim:history`,  
`reactions:read` and `reactions:write` are required scopes for Slack API token.

### Required GitHub token permissions:
`repo` is the required scope for Github API token (grants full access to public and private repositories).
Alternatively, `public_repo` can be used if repositories to track are public.

### Things to consider:
1. Slack API rate limit tiers - based on methods used, e.g.  
    https://api.slack.com/methods/conversations.history and  
    https://api.slack.com/methods/reactions.add etc
2. GitHub API rate limits

### Application structure:
```
├── clients    - clients (github, slack, local cache etc)
├── main.py    - main entrypoint
├── parsers    - slack / github data parsers
├── processors - message processors
├── utils.py   - shared functions 
```

### Contribution:
1. Define new parsers in `/parsers` directory
2. Define new worker thread in `/processors`
3. Add new thread and queue into `main.py`

### High-level of processing:
```
                    --> [ Queue ] -- processors.1 
                  / ..
main thread ---> [ Queue ] -- processors.2
                  \ ..
                    --> [ Queue ] -- processors TBD
                    
Where parsing of messages based on conditions happens before populating consumers' queue
```


### Build and publish:
```commandline
image_tag='slack-tools:<version>'
repository='<my_repository>'
platform='linux/amd64'

docker buildx build --platform "$platform" -t "$image_tag" .
docker tag "$image_tag" "$repository/$image_tag"
docker push "$repository/$image_tag"
```
change Helm `Chart.yaml` `version` and `appVersion` values accordingly.

### Apply & Delete:
```
helmfile apply --interactive --kube-context <context> (uses current context by default)
helmfile delete --interactive
```

### Usage:
```commandline

❯ python main.py --help
usage: main.py [-h] [--config_file CONFIG_FILE] --slack_api_token SLACK_API_TOKEN --slack_channel_id SLACK_CHANNEL_ID --slack_time_window_minutes SLACK_TIME_WINDOW_MINUTES [--slack_approved_reaction_name SLACK_APPROVED_REACTION_NAME]
               [--slack_merged_reaction_name SLACK_MERGED_REACTION_NAME] [--slack_github_error_reaction_name SLACK_GITHUB_ERROR_REACTION_NAME] --github_api_token GITHUB_API_TOKEN [--cache_folder_path CACHE_FOLDER_PATH] --sleep_period_minutes
               SLEEP_PERIOD_MINUTES [--max_retries MAX_RETRIES] [--dry_run] [--debug]

optional arguments:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
  --slack_api_token SLACK_API_TOKEN
                        [env var: SLACK_API_TOKEN]
  --slack_channel_id SLACK_CHANNEL_ID
                        [env var: SLACK_CHANNEL_ID]
  --slack_time_window_minutes SLACK_TIME_WINDOW_MINUTES
                        [env var: SLACK_TIME_WINDOW_MINUTES]
  --slack_approved_reaction_name SLACK_APPROVED_REACTION_NAME
                        [env var: SLACK_APPROVED_REACTION_NAME]
  --slack_merged_reaction_name SLACK_MERGED_REACTION_NAME
                        [env var: SLACK_MERGED_REACTION_NAME]
  --slack_github_error_reaction_name SLACK_GITHUB_ERROR_REACTION_NAME
                        [env var: SLACK_GITHUB_ERROR_REACTION_NAME]
  --github_api_token GITHUB_API_TOKEN
                        [env var: GITHUB_API_TOKEN]
  --cache_folder_path CACHE_FOLDER_PATH
                        [env var: CACHE_FOLDER_PATH]
  --sleep_period_minutes SLEEP_PERIOD_MINUTES
                        [env var: SLEEP_PERIOD_MINUTES]
  --max_client_retries MAX_CLIENT_RETRIES
                        [env var: MAX_CLIENT_RETRIES]
                        [env var: MAX_RETRIES]
  --dry_run             [env var: DRY_RUN]
  --debug               [env var: DEBUG]

Args that start with '--' (eg. --slack_api_token) can also be set in a config file (./config.yaml or specified via --config_file). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi).
If an arg is specified in more than one place, then commandline values override environment variables which override config file values which override defaults.
```

### TODO:
- [x] Support lookup of PRs inside of slack threads
- [x] Replace GHApi with own GitHub Client to support conditional requests
- [x] GitHub API caching based on conditional requests (etag/last-modified headers)
- [x] Local FileCache client
- [x] Pub-sub thread model instead of Async workarounds
- [x] Config file support
- [x] Additional reaction based on merged PR state
- [x] New Helm chart allowing persistence
- [ ] Load worker threads dynamically (app -> framework)
- [ ] Add configmap support to the Helm chart
