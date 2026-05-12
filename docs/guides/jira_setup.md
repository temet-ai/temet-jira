# Jira Setup Guide

This guide walks you through setting up authentication for the `temet-jira` CLI.

## Prerequisites

- A Jira Cloud instance (e.g., `https://your-company.atlassian.net`)
- An Atlassian account with access to your Jira instance
- Python 3.11+

## Step 1: Generate Your Jira API Token

### Where to Get Your Token

1. Navigate to your Atlassian account security settings:
   ```
   https://id.atlassian.com/manage-profile/security/api-tokens
   ```

2. Or manually navigate:
   - Go to [Atlassian Account](https://id.atlassian.com)
   - Click your profile icon (top right)
   - Select **Account Settings**
   - Click **Security** in the left sidebar
   - Select **Create and manage API tokens**

### Generate the Token

1. Click **Create API token**
2. Enter a descriptive label (e.g., "temet-jira CLI - Development Laptop")
3. Click **Create**
4. **Copy the token immediately** - you won't be able to see it again!

> **Important:** As of December 2024, all API tokens must have an expiration date (1-365 days). Plan to rotate your tokens regularly.

## Step 2: Choose Your Usage Method

### Global Install (Recommended)

Install once, use anywhere on your system:

```bash
uv tool install temet-jira
```

Then use from any directory:
```bash
temet-jira [command]
```

### Development Mode

For contributors working on the source code:

```bash
uv sync
uv run temet-jira [command]
```

## Step 3: Configure Your Environment

### Option A: Environment Variables (Recommended)

This option allows you to use `temet-jira` from **any directory**.

#### macOS/Linux

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export JIRA_BASE_URL=https://your-company.atlassian.net
export JIRA_USERNAME=your-email@example.com
export JIRA_API_TOKEN=your-api-token-here

# Optional defaults
export JIRA_DEFAULT_PROJECT=PROJ
export JIRA_DEFAULT_COMPONENT="Component Name"
```

Then reload your shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

**Note:** In shell scripts, quotes are optional for simple values but required for values with spaces.

#### Windows (PowerShell)

Add to your PowerShell profile (`$PROFILE`):

```powershell
$env:JIRA_BASE_URL = "https://your-company.atlassian.net"
$env:JIRA_USERNAME = "your-email@example.com"
$env:JIRA_API_TOKEN = "your-api-token-here"
```

Or set system environment variables through:
- Settings → System → About → Advanced system settings → Environment Variables

### Option B: Interactive Setup Wizard

Run the setup wizard to configure credentials interactively:

```bash
temet-jira setup
```

Credentials are saved to `~/.config/temet-jira/config.yaml`.

## Step 4: Verify Your Setup

Test your authentication:

```bash
# Using the CLI
temet-jira search "project = YOUR_PROJECT" --limit 1

# Or test directly with curl
curl -u "$JIRA_USERNAME:$JIRA_API_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/myself" | jq
```

If successful, you should see your user information or search results.

## Step 5: Start Using the Tool

```bash
# Get issue details
temet-jira get PROJ-123

# Search for issues
temet-jira search "project = PROJ AND status = Open"

# Create an issue
temet-jira create "Bug: Login not working" --type Bug

# Export to CSV
temet-jira export PROJ --format csv -o issues.csv
```

For more commands, see the main [README.md](../../README.md) or run:
```bash
temet-jira --help
```

## Security Best Practices

### DO:

- **Use descriptive labels** for tokens (e.g., "MacBook Pro - Development")
- **Set reasonable expiration dates** (90 days for regular use, 30 days for testing)
- **Store tokens in environment variables or secret managers** (not in code)
- **Rotate tokens regularly** (before expiration)
- **Revoke tokens** when changing jobs or devices
- **Use scoped tokens** when possible (for limited permissions)
- **Keep `.env` files in `.gitignore`**

### DON'T:

- **Never commit tokens to git** (check with `git log -p | grep JIRA_API_TOKEN`)
- **Never share tokens** (create separate tokens for each person)
- **Never use your password** (deprecated since 2019)
- **Never use SSO credentials** for API authentication
- **Never hardcode tokens** in scripts or applications
- **Never use tokens in URLs** (use headers instead)

## Troubleshooting

### Error: "401 Unauthorized"

**Cause:** Invalid or expired token, incorrect credentials

**Solutions:**
1. Verify your email matches the token owner: `echo $JIRA_USERNAME`
2. Check if token expired: [Manage API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
3. Regenerate a new token and update your configuration
4. Ensure you're using the token, not your password

### Error: "403 Forbidden"

**Cause:** Insufficient permissions

**Solutions:**
1. Verify you have access to the project in Jira's web UI
2. Check if the resource requires specific permissions
3. For admin operations, ensure you have admin rights
4. Contact your Jira administrator for permission changes

### Error: "404 Not Found"

**Cause:** Incorrect base URL or resource doesn't exist

**Solutions:**
1. Verify your `JIRA_BASE_URL` is correct (check the URL in your browser)
2. Ensure the issue key or project key exists
3. Check for typos in the resource path

### Error: "429 Too Many Requests"

**Cause:** Rate limiting

**Solutions:**
1. Wait a few minutes before retrying
2. Reduce the frequency of API calls
3. Consider batching operations
4. Check if you're inadvertently making duplicate calls

### Token Not Working After Setup

**Check configuration:**
```bash
# Verify environment variables are set
echo "URL: $JIRA_BASE_URL"
echo "Username: $JIRA_USERNAME"
echo "Token length: ${#JIRA_API_TOKEN}"  # Should be > 20

# Test with curl
curl -v -u "$JIRA_USERNAME:$JIRA_API_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/myself"
```

**Common issues:**
- Whitespace in token (copy-paste errors)
- Using wrong email address
- Token expired
- Using Jira Server URL instead of Jira Cloud

## Token Expiration and Rotation

### When to Rotate

- **Before expiration** (check [token management](https://id.atlassian.com/manage-profile/security/api-tokens))
- **When compromised** (immediately revoke and create new)
- **When changing devices** (revoke old device tokens)
- **Regularly** (recommended: every 90 days)

### How to Rotate

1. Generate a new token (keep the old one active)
2. Update your configuration with the new token
3. Test the new token
4. Revoke the old token
5. Update any automation or scripts

### Rotation Checklist

- [ ] Generate new token with expiration date
- [ ] Update `JIRA_API_TOKEN` in environment/`.env` file
- [ ] Test with `temet-jira` CLI
- [ ] Update CI/CD secrets (if applicable)
- [ ] Update documentation/scripts with new token
- [ ] Revoke old token
- [ ] Set calendar reminder for next rotation

## Advanced Configuration

### Using Service Accounts (Team/Organization Use)

For shared integrations or CI/CD:

1. Create a service account in [Atlassian Admin](https://admin.atlassian.com)
2. Navigate to: **Directory** → **Service accounts** → **Create service account**
3. Generate an API token for the service account
4. Use the service account email and token for `JIRA_USERNAME` and `JIRA_API_TOKEN`

### Using Scoped Tokens (Enhanced Security)

For limited-permission scenarios:

1. When creating a token, select **Create a scoped token**
2. Choose specific resources and permissions
3. Tokens are limited to selected capabilities only

**Use scoped tokens for:**
- Read-only data exports
- Specific project access
- Limited automation tasks
- Third-party integrations

### Secret Management (Production Use)

For production environments, use a secret manager:

**HashiCorp Vault:**
```bash
vault kv get secret/jira/api-token
export JIRA_API_TOKEN=$(vault kv get -field=token secret/jira/api-token)
```

**AWS Secrets Manager:**
```bash
aws secretsmanager get-secret-value --secret-id jira/api-token \
  --query SecretString --output text | jq -r .token
```

**1Password CLI:**
```bash
export JIRA_API_TOKEN=$(op read "op://Personal/Jira/api-token")
```

## Additional Resources

- **Atlassian API Token Documentation:** https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/
- **Jira Cloud REST API v3:** https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/
- **Jira Cloud Rate Limits:** https://developer.atlassian.com/cloud/jira/platform/rate-limiting/
- **Basic Auth for REST APIs:** https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/

## Need Help?

- **Project Issues:** [GitHub Issues](https://github.com/temet-ai/temet-jira/issues)
- **Jira Support:** [Atlassian Support](https://support.atlassian.com)
- **Community:** [Atlassian Community](https://community.atlassian.com)

---

**Last Updated:** November 10, 2025
**Applies to:** Jira Cloud (REST API v3)
**Note:** This guide does not apply to Jira Server or Jira Data Center installations.
