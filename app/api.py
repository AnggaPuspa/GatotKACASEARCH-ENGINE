from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, pathlib, re

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent  # Go up one level to project root
DB_PATH = BASE_DIR / "app" / "search.db"

app = FastAPI(title="Indonesian Search Engine API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_match(q: str):
    """Build FTS match query with better tokenization"""
    # Remove special characters and split into tokens
    tokens = re.findall(r'\b\w+\b', q.lower())
    if not tokens:
        return ""
    
    # Use OR for better recall, with prefix matching
    match_query = " OR ".join(f'"{token}"*' for token in tokens)
    return match_query

def highlight_snippet(snippet: str, query: str) -> str:
    """Enhanced snippet highlighting"""
    if not snippet or not query:
        return snippet or ""
    
    # Get individual words from query
    words = re.findall(r'\b\w+\b', query.lower())
    
    for word in words:
        # Case-insensitive replacement while preserving original case
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        snippet = pattern.sub(f'<mark>{word}</mark>', snippet)
    
    return snippet

@app.get("/search")
def search(q: str = Query(..., min_length=1, description="Search query"), 
          limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results")):
    """
    Search endpoint with enhanced features
    """
    try:
        # Validate database exists
        if not DB_PATH.exists():
            raise HTTPException(status_code=500, detail="Search database not found. Please run indexer first.")
        
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        
        match_query = build_match(q)
        if not match_query:
            return {"query": q, "results": [], "total": 0}
        
        # Main search query with ranking
        sql = """
            SELECT title, url, content,
                   snippet(docs_fts, 1, '<mark>', '</mark>', ' … ', 20) AS snippet,
                   rank AS score
            FROM docs_fts
            WHERE docs_fts MATCH ?
            ORDER BY rank
            LIMIT ?;
        """
        
        rows = con.execute(sql, (match_query, limit)).fetchall()
        
        # Process results
        results = []
        for row in rows:
            result = {
                "title": row["title"],
                "url": row["url"] or "",
                "snippet": highlight_snippet(row["snippet"], q),
                "score": getattr(row, "score", 0)
            }
            results.append(result)
        
        con.close()
        
        return {
            "query": q, 
            "results": results,
            "total": len(results),
            "match_query": match_query  # For debugging
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/stats")
def get_stats():
    """Get search database statistics"""
    try:
        if not DB_PATH.exists():
            return {"error": "Database not found"}
            
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        # Get total documents
        total_docs = cur.execute("SELECT COUNT(*) FROM docs_fts").fetchone()[0]
        
        # Get sample titles
        samples = cur.execute("SELECT title FROM docs_fts LIMIT 5").fetchall()
        sample_titles = [row[0] for row in samples]
        
        con.close()
        
        return {
            "total_documents": total_docs,
            "sample_titles": sample_titles,
            "database_path": str(DB_PATH)
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Indonesian Search Engine is running"}

# Mount static files AFTER all API routes
app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
