import asyncio
import csv
import io
import json
import os
import re
import sqlite3
import sys
import streamlit as st
from datetime import datetime
from pathlib import Path
from agno.agent import Agent
from agno.models.groq import Groq

PROJECT_DIR = Path(__file__).parent
DB_PATH = str(PROJECT_DIR / "store.db")

if not os.path.exists(DB_PATH):
    import subprocess
    subprocess.run([sys.executable, str(PROJECT_DIR / "seed_db.py")], check=True)


def fetch_sql_data(sql: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(sql)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return cols, rows


def _validate_read_only(sql: str) -> bool:
    cleaned = sql.strip().upper()
    forbidden = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
        "CREATE", "TRUNCATE", "REPLACE", "ATTACH",
        "DETACH", "REINDEX", "VACUUM"
    ]
    for keyword in forbidden:
        if re.match(rf"^\s*{keyword}\b", cleaned):
            return False
    statements = re.split(r";", sql)
    if len(statements) > 1:
        for stmt in statements:
            stmt_clean = stmt.strip().upper()
            if stmt_clean and not any(stmt_clean.startswith(k) for k in ["SELECT", "EXPLAIN", "PRAGMA"]):
                return False
    return True


def run_sql_query(sql: str) -> str:
    if not _validate_read_only(sql):
        return ("❌ BLOCKED: Only SELECT, EXPLAIN, and PRAGMA queries are allowed.\n"
                "INSERT, UPDATE, DELETE, DROP, ALTER, and other modifications are blocked for safety.")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchmany(100)
        if not rows:
            conn.close()
            return "Query returned no results."
        columns = [desc[0] for desc in cursor.description]
        result_lines = []
        result_lines.append(" | ".join(f"**{col}**" for col in columns))
        result_lines.append(" | ".join("---" for _ in columns))
        for row in rows:
            formatted = []
            for value in row:
                formatted.append("NULL" if value is None else str(value))
            result_lines.append(" | ".join(formatted))
        result_lines.append(f"\n*{len(rows)} row(s) returned*")
        remaining = cursor.fetchone()
        if remaining:
            result_lines.append("*⚠️ More results available (limited to 100 rows)*")
        conn.close()
        return "\n".join(result_lines)
    except sqlite3.Error as e:
        return f"❌ Database error: {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def get_schema() -> str:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        result_lines = ["# 📊 Database Schema\n"]
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            result_lines.append(f"## 📋 `{table_name}`")
            result_lines.append("| Column | Type | Required |")
            result_lines.append("|--------|------|----------|")
            for col in columns:
                result_lines.append(f"| `{col[1]}` | {col[2] if col[2] else 'TEXT'} | {'✅' if col[3] else '❌'} |")
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            result_lines.append(f"\n*📝 {count} rows*\n")
        conn.close()
        return "\n".join(result_lines)
    except sqlite3.Error as e:
        return f"❌ Database error: {str(e)}"


def export_query(sql: str, format: str = "csv") -> str:
    if not _validate_read_only(sql):
        return "❌ BLOCKED: Only read-only queries can be exported."
    format = format.lower()
    if format not in ["csv", "json", "md"]:
        return f"❌ Unsupported format: '{format}'. Use 'csv', 'json', or 'md'."
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return "Query returned no results — nothing to export."
        exports_dir = PROJECT_DIR / "exports"
        exports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"query_{timestamp}.{format}"
        filepath = exports_dir / filename
        if format == "csv":
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)
        elif format == "json":
            data = [dict(zip(columns, row)) for row in rows]
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)
        elif format == "md":
            with open(filepath, "w") as f:
                f.write("| " + " | ".join(columns) + " |\n")
                f.write("| " + " | ".join("---" for _ in columns) + " |\n")
                for row in rows:
                    escaped = [str(v) if v is not None else "" for v in row]
                    f.write("| " + " | ".join(escaped) + " |\n")
                f.write(f"\n*{len(rows)} rows exported*\n")
        return f"✅ Exported {len(rows)} rows to `{filename}`\n\n📁 File saved to: `{filepath}`"
    except sqlite3.Error as e:
        return f"❌ Database error: {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


st.set_page_config(page_title="✨ Groq + MCP Playground", page_icon="✨", layout="wide")

st.markdown("<h1 class='main-header'>✨ Groq + MCP Playground</h1>", unsafe_allow_html=True)
st.markdown("Chat with an AI agent that uses the Model Context Protocol to interact with data and tools")

