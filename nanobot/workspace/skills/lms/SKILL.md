---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

You have access to the LMS (Learning Management System) MCP server tools for querying live course data. Use these tools to answer questions about labs, learners, scores, and performance metrics.

## Available LMS Tools

### `lms_health`
Check if the LMS backend is healthy and report the item count.
- **Parameters**: None
- **Returns**: Status (healthy/unhealthy), item_count, error message if any
- **Use when**: User asks about system status or before querying other LMS data to ensure backend is available

### `lms_labs`
List all labs available in the LMS.
- **Parameters**: None
- **Returns**: Array of lab objects with id, type, parent_id, title, description
- **Use when**: User asks about available labs, or when a lab-specific query is made without specifying which lab

### `lms_learners`
List all learners registered in the LMS.
- **Parameters**: None
- **Returns**: Array of learner objects with id, external_id, student_group
- **Use when**: User asks about enrolled students or learner information

### `lms_pass_rates`
Get pass rates (average score and attempt count per task) for a specific lab.
- **Parameters**: 
  - `lab` (required): Lab identifier, e.g., 'lab-04'
- **Returns**: Array of task objects with task name, avg_score, attempts
- **Use when**: User asks about scores, pass rates, or task performance for a specific lab

### `lms_timeline`
Get submission timeline (date + submission count) for a specific lab.
- **Parameters**: 
  - `lab` (required): Lab identifier, e.g., 'lab-04'
- **Returns**: Array of objects with date and submissions count
- **Use when**: User asks about submission patterns, activity over time, or when students submitted work

### `lms_groups`
Get group performance (average score + student count per group) for a specific lab.
- **Parameters**: 
  - `lab` (required): Lab identifier, e.g., 'lab-04'
- **Returns**: Array of group objects with group name, avg_score, students count
- **Use when**: User asks about group performance, class section comparisons, or team-based metrics

### `lms_top_learners`
Get top learners by average score for a specific lab.
- **Parameters**: 
  - `lab` (required): Lab identifier, e.g., 'lab-04'
  - `limit` (optional, default 5): Max learners to return
- **Returns**: Array of learner objects with learner_id, avg_score, attempts
- **Use when**: User asks about top performers, best scores, or leaderboards

### `lms_completion_rate`
Get completion rate (passed / total) for a specific lab.
- **Parameters**: 
  - `lab` (required): Lab identifier, e.g., 'lab-04'
- **Returns**: Object with lab, completion_rate (percentage), passed count, total count
- **Use when**: User asks about completion rates, how many students finished, or overall lab success rate

### `lms_sync_pipeline`
Trigger the LMS sync pipeline. May take a moment to complete.
- **Parameters**: None
- **Returns**: Confirmation of sync initiation
- **Use when**: User requests a data sync, or when backend data appears stale/outdated

## Strategy Rules

1. **Lab selection**: If the user asks for scores, pass rates, completion, groups, timeline, or top learners without naming a lab:
   - First call `lms_labs` to get available labs
   - Present the lab options to the user and ask them to choose
   - Use each lab's `title` field as the user-facing label (e.g., "Lab 04 — Testing, Front-end, and AI Agents")
   - Use the lab `id` field (e.g., 'lab-04') as the parameter value for tool calls

2. **Health check**: If any LMS tool returns an error or unexpected result, call `lms_health` first to verify the backend is operational.

3. **Formatting**: 
   - Display percentages with one decimal place (e.g., 97.2%)
   - Show scores as numbers with one decimal place (e.g., 63.4)
   - Format counts as plain integers (e.g., 239 students)

4. **Concise responses**: Keep answers focused on the user's question. Provide summary statistics first, then offer to show more details if needed.

5. **Missing lab handling**: When a lab parameter is needed but not provided:
   - Call `lms_labs` first to get available labs
   - Use the `mcp_webchat_ui_message` tool to present a structured choice UI to the user
   - Each option should use the lab's `title` as the label and `id` as the value
   - Wait for the user to select a lab before proceeding with the actual query

6. **Structured UI integration**: When presenting lab choices or other multi-option selections:
   - Call `mcp_webchat_ui_message` with `type: "choice"`
   - Provide clear, concise labels for each option
   - Include the `chat_id` from your runtime context to route to the active chat
   - Let the `structured-ui` skill handle the generic UI behavior

7. **Capabilities explanation**: When the user asks "what can you do?", explain:
   - You can query live LMS data about labs, learners, and performance metrics
   - You can show pass rates, completion rates, group performance, top learners, and submission timelines
   - You need a specific lab identifier for most performance queries
   - You can trigger data sync if needed

## Example Interactions

**User**: "What labs are available?"
→ Call `lms_labs` and list the lab titles.

**User**: "Show me the scores"
→ Call `lms_labs` first, then ask user to choose a lab.

**User**: "What's the completion rate for lab-04?"
→ Call `lms_completion_rate` with lab='lab-04'.

**User**: "Which lab has the lowest pass rate?"
→ Call `lms_labs` to get all labs, then call `lms_pass_rates` for each lab, compare and report.

**User**: "Who are the top 3 students in lab-04?"
→ Call `lms_top_learners` with lab='lab-04' and limit=3.
