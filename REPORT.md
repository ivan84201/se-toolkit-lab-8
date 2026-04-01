# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

Based on my exploration of the workspace, here are the available labs:                                                                     

Required Labs (5 tasks)                                                                                                                    

Location: /root/se-toolkit-lab-8/lab/tasks/required/                                                                                       

 • task-1.md                                                                                                                               
 • task-2.md                                                                                                                               
 • task-3.md                                                                                                                               
 • task-4.md                                                                                                                               
 • task-5.md                                                                                                                               

Optional Labs (1 task)                                                                                                                     

Location: /root/se-toolkit-lab-8/lab/tasks/optional/                                                                                       

 • task-1.md                                      

Based on my exploration of the workspace, here are the available labs:                                                                     

Required Labs (5 tasks)                                                                                                                    

Location: /root/se-toolkit-lab-8/lab/tasks/required/                                                                                       

 • task-1.md                                                                                                                               
 • task-2.md                                                                                                                               
 • task-3.md                                                                                                                               
 • task-4.md                                                                                                                               
 • task-5.md                                                                                                                               

Optional Labs (1 task)                                                                                                                     

Location: /root/se-toolkit-lab-8/lab/tasks/optional/                                                                                       

 • task-1.md                                                                                                                               

-------------------------------------------------------------------------------------------------------------------------------------------

## Task 1B — Agent with LMS tools

🐈 nanobot
Here are the available labs:                                                                                                               

 1 Lab 01 – Products, Architecture & Roles                                                                                                 
 2 Lab 02 — Run, Fix, and Deploy a Backend Service                                                                                         
 3 Lab 03 — Backend API: Explore, Debug, Implement, Deploy                                                                                 
 4 Lab 04 — Testing, Front-end, and AI Agents                                                                                              
 5 Lab 05 — Data Pipeline and Analytics Dashboard                                                                                          
 6 Lab 06 — Build Your Own Agent                                                                                                           
 7 Lab 07 — Build a Client with an AI Coding Agent                                                                                         
 8 lab-08                                                                                                                                  

Is there a specific lab you'd like to explore or get more information about?  

🐈 nanobot
The backend is running and responding (I can see successful requests in the logs). The empty result likely means the database hasn't been  
populated yet.   

## Task 1C — Skill prompt

Here are the available labs. Which one would you like to see the scores for?                                                               

 1 Lab 01 – Products, Architecture & Roles                                                                                                 
 2 Lab 02 — Run, Fix, and Deploy a Backend Service                                                                                         
 3 Lab 03 — Backend API: Explore, Debug, Implement, Deploy                                                                                 
 4 Lab 04 — Testing, Front-end, and AI Agents                                                                                              
 5 Lab 05 — Data Pipeline and Analytics Dashboard                                                                                          
 6 Lab 06 — Build Your Own Agent                                                                                                           
 7 Lab 07 — Build a Client with an AI Coding Agent                                                                                         
 8 Lab 08 — lab-08                                                                                                                         

Just let me know which lab (e.g., "lab-04" or "Lab 04") and I'll show you the pass rates and scores! 

## Task 2A — Deployed agent

nanobot-1  | Using config: /tmp/config.resolved.json
nanobot-1  | Using config: /tmp/config.resolved.json
nanobot-1  | 🐈 Starting nanobot gateway version 0.1.4.post6 on port 18790...
nanobot-1  | 2026-04-01 00:30:56.572 | DEBUG    | nanobot.channels.registry:discover_all:64 - Skipping built-in channel 'matrix': Matrix dependencies not installed. Run: pip install nanobot-ai[matrix]
nanobot-1  | Warning: No channels enabled
nanobot-1  | ✓ Heartbeat: every 1800s
nanobot-1  | 2026-04-01 00:30:57.008 | INFO     | nanobot.cron.service:_load_store:85 - Cron: jobs.json modified externally, reloading
nanobot-1  | 2026-04-01 00:30:57.009 | INFO     | nanobot.cron.service:start:202 - Cron service started with 0 jobs
nanobot-1  | 2026-04-01 00:30:57.009 | INFO     | nanobot.heartbeat.service:start:124 - Heartbeat started (every 1800s)
nanobot-1  | 2026-04-01 00:30:57.356 | WARNING  | nanobot.channels.manager:start_all:82 - No channels enabled
nanobot-1  | 2026-04-01 00:30:59.441 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_health' from server 'lms'
nanobot-1  | 2026-04-01 00:30:59.441 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_labs' from server 'lms'
nanobot-1  | 2026-04-01 00:30:59.441 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_learners' from server 'lms'
nanobot-1  | 2026-04-01 00:30:59.442 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_pass_rates' from server 'lms'
nanobot-1  | 2026-04-01 00:30:59.442 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_timeline' from server 'lms'
nanobot-1  | 2026-04-01 00:30:59.442 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_groups' from server 'lms'
nanobot-1  | 2026-04-01 00:30:59.442 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_top_learners' from server 'lms'
nanobot-1  | 2026-04-01 00:30:59.442 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_completion_rate' from server 'lms'
nanobot-1  | 2026-04-01 00:30:59.442 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_sync_pipeline' from server 'lms'
nanobot-1  | 2026-04-01 00:30:59.442 | INFO     | nanobot.agent.tools.mcp:connect_mcp_servers:246 - MCP server 'lms': connected, 9 tools registered
nanobot-1  | 2026-04-01 00:30:59.442 | INFO     | nanobot.agent.loop:run:280 - Agent loop started

## Task 2B — Web client

![web client chat screenshot](image.png)

Chat:
Connected to Nanobot!

Start by asking:
• What can you do in this system?
• What tools do you have right now?
• Ask one question about the LMS or the system state.

I am more than a chat UI only when the agent has tools, skills, and memory. Try discovering those capabilities from the conversation itself.

===

show me the scores

===

I'll help you view the scores! First, let me check which labs are available in the LMS.
**Which lab would you like to see scores for?**

1. Lab 01 – Products, Architecture & Roles
2. Lab 02 — Run, Fix, and Deploy a Backend Service
3. Lab 03 — Backend API: Explore, Debug, Implement, Deploy
4. Lab 04 — Testing, Front-end, and AI Agents
5. Lab 05 — Data Pipeline and Analytics Dashboard
6. Lab 06 — Build Your Own Agent
7. Lab 07 — Build a Client with an AI Coding Agent
8. lab-08

Just let me know which lab number (or name) you'd like to see the scores for!

## Task 3A — Structured logging

<!-- Paste happy-path and error-path log excerpts, VictoriaLogs query screenshot -->

## Task 3B — Traces

<!-- Screenshots: healthy trace span hierarchy, error trace -->

## Task 3C — Observability MCP tools

<!-- Paste agent responses to "any errors in the last hour?" under normal and failure conditions -->

## Task 4A — Multi-step investigation

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

## Task 4C — Bug fix and recovery

<!-- 1. Root cause identified
     2. Code fix (diff or description)
     3. Post-fix response to "What went wrong?" showing the real underlying failure
     4. Healthy follow-up report or transcript after recovery -->
