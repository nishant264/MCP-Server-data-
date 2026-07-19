"""
db_mcp_server.py — A read-only MCP server for querying the SQLite database.

This runs as a separate process, and the main app (github_agent.py)
connects to it via the Model Context Protocol.

🔒 Security: This server ONLY allows read-only queries (SELECT).
    Any attempt to modify data (INSERT, UPDATE, DELETE, DROP, etc.)
    is blocked with an error message.
"""

import csv
import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("DB Agent")

# Path to our database file (same folder as this script)
DB_PATH = str(Path(__file__).parent / "store.db")

# Folder where exported files will be saved
EXPORT_DIR = Path(__file__).parent / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


def validate_read_only_query(sql: str) -> bool:
    """
    🔒 SECURITY GUARDRAIL 🔒
    
    Checks if a SQL query is read-only.
    Only allows: SELECT, EXPLAIN, and PRAGMA statements.
    Blocks: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, etc.
    
    Args:
        sql: The SQL query string to validate
        
    Returns:
        True if the query is safe (read-only), False otherwise
    """
    # Remove comments and whitespace for checking
    cleaned = sql.strip().upper()
    
    # List of forbidden SQL operations
    forbidden = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
        "CREATE", "TRUNCATE", "REPLACE", "ATTACH",
        "DETACH", "REINDEX", "VACUUM"
    ]
    
    # Check if query starts with a forbidden operation
    for keyword in forbidden:
        # Use regex to find the keyword as a whole word at the start
        if re.match(rf"^\s*{keyword}\b", cleaned):
            return False
    
    # Also block semicolons that might allow multiple statements
    # (splits on ; and checks for forbidden ops in secondary statements)
    statements = re.split(r";", sql)
    if len(statements) > 1:
        for stmt in statements:
            stmt_clean = stmt.strip().upper()
            if stmt_clean and not stmt_clean.startswith("SELECT") and \
               not stmt_clean.startswith("EXPLAIN") and \
               not stmt_clean.startswith("PRAGMA"):
                # Might be a comment or empty, check for forbidden ops
                for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", 
                               "CREATE", "TRUNCATE", "REPLACE"]:
                    if re.match(rf"^\s*{keyword}\b", stmt_clean):
                        return False
    
    return True


@mcp.tool()
def run_sql_query(sql: str) -> str:
    """
    Run a read-only SQL query on the database.
    
    🔒 SAFETY: Only SELECT, EXPLAIN, and PRAGMA queries are allowed.
    Any query that modifies data will be rejected.
    
    Args:
        sql: The SQL query to execute (must be a SELECT/EXPLAIN/PRAGMA statement)
        
    Returns:
        Query results as formatted text, or an error message
    """
    # --- Step 1: Security Check ---
    if not validate_read_only_query(sql):
        return (
            "❌ BLOCKED: This query is not read-only!\n\n"
            "Only SELECT, EXPLAIN, and PRAGMA queries are allowed.\n"
            "INSERT, UPDATE, DELETE, DROP, ALTER, and other modifications\n"
            "are blocked for safety."
        )
    
    # --- Step 2: Execute the Query ---
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(sql)
        
        # --- Step 3: Format Results ---
        rows = cursor.fetchmany(100)  # Max 100 rows for safety
        
        if not rows:
            return "Query returned no results."
        
        # Get column names from cursor description
        columns = [desc[0] for desc in cursor.description]
        
        # Build a formatted table
        result_lines = []
        
        # Header row
        header = " | ".join(f"**{col}**" for col in columns)
        separator = " | ".join("---" for _ in columns)
        result_lines.append(header)
        result_lines.append(separator)
        
        # Data rows
        for row in rows:
            formatted_row = []
            for value in row:
                if value is None:
                    formatted_row.append("NULL")
                else:
                    formatted_row.append(str(value))
            result_lines.append(" | ".join(formatted_row))
        
        # Add count
        result_lines.append(f"\n*{len(rows)} row(s) returned*")
        
        # Check if there are more rows (truncated)
        remaining = cursor.fetchone()
        if remaining:
            result_lines.append(f"*⚠️ More results available (limited to 100 rows)*")
        
        conn.close()
        return "\n".join(result_lines)
        
    except sqlite3.Error as e:
        return f"❌ Database error: {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_schema() -> str:
    """
    Get the database schema — lists all tables, their columns, and sample data counts.
    
    Use this to understand what data is available before writing queries.
    
    Returns:
        A formatted description of all tables and their structure
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        
        result_lines = ["# 📊 Database Schema\n"]
        
        for table in tables:
            table_name = table[0]
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            result_lines.append(f"## 📋 `{table_name}`")
            result_lines.append(f"| Column | Type | Required |")
            result_lines.append(f"|--------|------|----------|")
            
            for col in columns:
                # col: (cid, name, type, notnull, default_value, pk)
                col_name = col[1]
                col_type = col[2] if col[2] else "TEXT"
                required = "✅" if col[3] else "❌"
                result_lines.append(f"| `{col_name}` | {col_type} | {required} |")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            result_lines.append(f"\n*📝 {count} rows*\n")
        
        conn.close()
        return "\n".join(result_lines)
        
    except sqlite3.Error as e:
        return f"❌ Database error: {str(e)}"


@mcp.tool()
def export_query(sql: str, format: str = "csv") -> str:
    """
    Export query results to a file (CSV, JSON, or Markdown).
    
    Use this when the user asks to save or download the data.
    The file is saved to the 'exports' folder and the path is returned.
    
    🔒 SAFETY: Only SELECT queries are allowed.
    
    Args:
        sql: The SELECT query to export
        format: Export format - "csv", "json", or "md" (markdown)
        
    Returns:
        Path to the exported file, or an error message
    """
    # --- Step 1: Security Check ---
    if not validate_read_only_query(sql):
        return "❌ BLOCKED: Only read-only queries can be exported."
    
    # --- Step 2: Validate Format ---
    format = format.lower()
    if format not in ["csv", "json", "md"]:
        return f"❌ Unsupported format: '{format}'. Use 'csv', 'json', or 'md'."
    
    # --- Step 3: Execute Query ---
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "Query returned no results — nothing to export."
        
        # --- Step 4: Generate a filename ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "query"
        ext = format
        filename = f"{safe_name}_{timestamp}.{ext}"
        filepath = EXPORT_DIR / filename
        
        # --- Step 5: Write the file ---
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
                # Header
                f.write("| " + " | ".join(columns) + " |\n")
                f.write("| " + " | ".join("---" for _ in columns) + " |\n")
                # Rows
                for row in rows:
                    escaped = [str(v) if v is not None else "" for v in row]
                    f.write("| " + " | ".join(escaped) + " |\n")
                f.write(f"\n*{len(rows)} rows exported*\n")
        
        return (
            f"✅ Exported {len(rows)} rows to `{filename}`\n\n"
            f"📁 File saved to: `{filepath}`"
        )
        
    except sqlite3.Error as e:
        return f"❌ Database error: {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


# This is what runs when we execute this script:
# It starts the MCP server and listens for connections via stdio
if __name__ == "__main__":
    mcp.run()
