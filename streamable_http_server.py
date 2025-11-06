import os 
import sqlite3
import logfire
import hashlib
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic_ai import ApprovalRequired
from duckduckgo_search import DDGS


load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_API_KEY"))
logfire.instrument_pydantic_ai()


app = FastMCP("Notes MCP Server")

# Global variable to track current logged-in user
current_user = None


# Set up the SQLite DB and notes table
def get_db():
    conn = sqlite3.connect('notes.db')
    conn.execute(
        'CREATE TABLE IF NOT EXISTS notes (id TEXT PRIMARY KEY, topic TEXT, content TEXT, tags TEXT, username TEXT)'
    )
    conn.execute(
        'CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)'
    )
    return conn


@app.tool()
def add(a: int, b: int) -> int:
    return a + b


@app.tool()
def register_user(username: str, password: str) -> str:
    """Register a new user with username and password."""
    conn = get_db()
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn.execute(
            'INSERT OR REPLACE INTO users (username, password) VALUES (?, ?)', 
            (username, hashed_password)
        )
        conn.commit()
        return f'User "{username}" registered successfully.'
    finally:
        conn.close()


@app.tool()
def login_user(username: str, password: str) -> str:
    """Login a user and set them as the current active user."""
    global current_user
    conn = get_db()
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?', 
            (username, hashed_password)
        )
        if cursor.fetchone():
            current_user = username
            return f'User "{username}" logged in successfully. Session active.'
        else:
            return 'Invalid username or password.'
    finally:
        conn.close()


@app.tool()
def logout_user() -> str:
    """Logout the current user."""
    global current_user
    if current_user:
        logged_out_user = current_user
        current_user = None
        return f'User "{logged_out_user}" logged out successfully.'
    else:
        return 'No user is currently logged in.'


@app.tool()
def get_current_user() -> str:
    """Get the currently logged-in user."""
    global current_user
    if current_user:
        return f'Current user: {current_user}'
    else:
        return 'No user is currently logged in.'


# Save note tool always requires approval (deferred tool)
@app.tool()
def save_note(topic: str, content: str, tags: str = '') -> str:
    """Save a note for the currently logged-in user."""
    global current_user
    
    if not current_user:
        return 'Error: No user is logged in. Please login first.'
    
    #aise ApprovalRequired("Manual approval always required for save_note.")
    # (The below real code will only execute after approval—if you wire up approval handling)
    conn = get_db()
    try:
        # Add username tag to the tags
        user_tag = f'user:{current_user}'
        if tags:
            tags = f'{tags}, {user_tag}'
        else:
            tags = user_tag
        
        note_id = hashlib.sha256((topic + content + current_user).encode()).hexdigest()
        conn.execute(
            'INSERT OR REPLACE INTO notes (id, topic, content, tags, username) VALUES (?, ?, ?, ?, ?)', 
            (note_id, topic, content, tags, current_user)
        )
        conn.commit()
        return f'Note on "{topic}" saved for user "{current_user}".'
    finally:
        conn.close()


@app.tool()
def get_note(topic: str) -> str:
    """
    Retrieve notes for a given topic for the current user.
    topic: The topic/tag for the note.
    """
    global current_user
    
    if not current_user:
        return 'Error: No user is logged in. Please login first.'
    
    conn = get_db()
    try:
        cursor = conn.execute(
            'SELECT content, tags FROM notes WHERE topic = ? AND username = ?', 
            (topic, current_user)
        )
        rows = cursor.fetchall()
        if rows:
            result = f'Notes for user "{current_user}":\n\n'
            for row in rows:
                result += f'Content: {row[0]}\nTags: {row[1]}\n\n'
            return result
        else:
            return f'No notes found for topic: "{topic}" for user "{current_user}".'
    finally:
        conn.close()


@app.tool()
def get_all_notes() -> str:
    """
    Retrieve all notes for the currently logged-in user.
    
    Returns:
        Formatted string containing all notes with their topics, content, and tags.
    """
    global current_user
    
    if not current_user:
        return 'Error: No user is logged in. Please login first.'
    
    conn = get_db()
    try:
        cursor = conn.execute(
            'SELECT id, topic, content, tags FROM notes WHERE username = ? ORDER BY topic',
            (current_user,)
        )
        rows = cursor.fetchall()
        
        if rows:
            result = f'Total notes for user "{current_user}": {len(rows)}\n\n'
            for idx, row in enumerate(rows, 1):
                result += f'--- Note {idx} ---\n'
                result += f'ID: {row[0]}\n'
                result += f'Topic: {row[1]}\n'
                result += f'Content: {row[2]}\n'
                result += f'Tags: {row[3] if row[3] else "No tags"}\n\n'
            return result
        else:
            return f'No notes found for user "{current_user}".'
    finally:
        conn.close()


@app.tool()
def get_all_users_notes() -> str:
    """
    Retrieve all notes from all users (admin function).
    
    Returns:
        Formatted string containing all notes grouped by user.
    """
    conn = get_db()
    try:
        cursor = conn.execute(
            'SELECT username, id, topic, content, tags FROM notes ORDER BY username, topic'
        )
        rows = cursor.fetchall()
        
        if rows:
            result = f'Total notes in database: {len(rows)}\n\n'
            current_user_display = None
            user_count = 0
            
            for idx, row in enumerate(rows, 1):
                if current_user_display != row[0]:
                    current_user_display = row[0]
                    user_count = 1
                    result += f'\n========== USER: {row[0]} ==========\n\n'
                else:
                    user_count += 1
                
                result += f'--- Note {user_count} ---\n'
                result += f'ID: {row[1]}\n'
                result += f'Topic: {row[2]}\n'
                result += f'Content: {row[3]}\n'
                result += f'Tags: {row[4] if row[4] else "No tags"}\n\n'
            return result
        else:
            return 'No notes found in the database.'
    finally:
        conn.close()


@app.tool()
def duckduckgo_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        Formatted search results as a string
    """
    try:
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))
        
        # Format results nicely
        formatted_results = []
        for idx, result in enumerate(results, 1):
            formatted_results.append(
                f"{idx}. {result['title']}\n"
                f"   URL: {result['href']}\n"
                f"   {result['body']}\n"
            )
        
        return "\n".join(formatted_results)
    
    except Exception as e:
        return f"Search failed: {str(e)}"


@app.tool()
def save_search_result(topic: str, query: str, result: str) -> str:
    """Save search results as a note for the current user."""
    global current_user
    
    if not current_user:
        return 'Error: No user is logged in. Please login first.'
    
    conn = get_db()
    try:
        user_tag = f'user:{current_user}, search'
        note_id = hashlib.sha256((topic + query + current_user).encode()).hexdigest()
        conn.execute(
            'INSERT OR REPLACE INTO notes (id, topic, content, tags, username) VALUES (?, ?, ?, ?, ?)', 
            (note_id, topic, result, user_tag, current_user)
        )
        conn.commit()
        return f'Search result for "{query}" saved under topic "{topic}" for user "{current_user}".'
    finally:
        conn.close()


@app.tool()
def delete_note(topic: str) -> str:
    """Delete a note by topic for the current user."""
    global current_user
    
    if not current_user:
        return 'Error: No user is logged in. Please login first.'
    
    conn = get_db()
    try:
        cursor = conn.execute(
            'DELETE FROM notes WHERE topic = ? AND username = ?', 
            (topic, current_user)
        )
        conn.commit()
        if cursor.rowcount > 0:
            return f'Note on "{topic}" deleted for user "{current_user}".'
        else:
            return f'No notes found for topic: "{topic}" for user "{current_user}".'
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(transport='streamable-http')
