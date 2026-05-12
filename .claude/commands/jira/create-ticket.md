---
description: Create a new Jira ticket with proper structure and formatting
argument-hint: [summary] [optional: epic-key]
---

# Create Jira Ticket

@jira-ticket-manager

## Task
Create a new Jira ticket with the following details:

**Summary**: $ARGUMENTS

## Requirements
1. Parse the summary and any additional requirements from the arguments
2. Use the JiraDocumentBuilder to create a well-formatted description
3. Apply appropriate labels based on the ticket content
4. If an epic key is provided, link the ticket to that epic
5. Set appropriate issue type (Story, Task, or Bug based on content)
6. Add comprehensive acceptance criteria
7. Confirm successful creation and provide the ticket key

## Output Format
After creation, provide:
- Ticket key (e.g., PROJ-123)
- Direct link to the ticket
- Summary of what was created
