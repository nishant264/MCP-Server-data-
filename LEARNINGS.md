# 📚 Gemini + MCP Playground — Complete Study Guide

> Everything you learned, explained simply, in one place.
> Think of this as your personal cheat sheet to review later.

---

## 🧠 1. What is an AI Agent?

**Simple definition:** An AI agent is like a **smart assistant** that can use tools to get things done.

**Analogy:** A chef (the AI) who can use kitchen tools (knives, pans, ovens) to cook a meal. You don't tell the chef *how* to use each tool — you just say "Make me pasta" and the chef figures out which tools to use.

**In our project:**
- **You** say: *"Show me products over $50"*
- **Gemini** (the AI brain) understands your request
- **Gemini decides** to call a tool called `run_sql_query()`
- The tool runs the SQL and returns results
- **Gemini formats** the answer and shows it to you

**Key takeaway:** The AI *decides* which tools to call and in what order. That's what makes it an "agent" — it acts on your behalf.

---

## 🔌 2. What is MCP? (Model Context Protocol)

**Simple definition:** A **universal plug** that lets any AI connect to any tool.

**Analogy:** Think of USB-C. Before USB-C, every device had a different charger. Now one cable works for everything. MCP is like USB-C for AI — one standard way for AI to talk to databases, APIs, file systems, etc.

**In our project:**
- The AI (Gemini) talks to our MCP server via this standard protocol
- Our MCP server (`db_mcp_server.py`) provides tools like `run_sql_query()` and `export_query()`
- The AI can discover what tools are available and call them

**Why MCP matters:** It's an open standard by Anthropic. Big companies like Google, Microsoft, and OpenAI are adopting it. Knowing MCP is a future-proof skill.

**Without MCP:** Every AI-tool connection needs custom code
**With MCP:** One standard that works everywhere

---

## ⚙️ 3. What is Agno?

**Simple definition:** A Python library that makes it easy to build AI agents.

**Analogy:** If building an AI agent is like building a house, Agno is the **pre-built frame** — you don't need to build the walls from scratch, you just customize the rooms.

**What Agno does in our code:**

```python
from agno.agent import Agent

agent = Agent(
    model=Gemini(id="gemini-1.5-flash"),  # The AI brain
    tools=[mcp_tools],                        # What tools it can use
    instructions=[...],                       # How to behave
    markdown=True,                            # Format answers nicely
    
                     # Show what it's doing
)
```

**Key features we used:**
- `tools=[]` — List of tools the agent can call
- `instructions=[]` — Personality and rules for the AI
- `show_tool_calls=True` — Shows you what the AI is doing behind the scenes
- `agent.arun(message)` — Runs the agent with your question

---

## 🤖 4. What is Gemini?

**Simple definition:** Google's AI model — the "brain" that understands your questions and writes answers.

**Analogy:** If the project is a car, Gemini is the **engine**. It does the heavy thinking.

**In our code:**

```python
from agno.models.google import Gemini

model = Gemini(model="gemini-1.5-flash")
```

**Why Gemini instead of OpenAI?**
- **Free tier** — Google AI Studio gives free API credits
- **Competitive** — Very capable, especially for coding tasks
- **Google ecosystem** — Integrates well with other Google services

**Setting up:** Get your API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey), then set it as an environment variable:

```python
os.environ["GOOGLE_API_KEY"] = "your-key-here"
```

---

## 🖥️ 5. What is Streamlit?

**Simple definition:** A Python library that turns Python scripts into web apps — no HTML or CSS needed.

**Analogy:** Streamlit is like **PowerPoint for code**. You write Python, and it automatically creates a nice web page.

**What we use it for:**
- `st.text_input()` — Text boxes for API keys and SQL queries
- `st.text_area()` — Larger text area for questions
- `st.button()` — Run Query button
- `st.markdown()` — Display formatted text and results
- `st.download_button()` — Download CSV/JSON/MD files
- `st.sidebar` — Panel on the left for settings
- `st.spinner()` — Loading animation while AI thinks
- `st.expander()` — Collapsible sections
- `st.columns()` — Arrange buttons side by side

**Why it's great:** You can build a full web app with just Python. Perfect for AI demos and internal tools.

---

## 🗄️ 6. What is SQLite?

**Simple definition:** A database that's just a **single file** on your computer. No server needed.

**Analogy:**
- **Excel** = You manually type data, filter, sort (not automated)
- **MySQL/PostgreSQL** = A giant library with a librarian (server) — powerful but needs setup
- **SQLite** = A notebook in your pocket — always available, no librarian needed

**Why SQLite for this project:**
- ✅ Built into Python (no installation)
- ✅ No server setup
- ✅ No internet needed
- ✅ Perfect for learning

**Key SQL commands we used:**
```sql
SELECT * FROM products WHERE price > 50;         -- Read data
SELECT COUNT(*) FROM orders;                      -- Count rows
SELECT name, price FROM products ORDER BY price;  -- Sort results
PRAGMA table_info(products);                      -- Get table structure
```

---

## 🏗️ 7. Our Project Architecture

Here's how everything connects:

