# Outline Presentasi Sistem Gatot Kaca Search Engine

## 1. Pendahuluan (1 menit)

- Pengenalan sistem Information Retrieval Gatot Kaca Search Engine
- Tujuan: Pencarian informasi berbasis kata kunci untuk dokumen teks bahasa Indonesia
- Teknologi yang digunakan: Python, FastAPI, SQLite FTS5, HTML/TailwindCSS

## 2. Arsitektur Sistem (2 menit)

### 2.1. Komponen Utama

- **Backend**: Python + FastAPI
- **Database**: SQLite dengan FTS5 (Full-Text Search)
- **Frontend**: HTML + TailwindCSS + JavaScript

### 2.2. Alur Sistem

- **Indexing**: Proses mengolah dokumen mentah menjadi data terindeks
  - Pembacaan dokumen dari folder
  - Preprocessing teks
  - Penyimpanan ke dalam database FTS5
  
- **Searching**: Proses pencarian berdasarkan input kata kunci
  - Input query dari user
  - Preprocessing query
  - Pencarian di database
  - Ranking hasil berdasarkan relevansi
  - Penampilan hasil di UI

## 3. Proses Preprocessing (1.5 menit)

### 3.1. Tokenisasi

- Pemecahan teks menjadi token kata
- Penggunaan regex untuk membersihkan karakter khusus

### 3.2. Stopword Removal

- Penghapusan kata umum yang tidak memiliki nilai pencarian
- Penggunaan library Sastrawi.StopWordRemoverFactory

### 3.3. Stemming

- Pengubahan kata berimbuhan menjadi kata dasar
- Penggunaan library Sastrawi.StemmerFactory

### 3.4. Contoh Preprocessing

- Teks asli: "Wayang adalah seni pertunjukan tradisional Indonesia yang menggunakan boneka."
- Setelah preprocessing: "wayang seni pertunjuk tradisional indonesia guna boneka"

## 4. Database & Pencarian (1 menit)

### 4.1. SQLite FTS5 (Full-Text Search 5)

- Penjelasan tentang virtual table untuk pencarian teks
- Keunggulan dibanding LIKE query biasa: lebih cepat dan mendukung ranking

### 4.2. Ranking Algoritma

- Penjelasan singkat algoritma ranking di FTS5
- Implementasi scoring dan ordering berdasarkan relevansi

## 5. Fitur Utama Aplikasi (1.5 menit)

- Pencarian dengan kata kunci
- Filter berdasarkan kategori dokumen
- Tampilan snippet dengan highlight kata kunci
- Paginasi hasil pencarian
- Scoring relevansi hasil
- Analisis korpus (top words, statistik)
- Reindexing database

## 6. Demo Aplikasi (2 menit)

- Menunjukkan UI aplikasi
- Melakukan pencarian contoh
- Menampilkan hasil dan penjelasan komponen hasil
- Demonstrasi fitur filter dan pagination

## 7. Kesimpulan & Pengembangan Masa Depan (1 menit)

- Ringkasan kemampuan sistem
- Keterbatasan sistem saat ini
- Potensi pengembangan:
  - Penambahan semantik search
  - Peningkatan algoritma ranking
  - Implementasi pencarian dengan koreksi ejaan
  - Penambahan fitur autocomplete