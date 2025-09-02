import sys, sqlite3, pathlib, time
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

BASE_DIR = pathlib.Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "search.db"

# stopword dasar Bahasa Indonesia
STOPWORDS = {"dan", "yang", "di", "ke", "dari", "atau", "untuk", "ini", "itu", "pada"}
stemmer = StemmerFactory().create_stemmer()

def normalize(text: str) -> str:
    # lowercase → stemming → hapus stopwords
    words = text.lower().split()
    words = [stemmer.stem(w) for w in words if w not in STOPWORDS]
    return " ".join(words)

def ensure_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS docs_fts;")
    cur.execute("""
        CREATE VIRTUAL TABLE docs_fts USING fts5(
            title UNINDEXED,
            content,
            url UNINDEXED,
            tokenize = 'unicode61 remove_diacritics 2'
        );
    """)
    con.commit()
    con.close()

def index_folder(folder: pathlib.Path):
    folder = folder.resolve()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    count = 0
    for path in folder.rglob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        url = ""
        if text.startswith("url:"):
            first, _, rest = text.partition("\n")
            url = first.replace("url:", "", 1).strip()
            text = rest
        title = path.stem.replace("_", " ").title()

        cur.execute(
            "INSERT INTO docs_fts (title, content, url) VALUES (?,?,?)",
            (title, normalize(text), url),
        )
        count += 1

    con.commit()
    con.close()
    return count

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app/indexer.py <folder>")
        sys.exit(1)

    folder = pathlib.Path(sys.argv[1])
    ensure_db()
    n = index_folder(folder)
    print(f"✅ Indexed {n} docs into {DB_PATH}")
