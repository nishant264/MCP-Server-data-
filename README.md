# ✨ Gemini + MCP Playground

An AI agent that uses **Google Gemini** and the **Model Context Protocol (MCP)** to securely interact with data and tools.

Built with **Streamlit**, **Gemini**, **Agno**, and a custom **MCP server** — no Docker needed!

---

## 🏆 Why This Project?

This showcases **AI Engineering** skills:

| Skill | How It's Shown |
|-------|---------------|
| **AI Agent Architecture** | Google Gemini + Agno agent that decides which tools to call |
| **MCP Protocol** | Custom MCP server with read-only SQL tools + security guardrails |
| **Security Engineering** | Guards blocking dangerous queries (DELETE, DROP, etc.) |
| **Full-Stack AI** | Streamlit UI + AI backend + local database |
| **Practical Features** | One-click CSV/JSON/Markdown export |

---

## ✨ Features

- **Natural Language Queries** — Ask questions in plain English about a sample e-commerce database
- **Custom MCP Server** — A local server that translates AI requests into safe database queries
- **🔒 Security Guardrails** — Only SELECT queries allowed; all modifications blocked
- **Multiple Export Formats** — Download results as CSV, JSON, or Markdown with one click
- **AI-Assisted Export** — Just say *"export this as CSV"* and the AI handles it
- **Tool Transparency** — See exactly which tools the AI calls and what SQL it writes

---

## 🧠 How It Works

```
You: "Show me all products over $50"
                │
                ▼
┌───────────────────────────────────────┐
│   Streamlit Web App (github_agent.py)  │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │  Gemini (Google AI)             │  │
│  │  • Understands your question    │  │
│  │  • Decides which tool to call   │  │
│  │  • Formats the answer           │  │
│  └──────────┬──────────────────────┘  │
│             │ MCP Protocol             │
│             ▼                          │
│  ┌─────────────────────────────────┐  │
│  │  MCP Server (db_mcp_server.py)   │  │
│  │  • Validates query (read-only?) │  │
│  │  • Runs SELECT on SQLite DB     │  │
│  │  • Returns formatted results    │  │
│  └──────────┬──────────────────────┘  │
│             │                          │
│             ▼                          │
│     ┌──────────────┐                  │
│     │  store.db    │  (SQLite file)    │
│     └──────────────┘                  │
└───────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Requirements

- **Python 3.8+**
- **Gemini API Key** — Get one free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

> No Docker. No GitHub token. No OpenAI key.

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the sample database
python seed_db.py

# 3. Start the app
streamlit run github_agent.py
```

### Usage

1. **Enter your Gemini API key** in the sidebar (get one free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey))
2. **Type a question** about the store data — e.g., *"Show me all products under $50"*
3. **Click "Run Query"** and watch the AI work!
4. **Export results** using the download buttons below the response

---

## 💬 Example Queries

Try asking the AI:

```
🔍 "Show me all products sorted by price"
🔍 "Which customers have placed the most orders?"
🔍 "What's the total revenue from last month?"
🔍 "Show me orders that haven't shipped yet"
🔍 "Export all products as CSV"
🔍 "How many customers do we have from each city?"
```

---

## 📁 Project Structure

| File | Purpose |
|------|---------|
| `github_agent.py` | Main Streamlit app — UI + AI agent connection |
| `db_mcp_server.py` | Custom MCP server — read-only SQL tools + export |
| `seed_db.py` | Script to generate the sample database |
| `store.db` | SQLite database with sample e-commerce data |
| `requirements.txt` | Python dependencies |
| `exports/` | Folder where exported files are saved (created on first export) |

---

## 🗄️ Database Schema

The sample database (`store.db`) contains 5 tables with 30 orders, 25 products, and 10 customers:

| Table | Description |
|-------|-------------|
| `categories` | Product categories (Electronics, Clothing, Books, etc.) |
| `products` | Items for sale with prices and stock |
| `customers` | Customer information |
| `orders` | Orders placed with status (delivered, shipped, etc.) |
| `order_items` | Individual products within each order |

---

## 🔒 Security Guardrails

The MCP server has layers of protection:

1. **Keyword blocking** — Queries starting with `DELETE`, `DROP`, `INSERT`, `UPDATE`, etc. are rejected
2. **Multi-statement detection** — Multiple SQL statements separated by `;` are individually checked
3. **Result limiting** — Maximum 100 rows returned per query
4. **Read-only export** — Export tool also validates queries before writing files

---

## 🛠️ Tech Stack

| Technology | Role |
|-----------|------|
| **[Streamlit](https://streamlit.io/)** | Web UI framework |
| **[Google Gemini](https://ai.google.dev/)** | AI model (via `google-generativeai`) |
| **[Agno](https://github.com/agno-agi/agno)** | AI agent framework |
| **[MCP](https://modelcontextprotocol.io/)** | Model Context Protocol (tool communication standard) |
| **[SQLite](https://www.sqlite.org/)** | Local database (built into Python) |

---

## 📝 License

This project is for educational purposes. Built as a demonstration of AI Agent + MCP architecture.