```
┌─────────────────────────────────────────────────────┐
│              github_agent.py (Streamlit)              │
│  ── The web page you see in your browser              │
│                                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │         AI Agent (Gemini + Agno)               │    │
│  │  ── Understands your question                  │    │
│  │  ── Decides which MCP tool to call             │    │
│  │  ── Writes a nice formatted answer             │    │
│  └──────────────┬───────────────────────────────┘    │
│                 │  MCP Protocol (stdio)                │
│                 ▼                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │       db_mcp_server.py (MCP Server)            │    │
│  │  ── Runs as a separate Python process          │    │
│  │  ── Has 3 tools:                                │    │
│  │     • get_schema()  — Shows table structure    │    │
│  │     • run_sql_query() — Runs SELECT queries    │    │
│  │     • export_query() — Saves results to file   │    │
│  │  ── Security: Blocks DELETE, DROP, etc.        │    │
│  └──────────────┬───────────────────────────────┘    │
│                 │                                      │
│                 ▼                                      │
│        ┌──────────────┐                               │
│        │  store.db    │  (SQLite file)                 │
│        │  5 tables    │                                │
│        │  30 orders   │                                │
│        └──────────────┘                               │
└─────────────────────────────────────────────────────┘
```

---

## 🔒 8. Security Guardrails Explained

**The problem:** If the AI can write SQL, what stops it from writing `DROP TABLE products`?

**Our solution:** A function `validate_read_only_query()` that checks every query before running it.

```python
# Simplified version:
def validate_read_only_query(sql):
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]
    
    for keyword in forbidden:
        if sql.upper().startswith(keyword):
            return False  # BLOCKED!
    
    return True  # SAFE (SELECT query)
```

**Extra protections:**
1. **Multi-statement detection** — Catches `SELECT * ; DROP TABLE` tricks
2. **100-row limit** — No query returns more than 100 rows
3. **Export validation** — Export tool also checks queries before saving

---

## 📥 9. Export Feature

**Two ways to export data:**

**Manual Export** (in the UI):
1. After results appear, scroll to the "Download Results" section
2. Type a SQL query in the text box (or use the default)
3. Click CSV, JSON, or Markdown button
4. File downloads automatically

**AI-Assisted Export** (via MCP):
1. Ask the AI: *"Export this as CSV"*
2. The AI calls `export_query()` tool
3. File is saved to the `exports/` folder

**Helper function we built:**
```python
def fetch_sql_data(sql):
    conn = sqlite3.connect("store.db")
    cursor = conn.execute(sql)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return cols, rows
```

---

## 📦 10. Dependencies (requirements.txt)

```txt
streamlit>=1.28.0     # Web UI
agno>=2.2.10          # AI agent framework
mcp>=1.4.0            # Model Context Protocol
google-generativeai>=0.8.0  # Gemini AI model
```

To install: `pip install -r requirements.txt`

---

## 🎯 11. Key Concepts Glossary

| Term | Simple Definition |
|------|------------------|
| **AI Agent** | An AI that can use tools to accomplish tasks |
| **MCP** | A standard way for AI to talk to tools (like USB-C) |
| **Agno** | Python library for building AI agents |
| **Gemini** | Google's AI model (the "brain") |
| **Streamlit** | Python library for making web apps |
| **SQLite** | A database that's just a file on your computer |
| **MCP Server** | A program that provides tools to AI via MCP |
| **Tool** | A function the AI can call (like run_sql_query) |
| **StdioServerParameters** | Settings for connecting to an MCP server |
| **Environment Variable** | A secret value stored in the system (like API keys) |
| **Security Guardrail** | Code that blocks dangerous actions |
| **FastMCP** | Easy way to create MCP servers (from the mcp library) |

---

## 🚀 12. How to Run the Project

```bash
# 1. Install everything
pip install -r requirements.txt

# 2. Generate the sample database
python seed_db.py

# 3. Start the app
streamlit run github_agent.py
```

Then in the browser:
1. Get a free Gemini API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Paste it in the sidebar
3. Type a question like *"Show me all products over $50"*
4. Click "Run Query"

---

## 📁 13. Project Files Reference

| File | What it does | Key concepts inside |
|------|-------------|-------------------|
| `github_agent.py` | The main app with the UI and AI agent | Streamlit, Agno Agent, MCPTools, Gemini |
| `db_mcp_server.py` | The MCP server with database tools | FastMCP, @mcp.tool(), SQL, security |
| `seed_db.py` | Generates the sample database | SQLite, CREATE TABLE, INSERT |
| `store.db` | The actual database file | SQLite format — just a file! |
| `requirements.txt` | Python packages to install | pip, dependencies |
| `README.md` | Project documentation | Markdown, documentation |
| `LEARNINGS.md` | This file — your study guide! | Everything you learned |

---

## 💡 14. Quick Code Patterns to Remember

**Starting an MCP server:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def my_tool(param: str) -> str:
    """Describe what this tool does."""
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run()
```

**Connecting to an MCP server from an app:**
```python
from mcp import StdioServerParameters
from agno.tools.mcp import MCPTools

server_params = StdioServerParameters(
    command="python",
    args=["my_server.py"]
)

async with MCPTools(server_params=server_params) as tools:
    agent = Agent(tools=[tools], ...)
    response = await agent.arun("Your question")
```

**Creating an AI Agent:**
```python
from agno.agent import Agent
from agno.models.google import Gemini

agent = Agent(
    model=Gemini(id="gemini-1.5-flash"),
    tools=[...],
    instructions=["How the AI should behave"],
    markdown=True,
)
```

---

> **You've built a real AI + MCP project from scratch!** 🎉
> Most developers haven't even heard of MCP yet — this puts you ahead of the curve.
