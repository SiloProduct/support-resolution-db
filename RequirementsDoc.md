## Requirements Document: Silo Support Ticket Issue Clustering Script

### Objective

Process ~150 resolved Freshdesk tickets to create a deduplicated issue database using LLM-based clustering.

### Core Requirements

**Data Source**

- Freshdesk Filter API endpoint: `https://heysilo-help.freshdesk.com//api/v2/search/tickets?query="status:3%20OR%20status:4"&page=1`
- Requires pageination query - Pages 1 - 5
- Filter: `status=4` (resolved) `status=5` (closed)
- Initial call returns ticket IDs only
- Conversations Freshdesk API endpoint: `https://heysilo-help.freshdesk.com/api/v2/tickets/{{ticketId}}?include=conversation`

**Processing Flow**

```javascript
1. Fetch all resolved ticket IDs (single GET request)
2. Extract ticket IDs to list
3. Process in batches of 3 tickets
4. For each ticket:
   - GET conversation using ticket ID
   - Extract description_text + body_text + private flag (true=internal conversation, false=visible to user) + incoming flag (true=user, false=agent)
   - Build clean conversation object (user message → agent response)
   - LLM determines if new issue or matches existing
   - Flag for human review if uncertainty (Flag when human review is needed will be returned by LLM)
5. Build final issue database via LLM
```

**Conversation Object Format**

```javascript
{
  "ticket_id": 12345,
  "conversation": [
    {"speaker": "user", "text": "My wifi setup keeps failing"},
    {"speaker": "agent", "Private/Not Private", "text": "Please check if your router supports 2.4GHz..."}
  ]
}
```

**Output Format**
JSON file: `silo_issues_db.json`

```json
[
  {
    "issue_id": "WIFI-001",
    "category": "setup",
    "keywords": ["wifi setup", "can't connect"],
    "root_cause": "2.4GHz router compatibility",
    "resolution_steps": ["step1", "step2"],
    "tickets": [12345, 12367, 12401],
    "notes": "Importent notes for resolution and escalation instructions"
  }
]
```

**File Structure**

```javascript
project/
├── main.py              # Core processing script
├── prompts_config.py    # All LLM prompts (separate file)
├── requirements.txt     # Dependencies
├── conversations/       # Cleaned per-ticket conversation JSON files
└── output/
    └── silo_issues_db.json
```