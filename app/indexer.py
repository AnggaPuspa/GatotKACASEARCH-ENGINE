import sys, sqlite3, pathlib, time, re, logging, os
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GatotKaca-Indexer")

BASE_DIR = pathlib.Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "search.db"

# Get comprehensive Indonesian stopwords from Sastrawi
factory = StopWordRemoverFactory()
STOPWORDS = set(factory.get_stop_words())
# Add some additional common words that might not be in the library
additional_stopwords = {"ya", "iya", "nya", "juga", "saja", "dapat", "adalah", "merupakan", "seperti", "sebagai", "oleh"}
STOPWORDS.update(additional_stopwords)

stemmer = StemmerFactory().create_stemmer()

def normalize(text: str) -> str:

    # Convert to lowercase and remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Split into words
    words = text.split()
    # Apply stemming and remove stopwords
    words = [stemmer.stem(w) for w in words if w not in STOPWORDS and len(w) > 1]
    return " ".join(words)

def ensure_db():
    """Create or recreate the search database with FTS5 virtual table"""
    logger.info(f"Creating/recreating search database at {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS docs_fts;")
    cur.execute("""
        CREATE VIRTUAL TABLE docs_fts USING fts5(
            title UNINDEXED,
            content,
            url UNINDEXED,
            category UNINDEXED,
            tokenize = 'unicode61 remove_diacritics 2'
        );
    """)
    con.commit()
    con.close()
    logger.info("Database schema created successfully")

def index_folder(folder: pathlib.Path):
    """Index all .txt files in the specified folder and its subfolders"""
    folder = folder.resolve()
    logger.info(f"Starting indexing process from folder: {folder}")
    
    if not folder.exists():
        logger.error(f"Folder does not exist: {folder}")
        return 0
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    count = 0
    start_time = time.time()
    
    # Detect and categorize files based on filename or content patterns
    for path in folder.rglob("*.txt"):
        try:
            # Read the file content
            text = path.read_text(encoding="utf-8", errors="ignore")
            
            # Extract URL if present
            url = ""
            if text.startswith("url:"):
                first, _, rest = text.partition("\n")
                url = first.replace("url:", "", 1).strip()
                text = rest
            
            # Format the title from the filename
            title = path.stem.replace("_", " ").title()
            
            # Determine category based on the filename
            filename_lower = path.name.lower()
            if "sejarah" in filename_lower:
                category = "Sejarah"
            elif "wisata" in filename_lower:
                category = "Wisata"
            elif "budaya" in filename_lower:
                category = "Budaya"
            else:
                category = "Lainnya"
            
            # Apply preprocessing to the content
            processed_text = normalize(text)
            
            # Insert into the database
            cur.execute(
                "INSERT INTO docs_fts (title, content, url, category) VALUES (?,?,?,?)",
                (title, processed_text, url, category),
            )
            
            count += 1
            if count % 10 == 0:
                logger.info(f"Processed {count} documents...")
                
        except Exception as e:
            logger.error(f"Error processing file {path}: {str(e)}")

    con.commit()
    con.close()
    
    elapsed_time = time.time() - start_time
    logger.info(f"✅ Completed indexing {count} documents in {elapsed_time:.2f} seconds")
    return count

def get_most_common_words(limit=10):
    """
    Get the most frequent words in the corpus
    """
    if not DB_PATH.exists():
        logger.error("Database not found. Please run indexing first.")
        return []
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # SQLite FTS5 doesn't provide direct word frequency, so we concatenate all content and analyze
    try:
        # Get all words from all documents
        result = cur.execute("SELECT content FROM docs_fts").fetchall()
        all_content = " ".join([row[0] for row in result])
        
        # Count word frequency
        words = all_content.split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        con.close()
        return sorted_words[:limit]
    except Exception as e:
        logger.error(f"Error analyzing word frequency: {str(e)}")
        con.close()
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app/indexer.py <folder>")
        sys.exit(1)

    folder = pathlib.Path(sys.argv[1])
    ensure_db()
    n = index_folder(folder)
    
    # Show statistics after indexing
    logger.info(f"✅ Successfully indexed {n} documents into {DB_PATH}")
    
    if n > 0:
        logger.info("Most common words in the corpus:")
        common_words = get_most_common_words(10)
        for word, count in common_words:
            logger.info(f"- '{word}': {count} occurrences")
