import asyncio
import csv
import io
import json
import os
import sqlite3
import streamlit as st
from pathlib import Path
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters
from agno.models.google import Gemini

# Get the folder where this script is located
# This ensures we can find db_mcp_server.py no matter where we run from
PROJECT_DIR = Path(__file__).parent
DB_PATH = str(PROJECT_DIR / "store.db")


def fetch_sql_data(sql: str):
    """Run a SQL query and return (columns, rows)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(sql)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return cols, rows

st.set_page_config(page_title="✨ Gemini + MCP Playground", page_icon="✨", layout="wide")

st.markdown("<h1 class='main-header'>✨ Gemini + MCP Playground</h1>", unsafe_allow_html=True)
st.markdown("Chat with an AI agent that uses the Model Context Protocol to interact with data and tools")

with st.sidebar:
    st.header("🔑 Authentication")
    
    api_key = st.text_input("Gemini API Key", type="password",
                          help="Get your free API key from aistudio.google.com")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    
    st.markdown("---")
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
    2. **Gemini** (Google's AI) understands your request
    3. The **MCP server** translates it into database queries
    4. Results come back formatted as readable text
    
    **Export:** Say "export this as CSV" or 
    use the manual export section below results.
    """)

query = st.text_area("Your Query", placeholder="e.g., Show me all products sorted by price")

async def run_agent(message):
    if not os.getenv("GOOGLE_API_KEY"):
        return "Error: Please enter your Gemini API key in the sidebar"
    
    try:
        # Connect to our custom MCP server (db_mcp_server.py)
        # This lets the AI agent talk to the SQLite database
        # Use absolute path so it works from any directory
        mcp_server_path = PROJECT_DIR / "db_mcp_server.py"
        server_params = StdioServerParameters(
            command="python",
            args=[str(mcp_server_path)]
        )
        
        async with MCPTools(server_params=server_params) as mcp_tools:
            # Create the AI agent with Gemini and our database tools
            agent = Agent(
                model=Gemini(id="gemini-2.0-flash"),
                tools=[mcp_tools],
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
    if not api_key:
        st.error("Please enter your Gemini API key in the sidebar")
    elif not query:
        st.error("Please enter a query")
    else:
        with st.spinner("🧠 Gemini is thinking... calling database tools..."):
            result = asyncio.run(run_agent(query))
        
        st.markdown("### Results")
        st.markdown(result)
        
        # --- Export Section ---
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
                    # CSV
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
                    # JSON
                    data = [dict(zip(cols, row)) for row in rows]
                    st.download_button(
                        "📋 JSON", data=json.dumps(data, indent=2, default=str),
                        file_name="export.json", mime="application/json",
                        use_container_width=True,
                    )
                
                with col3:
                    # Markdown
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
        <h4>🚀 Welcome to Gemini + MCP Playground!</h4>
        <p>This app showcases how <strong>AI agents</strong> use the <strong>Model Context Protocol (MCP)</strong> 
        to securely interact with data.</p>
        
        <h4>How to use:</h4>
        <ol>
            <li>Enter your <strong>Gemini API key</strong> in the sidebar 
                (get one free at <a href='https://aistudio.google.com/apikey'>aistudio.google.com</a>)</li>
            <li>Type a question about the store data (products, customers, orders)</li>
            <li>Click 'Run Query' and watch the AI work!</li>
        </ol>
        
        <h4>🧠 What's happening under the hood:</h4>
        <ul>
            <li><strong>Gemini</strong> — Google's AI model that understands your question</li>
            <li><strong>Agno</strong> — The library that manages the AI agent</li>
            <li><strong>MCP (Model Context Protocol)</strong> — The standard way AI talks to tools</li>
            <li><strong>SQLite</strong> — The local database with sample e-commerce data</li>
        </ul>
        </div>""", 
        unsafe_allow_html=True
    )
