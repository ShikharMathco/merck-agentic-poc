<!-- # Enhanced Multi-Agent System Architecture (Text2SQL + Scenario Planner)

```
text2sql-system/
│
├── agentcore/                          # AWS AgentCore configs
│   ├── orchestrator/
│   │   ├── agent.json
│   │   └── config.yaml
│   │
│   ├── text2sql/
│   │   ├── agent.json
│   │   └── config.yaml
│   │
│   └── scenario_planner/               # Scenario Planner AgentCore config
│       ├── agent.json
│       └── config.yaml
│
├── orchestrator/                       # LangGraph or simple python orchestrator
│   ├── __init__.py
│   ├── orchestrator.py                 # Core logic calling both agents
│   ├── state.py                        # LangGraph-style state (optional)
│   ├── router.py                       # Routing logic between agents
│   └── workflow_schemas.py             # Define agent interaction patterns
│
├── agents/
│   ├── text2sql/
│   │   ├── __init__.py
│   │   ├── agent.py                    # MAIN entrypoint for this agent
│   │   │
│   │   ├── pipeline/                   # Your modular Text2SQL pipeline
│   │   │   ├── keyword_extractor.py
│   │   │   ├── entity_resolver.py
│   │   │   ├── table_selector.py
│   │   │   ├── column_selector.py
│   │   │   ├── query_generator.py
│   │   │   ├── sql_rewriter.py
│   │   │   └── query_executor.py
│   │   │
│   │   ├── prompts/
│   │   │   ├── keyword_extraction.txt
│   │   │   ├── entity_resolution.txt
│   │   │   ├── table_selection.txt
│   │   │   ├── column_selection.txt
│   │   │   ├── sql_generation.txt
│   │   │   ├── sql_rewrite.txt
│   │   │   └── system_instructions.txt
│   │   │
│   │   ├── schemas/
│   │   │   ├── database_schema.json
│   │   │   └── tables/
│   │   │       ├── orders.json
│   │   │       ├── customers.json
│   │   │       └── products.json
│   │   │
│   │   └── utils/
│   │       ├── text_cleaner.py
│   │       └── schema_loader.py
│   │
│   └── scenario_planner/                # Scenario Planner Agent
│       ├── __init__.py
│       ├── agent.py                     # MAIN entrypoint for scenario planner
│       │
│       ├── pipeline/                    # Modular scenario planning pipeline
│       │   ├── input_extractor.py       # Extract user input from request
│       │   ├── business_rule_interpreter.py  # Interpret business rules
│       │   ├── payload_generator.py     # Generate scenario payloads
│       │   ├── optimizer_executor.py    # Run optimization logic
│       │   ├── db_writer.py             # Write scenarios to database
│       │   └── output_formatter.py      # Format final output to user
│       │
│       ├── context/                     # Context management
│       │   ├── abbreviations.py         # Load and manage abbreviations
│       │   ├── business_rules.py        # Business rules engine
│       │   ├── company_context.py       # Company-specific context
│       │   └── context_interpreter.py   # Interpret various contexts
│       │
│       ├── prompts/
│       │   ├── input_extraction.txt
│       │   ├── business_rule_parsing.txt
│       │   ├── payload_generation.txt
│       │   ├── optimization_instructions.txt
│       │   └── system_instructions.txt
│       │
│       ├── schemas/
│       │   ├── database_schema.json     # Scenario DB schema
│       │   ├── context_schema.json      # Context information schema
│       │   ├── scenario_input.json      # Input validation schema
│       │   ├── scenario_output.json     # Output format schema
│       │   └── business_rules/          # Business rule definitions
│       │       ├── budget_rules.json
│       │       ├── category_rules.json
│       │       └── optimization_rules.json
│       │
│       └── utils/
│           ├── scenario_validator.py    # Validate scenario inputs
│           ├── optimizer_engine.py      # Optimization algorithms
│           └── metadata_manager.py      # Handle scenario metadata
│
├── services/
│   ├── llm/
│   │   ├── bedrock_client.py
│   │   └── openai_client.py
│   │
│   ├── db/
│   │   ├── postgres_client.py
│   │   ├── mysql_client.py
│   │   └── scenario_db_client.py        # Scenario-specific DB operations
│   │
│   ├── log/
│   │   ├── logger.py
│   │   └── tracing.py
│   │
│   └── context/                         # Shared context service
│       ├── context_loader.py            # Load context from various sources
│       └── context_cache.py             # Cache context for performance
│
├── docker/
│   ├── orchestrator.Dockerfile
│   ├── text2sql.Dockerfile
│   └── scenario_planner.Dockerfile      # Scenario Planner container
│
├── tests/
│   ├── test_text2sql.py
│   ├── test_scenario_planner.py         # Scenario Planner tests
│   └── test_orchestrator.py
│
├── scripts/
│   ├── run_local_orchestrator.py
│   ├── run_local_text2sql.py
│   └── run_local_scenario_planner.py    # Local scenario planner runner
│
├── requirements.txt
├── pyproject.toml
├── README.md
└── .env
```

