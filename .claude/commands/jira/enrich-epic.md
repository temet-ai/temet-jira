---
description: Enrich an existing epic with complete structure and breakdown
argument-hint: [epic-key]
---

# Enrich Jira Epic

@jira-ticket-manager

## Task
Enrich and enhance epic: $ARGUMENTS

## Requirements
1. Fetch the current epic details
2. Analyze existing content and structure
3. Enhance the epic description with:
   - **📋 Overview**: Clear summary of what this epic achieves
   - **🎯 Goals**: Specific, measurable objectives
   - **📊 Scope**: What's included and excluded
   - **✅ Success Criteria**: How we measure completion
   - **🔗 Dependencies**: Related epics or external dependencies
4. Use JiraDocumentBuilder for proper ADF formatting
5. Apply consistent formatting (emoji prefixes, panels, bullet lists)
6. Review existing child tickets and suggest improvements:
   - Missing tickets for incomplete coverage
   - Tickets that should be split or merged
   - Proper ticket organization and labeling
7. Update the epic with enhanced content
8. Provide summary of changes made

## Output Format
After enrichment, provide:
- What was added/enhanced
- Link to updated epic
- Recommendations for child tickets
- Any gaps or issues identified