with st.sidebar:
    st.markdown("### Try Asking")
    st.markdown("- Show me all products with price above $50")
    st.markdown("- Which customers have placed the most orders?")
    st.markdown("- What's the total revenue from last month?")
    st.markdown("- Show me orders that haven't shipped yet")
    st.markdown("- Export products as CSV")
    st.markdown("---")
    st.markdown("### ⚙️ How It Works")
    st.markdown("""
    1. **You** ask a question in plain English
    2. **Groq** (via Llama 3.3 70B) understands your request
    3. The agent runs SQL queries against the database
    4. Results come back formatted as readable text
    
    **Export:** Say "export this as CSV" or 
    use the manual export section below results.
    """)

query = st.text_area("Your Query", placeholder="e.g., Show me all products sorted by price")

async def run_agent(message):
    if not os.getenv("GROQ_API_KEY"):
        return "Error: Groq API key not configured. Please contact the site owner."
    try:
        agent = Agent(
            model=Groq(id="llama-3.3-70b-versatile"),
            tools=[run_sql_query, get_schema, export_query],
            instructions=[
                "You are a helpful data assistant for a small e-commerce store.",
                "Your database has 5 tables: categories, products, customers, orders, order_items.",
                "Always start by calling get_schema() to understand the database structure.",
                "Then use run_sql_query() to answer the user's question.",
                "When showing results, use clear markdown formatting.",
                "Explain what you found in plain, friendly language.",
                "If a user asks to export or download data, use export_query().",
                "If a query fails, try a simpler version of it.",
                "NEVER try to modify data — only read it.",
            ],
            markdown=True,
        )
        response = await asyncio.wait_for(
            agent.arun(message), timeout=120.0
        )
        return response.content
    except asyncio.TimeoutError:
        return "Error: Request timed out after 120 seconds"
    except Exception as e:
        return f"Error: {str(e)}"

if st.button("🚀 Run Query", type="primary", use_container_width=True):
    if not query:
        st.error("Please enter a query")
    else:
        with st.spinner("🧠 Groq is thinking... calling database tools..."):
            result = asyncio.run(run_agent(query))
        st.markdown("### Results")
        st.markdown(result)
        with st.expander("📥 Export Data (CSV / JSON / Markdown)", expanded=True):
            st.markdown("Write a SQL query below and download the results in your preferred format.")
            export_sql = st.text_input(
                "SQL Query",
                value="SELECT * FROM products ORDER BY price DESC LIMIT 50",
                key="export_sql_input"
            )
            try:
                cols, rows = fetch_sql_data(export_sql)
                col1, col2, col3 = st.columns(3)
                with col1:
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(cols)
                    writer.writerows(rows)
                    st.download_button(
                        "📄 CSV", data=output.getvalue(),
                        file_name="export.csv", mime="text/csv",
                        use_container_width=True,
                    )
                with col2:
                    data = [dict(zip(cols, row)) for row in rows]
                    st.download_button(
                        "📋 JSON", data=json.dumps(data, indent=2, default=str),
                        file_name="export.json", mime="application/json",
                        use_container_width=True,
                    )
                with col3:
                    md_lines = ["| " + " | ".join(cols) + " |"]
                    md_lines.append("| " + " | ".join("---" for _ in cols) + " |")
                    for row in rows:
                        escaped = [str(v) if v is not None else "" for v in row]
                        md_lines.append("| " + " | ".join(escaped) + " |")
                    md_lines.append(f"\n*{len(rows)} rows*")
                    st.download_button(
                        "📝 Markdown", data="\n".join(md_lines),
                        file_name="export.md", mime="text/markdown",
                        use_container_width=True,
                    )
            except Exception as e:
                st.error(f"Query failed: {e}")

if 'result' not in locals():
    st.markdown(
        """<div class='info-box'>
        <h4>🚀 Welcome to Groq + MCP Playground!</h4>
        <p>This app showcases how <strong>AI agents</strong> use tools to securely interact with data.</p>
        
        <h4>How to use:</h4>
        <ol>
            <li>Type a question about the store data (products, customers, orders)</li>
            <li>Click 'Run Query' and watch the AI work!</li>
        </ol>
        
        <h4>🧠 What's happening under the hood:</h4>
        <ul>
            <li><strong>Groq</strong> — Llama 3.3 70B running on Groq's ultra-fast inference</li>
            <li><strong>Agno</strong> — The library that manages the AI agent</li>
            <li><strong>SQLite</strong> — The local database with sample e-commerce data</li>
        </ul>
        </div>""", 
        unsafe_allow_html=True
    )