## Aggressive Timeline (7 Days) ⚡

### Day 1: Foundation Sprint
**Morning (4h):**
- Create folder structure for all 3 agents
- Set up basic agent.py handlers with placeholder logic
- Configure shared services (LLM client, DB client, logger)

**Afternoon (4h):**
- Build simple orchestrator with hardcoded routing
- Test agent invocation locally (mock responses)
- Set up requirements.txt and basic configs

**Goal:** Working skeleton that can route requests end-to-end

---

### Day 2: Text2SQL Core (MVP)
**Morning (4h):**
- Implement core Text2SQL pipeline (simplified):
  - Keyword extraction → Table selection → SQL generation
  - Skip entity resolution and column selection for now
- Load database schema from JSON

**Afternoon (4h):**
- Integrate Bedrock LLM calls
- Test SQL generation with 3-5 sample queries
- Basic query executor with error handling

**Goal:** Text2SQL generates and executes valid SQL for simple queries

---

### Day 3: Scenario Planner Core (MVP)
**Morning (4h):**
- Implement scenario planner pipeline (simplified):
  - Input extractor (parse user parameters)
  - Basic payload generator (create scenario JSON)
  - DB writer (insert to scenarios table)

**Afternoon (4h):**
- Add simple optimization logic (basic budget allocation)
- Load context (abbreviations, business rules from JSON)
- Test end-to-end: input → scenario creation → DB storage

**Goal:** Scenario Planner creates and stores basic scenarios

---

### Day 4: Integration & Refinement
**Morning (4h):**
- Connect Text2SQL ↔ Scenario Planner workflows
- Test chained execution (query data → create scenario)
- Fix integration bugs

**Afternoon (4h):**
- Add business rule validation (budget constraints, impact ratio)
- Implement optimizer logic (incremental rates calculation)
- Polish output formatting for both agents

**Goal:** Both agents work together in realistic workflows

---

### Day 5: Dockerization & AWS Prep
**Morning (4h):**
- Create 3 Dockerfiles (orchestrator, text2sql, scenario_planner)
- Write docker-compose.yml for local testing
- Test all agents in containers locally

**Afternoon (4h):**
- Create AgentCore configs (agent.json, config.yaml) for all 3
- Set up IAM roles and permissions
- Prepare deployment scripts

**Goal:** Containerized agents ready for AWS deployment

---

### Day 6: AWS Deployment
**Morning (4h):**
- Deploy orchestrator to AWS Lambda/ECS
- Deploy Text2SQL agent
- Deploy Scenario Planner agent

**Afternoon (4h):**
- Configure agent communication (Lambda invocations or API Gateway)
- Test basic flows in AWS environment
- Debug deployment issues

**Goal:** All agents running in AWS AgentCore runtime

---

### Day 7: Testing & Polish
**Morning (4h):**
- End-to-end testing of all workflows
- Performance testing and optimization
- Fix critical bugs

**Afternoon (4h):**
- Add logging and monitoring
- Write basic documentation (README, API docs)
- Final deployment validation

**Goal:** Production-ready system with monitoring

---

## What to Cut/Simplify for 7-Day Timeline

### ❌ Cut These (Add Later):
1. **Text2SQL Advanced Features:**
   - Entity resolution (Phase 2)
   - Advanced column selection (Phase 2)
   - SQL rewriting/optimization (Phase 2)
   
2. **Scenario Planner Advanced Features:**
   - Complex optimization algorithms (use simple allocation)
   - Advanced business rules engine (hardcode top 3-5 rules)
   - Metadata management (minimal for MVP)

3. **Infrastructure:**
   - Skip extensive unit tests (focus on integration tests)
   - Manual deployment initially (automate later)
   - Basic error handling only

### ✅ Keep These (Critical Path):
1. **Core Text2SQL:**
   - Schema-aware SQL generation
   - Basic query execution
   - LLM integration

2. **Core Scenario Planner:**
   - Input parsing and validation
   - Scenario payload generation
   - DB write operations
   - Basic optimization

3. **Core Orchestrator:**
   - Request routing
   - Agent invocation
   - Response formatting

4. **AWS Deployment:**
   - All 3 agents running
   - Basic inter-agent communication
   - Database connectivity

---

Each agent's `agent.json` follows this pattern:

