View or manage jira-tool configuration.

Usage: /config [subcommand]

Execute: `jira-tool config $ARGUMENTS`

Subcommands:
- `show` - Display current configuration (default)
- `set <key> <value>` - Set a config value
- `get <key>` - Get a specific value
- `unset <key>` - Remove a config value
- `path` - Show config file location
- `edit` - Open config in editor

Examples:
```bash
jira-tool config                      # Show all config
jira-tool config set project PROJ
jira-tool config get base_url
```

Config file: ~/.config/jira-tool/config.yaml
