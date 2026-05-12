View or manage temet-jira configuration.

Usage: /config [subcommand]

Execute: `temet-jira config $ARGUMENTS`

Subcommands:
- `show` - Display current configuration (default)
- `set <key> <value>` - Set a config value
- `get <key>` - Get a specific value
- `unset <key>` - Remove a config value
- `path` - Show config file location
- `edit` - Open config in editor

Examples:
```bash
temet-jira config                      # Show all config
temet-jira config set project PROJ
temet-jira config get base_url
```

Config file: ~/.config/temet-jira/config.yaml
