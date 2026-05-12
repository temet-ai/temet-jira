# Jira Document Formatting (ADF - Atlassian Document Format)

## Overview

ADF (Atlassian Document Format) is the standard markup for rich text in Jira descriptions and comments. Use ADF when creating or updating tickets to add formatting, links, lists, code blocks, and structured content.

## Table of Contents

- Basic Formatting
- Lists & Nesting
- Links & References
- Code & Technical Content
- Tables & Complex Layouts
- Common Patterns

---

## Basic Formatting

### Headings

Organize ticket descriptions with clear hierarchy:

```
## Summary
Brief one-liner about what needs to be done

## Background
Why this ticket exists

## Requirements
What's needed to complete this

## Acceptance Criteria
How to verify it's done
```

### Text Styling

- **Bold**: `**text**` for emphasis
- *Italic*: `*text*` for asides
- `Code`: `` `text` `` for inline code references
- ~~Strikethrough~~: `~~text~~` for removed content

### Line Breaks & Whitespace

- Empty lines create paragraph breaks
- Use consistent indentation for nested content
- Leave blank lines before/after code blocks for readability

---

## Lists & Nesting

### Unordered Lists

```
- First item
- Second item
  - Nested item
  - Another nested
- Third item
```

### Ordered Lists

```
1. First step
2. Second step
   1. Substep
   2. Another substep
3. Third step
```

### Mixed Lists

Combine ordered and unordered for complex workflows:

```
1. Setup phase
   - Install dependencies
   - Configure environment
2. Development phase
   - Write feature code
   - Add tests
3. Review phase
   - Code review
   - Merge to main
```

---

## Links & References

### Jira Ticket Links

Reference other tickets inline:

```
Related to PROJ-100
Blocked by PROJ-101
Depends on PROJ-102
```

### External Links

```
[Document Title](https://example.com/path)
[API Reference](https://api.example.com/docs)
```

### User Mentions

Tag team members for visibility:

```
cc @username
@another-user can review this
```

---

## Code & Technical Content

### Inline Code

For class names, method names, or brief code references:

```
Use the `AuthService.authenticate()` method
The `user_id` field is required
```

### Code Blocks

For larger code samples or configurations:

```python
def authenticate(user_id):
    """Authenticate user and return token"""
    return AuthService.authenticate(user_id)
```

### Technical Specifications

```
**API Endpoint:** POST /api/v1/auth/token
**Request:** { "user_id": "string", "password": "string" }
**Response:** { "token": "jwt", "expires_in": 3600 }
**Status Codes:** 200 (success), 401 (invalid), 500 (error)
```

---

## Tables & Complex Layouts

### Simple Requirement Tables

```
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| user_id | string | Yes | Unique identifier |
| email | string | Yes | Must be valid email |
| role | enum | No | admin, user, guest |
```

### Comparison Tables

```
| Feature | Option A | Option B | Decision |
|---------|----------|----------|----------|
| Complexity | Low | High | Choose A |
| Performance | Standard | Optimized | Choose B for perf |
| Cost | $X | $2X | Budget dictates |
```

### Acceptance Criteria Table

```
| Criterion | Status | Notes |
|-----------|--------|-------|
| Endpoint returns 200 | ☐ | Test with Postman |
| Response includes token | ☐ | Check format |
| Token expires after 1h | ☐ | Verify expiry logic |
| Invalid credentials return 401 | ☐ | Test error cases |
```

---

## Common Patterns

### Epic Description Pattern

```
## Overview
[1-2 sentence summary of epic value]

## Goals
- Achieve goal 1
- Enable goal 2
- Support goal 3

## Scope
### Included
- Feature A
- Feature B

### Out of Scope
- Feature X (defer to later)
- Feature Y (not prioritized)

## Success Metrics
- Metric 1: Target value
- Metric 2: Target value

## Timeline
- Phase 1 (Week 1-2): Foundation
- Phase 2 (Week 3-4): Integration
- Phase 3 (Week 5-6): Polish
```

### User Story Pattern

```
## As a [user type]
I want to [action]
So that [benefit]

## Acceptance Criteria
1. [ ] Given [precondition], when [action], then [result]
2. [ ] Given [precondition], when [action], then [result]
3. [ ] Edge case: [scenario] → [expected behavior]

## Technical Notes
- Implementation approach
- Potential risks
- Dependencies
```

### Bug Report Pattern

```
## Description
[Clear description of the bug]

## Steps to Reproduce
1. Do this
2. Then do that
3. Observe the issue

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- Browser: Chrome 120
- OS: macOS 14.2
- App Version: 1.2.3

## Attachments
[Screenshots, logs, error messages]
```

### Task Pattern

```
## Overview
[What needs to be done]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Implementation Notes
[Technical approach, gotchas]

## Testing
[How to verify completion]

## Related Tickets
PROJ-100, PROJ-101
```

---

## Best Practices

**Structure:**
- Start with clear summary/background
- Use headings for major sections
- Nest requirements under categories
- End with acceptance criteria

**Clarity:**
- Use second person ("you" not "developer")
- Be specific with examples
- Link to related tickets
- Include edge cases

**Maintenance:**
- Update description if requirements change
- Mark completed items with ✓
- Archive old patterns in comments
- Keep critical info in description (not comments)

**Formatting:**
- Use consistent heading levels (## for main, ### for sub)
- Leave blank lines before/after code blocks
- Use tables for structured data
- Avoid excessive bold/italic (confuses priorities)