```json
{
  "agentName": "scenario-planner",
  "agentType": "aws-bedrock",
  "runtime": "python3.12",
  "handler": "agents.scenario_planner.agent.handler",
  "timeout": 300,
  "memory": 2048,
  "environment": {
    "DB_HOST": "${DB_HOST}",
    "CONTEXT_BUCKET": "${CONTEXT_BUCKET}",
    "LLM_MODEL": "anthropic.claude-sonnet-4-5"
  },
  "permissions": [
    "bedrock:InvokeModel",
    "s3:GetObject",
    "rds:ExecuteStatement"
  ]
}
```

### 4. Agent Communication Protocol

All agents expose a standard interface:

```python
def handler(event, context):
    """
    event = {
        "agent": "scenario_planner",
        "action": "create_scenario",
        "payload": {...},
        "context": {...}
    }
    """
    return {
        "statusCode": 200,
        "agent": "scenario_planner",
        "result": {...},
        "metadata": {...}
    }
```

## Scenario Planner Specific Notes

### Context Loading Priority
1. Load database schema from Context Information
2. Load business rules from configuration
3. Load abbreviations and company context
4. Initialize context interpreter

### Pipeline Flow
1. **Extract Input** - Parse user request and parameters (category, channel, subchannel, budget, impact_ratio)
2. **Business Rule Interpretation** - Apply relevant business rules and constraints
3. **Payload Generation** - Create scenario configurations with metadata
4. **Optimizer Execution** - Run optimization algorithms to generate optimized scenarios
5. **DB Write** - Store scenarios with metadata (baseline vs optimized)
6. **Output Formatting** - Return results to user in structured format

### Database Operations
- **Read**: Retrieve context, schemas, existing scenarios
- **Write**: Store new scenarios, optimization results with incremental rates
- **Update**: Modify scenario parameters
- **Query**: Fetch scenarios for comparison/reporting

### Integration with Text2SQL

**Scenario Creation from Query Results:**
- Text2SQL retrieves historical data
- Data passed to Scenario Planner for scenario generation
- Scenario Planner creates baseline and optimized scenarios

**Scenario Analysis:**
- Scenario Planner stores scenarios in database
- Text2SQL queries scenario tables for analysis and reporting
- Results returned to user via orchestrator

**Example Workflow:**
1. User: "Create scenarios for Digital category with 200k budget"
2. Orchestrator routes to Scenario Planner
3. Scenario Planner creates scenarios and stores in DB
4. User: "Show me the top performing scenarios"
5. Orchestrator routes to Text2SQL
6. Text2SQL queries scenario tables and returns results

## Use Case Examples

### Use Case 1: Create New Scenario
```
User Input: "Create scenario for Digital, Meta channel, FB subchannel with 200k budget and 1.5 impact ratio"

Flow:
1. Orchestrator → Scenario Planner
2. Input Extraction → Parse parameters
3. Business Rules → Validate constraints
4. Payload Generation → Create baseline scenario
5. Optimizer → Generate optimized allocation
6. DB Write → Store both scenarios
7. Output → Return scenario IDs and summary
```

### Use Case 2: Analyze Scenarios
```
User Input: "Show me all scenarios created last month with budget > 150k"

Flow:
1. Orchestrator → Text2SQL
2. Query Generation → Build SQL query on scenario tables
3. Query Execution → Fetch scenario data
4. Output → Return formatted results
```

### Use Case 3: Create Scenario from Historical Data
```
User Input: "Create a new scenario based on Q3 performance data"

Flow:
1. Orchestrator → Text2SQL (fetch Q3 data)
2. Orchestrator → Scenario Planner (with Q3 data as input)
3. Scenario Planner → Create scenarios using historical patterns
4. DB Write → Store scenarios
5. Output → Return results
```

## Deployment Considerations

### AWS Resources Required
- **3 Lambda Functions** (or ECS tasks): orchestrator, text2sql, scenario_planner
- **RDS Instance**: For both operational data and scenario storage
- **S3 Bucket**: For context files, schemas, and configuration
- **Bedrock Access**: For LLM invocations
- **IAM Roles**: Proper permissions for each agent

### Environment Variables
```bash
# Orchestrator
ORCHESTRATOR_NAME=multi-agent-orchestrator
TEXT2SQL_AGENT_ARN=arn:aws:lambda:region:account:function:text2sql-agent
SCENARIO_PLANNER_AGENT_ARN=arn:aws:lambda:region:account:function:scenario-planner-agent

# Text2SQL
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_NAME=operational_db
LLM_MODEL=anthropic.claude-sonnet-4-5

# Scenario Planner
DB_HOST=your-rds-endpoint.rds.amazonaws.com
SCENARIO_DB_NAME=scenarios_db
CONTEXT_BUCKET=your-context-bucket
LLM_MODEL=anthropic.claude-sonnet-4-5
```

### Monitoring and Logging
- CloudWatch Logs for each agent
- X-Ray for distributed tracing
- Custom metrics for agent performance
- Error alerting and retry logic -->