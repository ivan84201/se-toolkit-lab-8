# Observability Skill

Use the observability MCP tools to query VictoriaLogs and VictoriaTraces when investigating errors, debugging issues, or monitoring system health.

## Available Tools

### Log Tools (VictoriaLogs)

- **`logs_search`** — Search logs using LogsQL queries
  - Parameters: `query` (LogsQL string), `limit` (max entries, default 100)
  - Use for: Finding specific log entries, filtering by service/severity/time

- **`logs_error_count`** — Count errors per service over a time window
  - Parameters: `service` (optional filter), `time_range` (default "1h")
  - Use for: Quick overview of error distribution across services

### Trace Tools (VictoriaTraces)

- **`traces_list`** — List recent traces
  - Parameters: `service` (optional filter), `limit` (default 20)
  - Use for: Finding traces for a specific service or recent activity

- **`traces_get`** — Fetch a specific trace by ID
  - Parameters: `trace_id` (required)
  - Use for: Inspecting the full span hierarchy of a specific request

## Strategy

### When the user asks about errors or failures:

1. **Start with `logs_error_count`** to get a quick overview of recent errors
   - Use a narrow time window (e.g., "10m" or "1h") for recent issues
   - If the user mentions a specific service, filter by that service

2. **Use `logs_search`** to inspect the actual error messages
   - Query pattern: `_time:10m service.name:"<service>" severity:ERROR`
   - Look for `trace_id` fields in error log entries

3. **If you find a `trace_id`**, use `traces_get` to fetch the full trace
   - This shows the complete request flow across services
   - Identify which span failed and why

4. **Summarize findings concisely**
   - Don't dump raw JSON
   - Report: which service failed, what error occurred, when it happened
   - If you have trace data, explain the failure point in the request flow

### When the user asks about system health:

1. Check `logs_error_count` for the last hour
2. If no errors, report healthy status
3. If errors exist, follow the error investigation flow above

### Query Tips

**VictoriaLogs (LogsQL) examples:**

```text
# All errors in the last 10 minutes
_time:10m severity:ERROR

# Errors from a specific service
_time:1h service.name:"Learning Management Service" severity:ERROR

# Search for a specific event type
_time:1h event:"db_query" severity:ERROR
```

**VictoriaTraces:**

- Use the Jaeger-compatible API endpoints
- Traces are linked to logs via `trace_id` field
- Each trace shows spans with timing and status information

## Response Style

- Be concise and actionable
- Focus on what the user needs to know, not every detail
- If you find errors, explain:
  - What failed
  - Which service
  - When it happened
  - Any relevant trace information
- Offer to dig deeper if the user wants more details

## Example Interactions

**User**: "Any errors in the last hour?"
→ Call `logs_error_count` with time_range="1h", summarize results.

**User**: "What's wrong with the backend?"
→ Call `logs_error_count` filtered to backend service, then `logs_search` for details, then `traces_get` if trace IDs are found.

**User**: "Show me the trace for request abc123"
→ Call `traces_get` with trace_id="abc123", summarize the span hierarchy and any errors.

**User**: "Any LMS backend errors in the last 10 minutes?"
→ Call `logs_error_count` with service="Learning Management Service" and time_range="10m", then investigate if errors exist.
