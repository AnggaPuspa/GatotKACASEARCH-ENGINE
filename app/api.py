from fastapi import FastAPI, Query, HTTPException, BackgroundTasks, Path
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sqlite3, pathlib, re, subprocess, sys, logging
from typing import Optional, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GatotKaca-API")

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent  
DB_PATH = BASE_DIR / "app" / "search.db"
DATA_DIR = BASE_DIR / "data" / "sample"  

app = FastAPI(title="Indonesian Search Engine API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_match(q: str):
    """Build FTS match query with better tokenization"""
    tokens = re.findall(r'\b\w+\b', q.lower())
    if not tokens:
        return ""
    match_query = " OR ".join(f'"{token}"*' for token in tokens)
    return match_query

def highlight_snippet(snippet: str, query: str) -> str:
    if not snippet or not query:
        return snippet or ""
    
    words = re.findall(r'\b\w+\b', query.lower())
    
    for word in words:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        snippet = pattern.sub(f'<mark>{word}</mark>', snippet)
    
    return snippet

@app.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results"),
    page: int = Query(default=1, ge=1, description="Page number for pagination"),
    category: Optional[str] = Query(None, description="Filter by document category")
):
    try:
        if not DB_PATH.exists():
            raise HTTPException(
                status_code=500, 
                detail="Database belum diindeks. Jalankan proses indexing terlebih dahulu."
            )
        
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        
        match_query = build_match(q)
        if not match_query:
            return {"query": q, "results": [], "total": 0, "page": page, "pages": 0}
        
        offset = (page - 1) * limit
        
        params = [match_query]
        
        if category and category.lower() != "semua":
            sql_count = "SELECT COUNT(*) FROM docs_fts WHERE docs_fts MATCH ? AND category = ?"
            params.append(category)
            
            sql = """
                SELECT title, url, content, category,
                       snippet(docs_fts, 1, '<mark>', '</mark>', ' … ', 20) AS snippet,
                       rank AS score
                FROM docs_fts
                WHERE docs_fts MATCH ? AND category = ?
                ORDER BY rank
                LIMIT ? OFFSET ?;
            """
        else:
            sql_count = "SELECT COUNT(*) FROM docs_fts WHERE docs_fts MATCH ?"
            
            sql = """
                SELECT title, url, content, category,
                       snippet(docs_fts, 1, '<mark>', '</mark>', ' … ', 20) AS snippet,
                       rank AS score
                FROM docs_fts
                WHERE docs_fts MATCH ?
                ORDER BY rank
                LIMIT ? OFFSET ?;
            """
        
        total_count = con.execute(sql_count, params).fetchone()[0]
        total_pages = (total_count + limit - 1) // limit  
        
        params.extend([limit, offset])
        
        rows = con.execute(sql, params).fetchall()

        results = []
        for row in rows:
            result = {
                "title": row["title"],
                "url": row["url"] or "",
                "category": row["category"],
                "snippet": highlight_snippet(row["snippet"], q),
                "score": round(float(row["score"]), 4) if row["score"] is not None else 0
            }
            results.append(result)
        
        con.close()
        
        return {
            "query": q, 
            "results": results,
            "total": total_count,
            "page": page,
            "pages": total_pages,
            "match_query": match_query
        }
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/stats")
def get_stats():
    """Get search database statistics"""
    try:
        if not DB_PATH.exists():
            return {"error": "Database not found"}
            
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        total_docs = cur.execute("SELECT COUNT(*) FROM docs_fts").fetchone()[0]

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

@app.get("/reindex")
async def reindex(background_tasks: BackgroundTasks, data_dir: str = Query(None)):
    try:
        folder_path = pathlib.Path(data_dir) if data_dir else DATA_DIR
        
        if not folder_path.exists():
            return JSONResponse(
                status_code=404,
                content={"error": f"Folder not found: {folder_path}"}
            )
        
        def run_indexer(folder_path):
            try:
                indexer_path = BASE_DIR / "app" / "indexer.py"
                logger.info(f"Starting reindexing from {folder_path}")
                subprocess.run(
                    [sys.executable, str(indexer_path), str(folder_path)],
                    check=True
                )
                logger.info("Reindexing completed successfully")
            except Exception as e:
                logger.error(f"Error during reindexing: {str(e)}")
        
        background_tasks.add_task(run_indexer, folder_path)
        
        return {
            "status": "reindexing_started", 
            "message": f"Reindexing started from folder: {folder_path}",
            "folder": str(folder_path)
        }
        
    except Exception as e:
        logger.error(f"Reindex error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reindex error: {str(e)}")

@app.get("/analyze")
def analyze_corpus():
    try:
        if not DB_PATH.exists():
            return JSONResponse(
                status_code=404,
                content={"error": "Database belum diindeks. Jalankan proses indexing terlebih dahulu."}
            )
        
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        total_docs = cur.execute("SELECT COUNT(*) FROM docs_fts").fetchone()[0]
        
        categories = cur.execute(
            "SELECT category, COUNT(*) as count FROM docs_fts GROUP BY category ORDER BY count DESC"
        ).fetchall()
        category_stats = [{"category": row["category"], "count": row["count"]} for row in categories]
        
        all_content = " ".join([row[0] for row in cur.execute("SELECT content FROM docs_fts").fetchall()])
        words = all_content.split()
        word_count = {}
        
        for word in words:
            if len(word) > 2:  
                word_count[word] = word_count.get(word, 0) + 1
        
        top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]
        top_words_list = [{"word": word, "count": count} for word, count in top_words]
        
        con.close()
        
        return {
            "total_documents": total_docs,
            "categories": category_stats,
            "top_words": top_words_list,
            "database_path": str(DB_PATH)
        }
        
    except Exception as e:
        logger.error(f"Analyze error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analyze error: {str(e)}")

@app.get("/categories")
def get_categories():
    """Get all available document categories"""
    try:
        if not DB_PATH.exists():
            return JSONResponse(
                status_code=404,
                content={"error": "Database belum diindeks. Jalankan proses indexing terlebih dahulu."}
            )
        
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        
        categories = con.execute(
            "SELECT DISTINCT category FROM docs_fts ORDER BY category"
        ).fetchall()
        
        category_list = [row["category"] for row in categories]
        con.close()
        
        return {
            "categories": category_list
        }
        
    except Exception as e:
        logger.error(f"Categories error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Categories error: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Indonesian Search Engine is running"}

app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
