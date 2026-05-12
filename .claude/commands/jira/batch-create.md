---
description: Create multiple tickets from a requirements list (parallel)
argument-hint: [epic-key] [requirements-description]
---

# Batch Create Jira Tickets (Parallel)

## Task

Create multiple Jira tickets in parallel under an epic using a team of agents.

**Input**: $ARGUMENTS

---

## Phase 1 - Parse & Plan (you do this)

1. **Extract the epic key** from the first token of `$ARGUMENTS` (e.g., `PROJ-42`).
2. **Fetch epic details** using `temet-jira get <epic-key>` to understand the context (summary, description, project key, labels).
3. **Parse the remaining arguments** into individual ticket specs. Support these input formats:
   - **Numbered list**: "1) Implement OAuth, 2) Add session management, 3) Create profile endpoint"
   - **Bullet points**: "- Feature A\n- Feature B\n- Feature C"
   - **Free-form**: "We need authentication, user profiles, and API endpoints" -- infer discrete tickets from the text
4. **For each ticket**, prepare a spec object with:
   - `summary`: Clear, specific ticket title (imperative form, e.g., "Implement OAuth flow")
   - `description_outline`: Bullet points of what the ticket covers, plus acceptance criteria
   - `type`: One of Story, Task, or Bug (default to Task if unclear)
   - `labels`: Relevant labels inferred from the epic and content
   - `epic_key`: The parent epic key
   - `project_key`: Extracted from the epic key prefix

5. **Create tasks** using TaskCreate -- one task per ticket spec. Each task subject should be "Create ticket: <summary>". Include the full spec and epic context in the task description.

---

## Phase 2 - Parallel Ticket Creation

**IMPORTANT**: Spawn ALL writers simultaneously, do not wait between spawns.

For each ticket spec, spawn a teammate using the `batch-tickets` team:

- **Agent name**: `ticket-writer-N` (where N is 1, 2, 3, ... matching the ticket number)
- **Subagent type**: `general-purpose`
- **Up to 4 agents in parallel**. If there are more than 4 tickets, batch them: spawn the first 4, wait for them to complete, then spawn the next batch.

**Instructions to send each writer** (via SendMessage after spawn):

Include ALL of the following in your message to each writer:

```
You are creating a single Jira ticket. Here are your instructions:

## Your Ticket Spec
- Summary: <summary>
- Type: <type>
- Labels: <labels>
- Project: <project_key>
- Epic: <epic_key>

## Epic Context
<paste the epic summary and description here so the writer understands the broader context>

## Description Outline
<paste the description_outline bullets>

## Instructions

1. Create the ticket using temet-jira:
   ```bash
   temet-jira create --project <project_key> --summary "<summary>" --type <type> --description "<description>"
   ```

2. The description MUST use Atlassian Document Format (ADF). Structure it as:
   - **Overview** paragraph explaining what this ticket covers
   - **Requirements** / **Acceptance Criteria** as a bullet list
   - Keep it concise but specific

3. After creating the ticket, link it to the epic:
   ```bash
   temet-jira link <new-ticket-key> <epic_key> --type "Epic-Story"
   ```

4. Add labels if any:
   ```bash
   temet-jira label <new-ticket-key> add <label1> <label2>
   ```

5. When done, update your task as completed and send me (team-lead) a message with:
   - The ticket key (e.g., PROJ-123)
   - The summary
   - Whether it succeeded or failed (and why if failed)
```

---

## Phase 3 - Summary (you do this)

After all writers have reported back:

1. **Collect results** from all writer messages.
2. **Present a summary table**:

```
## Batch Create Results

**Epic**: <epic-key> - <epic-summary>
**Tickets created**: X / Y

| # | Key | Summary | Status |
|---|-----|---------|--------|
| 1 | PROJ-101 | Implement OAuth flow | Created |
| 2 | PROJ-102 | Add session management | Created |
| 3 | -- | Create profile endpoint | FAILED: reason |
```

3. **Report any failures** with error details.
4. **Shut down the team** by sending shutdown requests to all writers.
