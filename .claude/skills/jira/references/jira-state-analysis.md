# Jira State Duration Analysis & Workflow Optimization

## Overview

Analyze how long tickets spend in each workflow state to identify bottlenecks, optimize processes, and improve delivery metrics. This guide covers state duration calculation, business hours tracking, and workflow insights.

## Table of Contents

- State Duration Basics
- Business Hours Tracking
- Identifying Bottlenecks
- Cycle Time Analysis
- Workflow Patterns
- Improvement Strategies

---

## State Duration Basics

### What is State Duration?

State duration measures how long a ticket stays in a particular workflow state (To Do, In Progress, Done, etc.).

**Example:**
```
Ticket: PROJ-123
Created: 2024-01-15 09:00 (To Do)
Moved to In Progress: 2024-01-16 14:00 (1 day 5 hours)
Moved to Review: 2024-01-18 10:00 (1 day 20 hours)
Moved to Done: 2024-01-19 16:00 (1 day 6 hours)
```

### Measuring Duration

**Calendar days:** Simple count of all days (includes nights, weekends)
- From 1/15 to 1/19: 4 days

**Business hours:** Only count 9 AM–5 PM, Monday–Friday
- More accurate for work metrics
- 1/15 to 1/16: 8 hours
- 1/16 to 1/18: 16 hours
- 1/18 to 1/19: 8 hours
- **Total:** 32 business hours

### Extracting State Data

Use changelog expansion to get state transitions:

```bash
# Export with changelog for state analysis
temet-jira export "project = PROJ" \
  --expand changelog \
  --format json \
  --output export.json

# Analyze the exported data
temet-jira analyze state-durations export.json \
  --business-hours \
  --output analysis.csv
```

---

## Business Hours Tracking

### Why Business Hours Matter

Calendar days inflate metrics due to weekends and off-hours work. Business hours reveal actual productivity:

```
Ticket stuck 3 calendar days over weekend:
- Friday 5 PM to Monday 9 AM = 1 business hour
- More realistic of actual work stoppage

Ticket in progress 10 calendar days:
- But only 40 business hours = 1 work week
- Accurate staffing requirement
```

### Configuring Business Hours

Default: 9 AM–5 PM, Monday–Friday

**Custom schedules:**
```
Standard (40 hours/week):
  Monday-Friday: 9 AM-5 PM (8 hours/day)

Compressed (32 hours/week):
  Monday-Friday: 9 AM-1 PM (4 hours/day)

Flexible (varies):
  Define custom hours per project
```

### Weekend Handling

By default, weekends and holidays are excluded:

```
State Started: Friday 4 PM
State Ended: Monday 10 AM

Calendar days: 3 (Fri, Sat, Sun, Mon)
Business hours: 2 (4 PM-5 PM Friday + 9 AM-10 AM Monday)
```

---

## Identifying Bottlenecks

### The 80/20 Rule

Typically, 20% of states consume 80% of cycle time. Find them:

```bash
# Export and analyze
temet-jira analyze state-durations export.json \
  --business-hours \
  --sort-by duration \
  --output bottlenecks.csv
```

**Example Results:**
```
State           | Avg Duration | Median Duration | # Tickets
In Progress     | 32 hours     | 16 hours        | 120
Code Review     | 24 hours     | 8 hours         | 80
Blocked         | 40 hours     | 24 hours        | 35
Testing         | 16 hours     | 8 hours         | 110
Done            | 2 hours      | 1 hour          | 200
```

**Analysis:**
- "Blocked" state averages 40 hours → Investigate blockers
- "In Progress" has high variance (16–32 hour range) → Inconsistent completion
- "Code Review" takes 24 hours average → Resource constraint?

### Red Flags

```
1. Single state > 40% of total cycle time
   → Dedicated attention needed

2. High variance in state durations
   → Inconsistent process or hidden dependencies

3. "Blocked" or "Waiting" states growing
   → External dependencies not being managed

4. States with >7 day average
   → Handoff delays or resource bottleneck

5. Ticket stuck in one state >2x longer than peers
   → Check for hidden blockers or misclassification
```

---

## Cycle Time Analysis

### What is Cycle Time?

Total time from "To Do" to "Done":

```
Cycle Time = Done Date - Created Date

Example: PROJ-123
Created: 2024-01-15
Completed: 2024-01-22
Cycle Time: 7 calendar days (56 business hours)
```

### Calculating Key Metrics

**Average Cycle Time:**
```
Sum of all cycle times / Number of completed tickets

Example: (7 + 5 + 10 + 8 + 6) / 5 = 7.2 days average
```

**Median Cycle Time (better for outliers):**
```
Middle value when sorted

Example: 5, 6, 7, 8, 10 → Median = 7 days
(Immune to extreme outliers)
```

**Percentile Distribution:**
```
P50 (median):       7 days   (50% done by this time)
P75 (75th):        10 days   (75% done by this time)
P95 (95th):        20 days   (95% done by this time)

High P95/P50 ratio → Many outliers slow down delivery
```

