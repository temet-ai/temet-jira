---
description: Show all active tickets assigned to you
---

# My Jira Tickets

@jira-ticket-manager

## Task
Retrieve and display all active tickets assigned to the current user.

## Requirements
1. Use the correct JQL query: `assignee = currentUser() AND project = PROJ AND status NOT IN (Done, Closed)`
2. Fetch tickets with relevant fields: summary, status, priority, epic link
3. Format the output in a readable table or list
4. Group tickets by status if helpful (To Do, In Progress, In Review, etc.)
5. Include ticket keys with direct links

## Important Notes
- **ALWAYS** use `status` field, NOT `resolution` field
- Exclude completed tickets (Done, Closed statuses)
- Common active statuses: To Do, In Progress, In Review, Testing, Blocked

## Output Format
Display:
- Total count of active tickets
- Grouped by status
- For each ticket:
  - Key and direct link
  - Summary
  - Priority
  - Epic (if linked)