### Cycle Time Trends

Track improvements over time:

```bash
# Analyze by quarter
temet-jira analyze state-durations export.json \
  --group-by-month \
  --output trends.csv
```

**Example Trend:**
```
Month      | Avg Cycle Time | # Completed
2024-01    | 9.2 days       | 45
2024-02    | 8.5 days       | 52
2024-03    | 7.1 days       | 61
2024-04    | 6.8 days       | 58

Trend: Improving (9.2 → 6.8 days)
Correlation: Team scaling (+13 devs)
```

---

## Workflow Patterns

### State Distribution

Understand where work typically flows:

```bash
# Count tickets per state (all time)
temet-jira export "project = PROJ" \
  --fields status \
  --format json | \
  jq -r '.[].fields.status' | \
  sort | uniq -c
```

**Healthy Pattern:**
```
 200  To Do           (20% - backlog)
 150  In Progress     (15% - active)
  50  Code Review     (5% - being reviewed)
  20  Blocked         (2% - waiting on externals)
 580  Done            (58% - completed)
```

**Red Flag Pattern:**
```
  30  To Do           (3% - empty backlog)
 400  In Progress     (40% - overloaded)
 100  Code Review     (10% - review bottleneck)
  50  Blocked         (5% - too many blockers)
 420  Done            (42% - falling behind)
```

### Typical Duration Profiles

**Fast-track (sprint items):**
```
To Do → In Progress → Code Review → Done
Total: 2-3 days
```

**Medium-track (standard features):**
```
To Do → In Progress → Code Review → Testing → Done
Total: 5-7 days
```

**Slow-track (complex/blocked):**
```
To Do → In Progress → Blocked → In Progress → Code Review → Testing → Blocked → Done
Total: 14+ days
```

---

## Improvement Strategies

### Quick Wins (1-2 weeks)

1. **Reduce Code Review Time**
   - Target: 24 hours → 8 hours
   - Action: Rotate reviewers, set SLA
   - Impact: 10-15% cycle time improvement

2. **Unblock Faster**
   - Identify top blockers (external dependencies)
   - Assign owner to resolve
   - Impact: 5-10% improvement

3. **Limit WIP (Work In Progress)**
   - Set max tickets in "In Progress"
   - Forces completion before new work
   - Impact: 15-20% improvement

### Medium Term (1 month)

1. **Parallelize Testing**
   - Move testing earlier (during development)
   - Automated test gates
   - Impact: 20-30% improvement

2. **Reduce Handoffs**
   - Cross-functional teams own feature end-to-end
   - Reduce "waiting on someone else"
   - Impact: 25% improvement

3. **Optimize State Flow**
   - Remove unnecessary states (To Do → In Progress → Done)
   - Combine similar states
   - Impact: 10% improvement

### Long Term (quarterly)

1. **Team Sizing**
   - Measure bottleneck states
   - Allocate resources to longest states
   - Impact: 30-50% improvement

2. **Process Reengineering**
   - Review entire workflow
   - Identify repeated patterns in blocked tickets
   - Impact: 40-60% improvement

3. **Cultural Changes**
   - Prioritize completion over starting new work
   - Set team cycle time goals
   - Impact: 20-30% sustained improvement

---

## Advanced Analysis

### Correlation Analysis

Find factors affecting cycle time:

```
High priority tickets: 5.2 day average
Low priority tickets: 8.1 day average
→ Priority affects cycle time by ~3 days

Small tickets (<5 story points): 3.2 days
Large tickets (>20 points): 11.4 days
→ Ticket size is strong predictor of duration
```

### Outlier Detection

Find tickets significantly slower/faster than peers:

```
Average: 7 days
Standard deviation: 2 days

Outliers:
- PROJ-456: 21 days (3 std deviations) → Investigate blocker
- PROJ-789: 1 day (far below average) → What went well?
```

### Predictability Metrics

Measure consistency:

```
Low variance (good):
  Distribution: 6, 6, 7, 7, 8 days
  Std Dev: 0.8 days
  Predictable

High variance (risky):
  Distribution: 1, 3, 9, 15, 20 days
  Std Dev: 8.5 days
  Unpredictable
```

---

## Tools & Commands

### Export for Analysis

```bash
# Full export with changelog
temet-jira export "project = PROJ" \
  --expand changelog \
  --format json \
  --output raw.json

# Analyze state durations
temet-jira analyze state-durations raw.json \
  --business-hours \
  --output analysis.csv

# Group by team/component
temet-jira analyze state-durations raw.json \
  --group-by component \
  --output by-component.csv
```

### Output Interpretation

CSV Columns:
- `state` — Workflow state name
- `avg_duration` — Average time in state (business hours)
- `median_duration` — Median time (more robust)
- `min_duration` — Fastest observed
- `max_duration` — Slowest observed
- `count` — Number of tickets observed
- `percent_of_total` — % of total cycle time
