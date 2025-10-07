let searchStartTime = 0;
let currentPage = 1;
let totalPages = 1;
let currentQuery = '';
let currentCategory = 'Semua';
const RESULTS_PER_PAGE = 20;

document.addEventListener('DOMContentLoaded', function() {
  loadCategories();
  document.getElementById("q").focus();
  checkDatabaseStatus();
  initDarkMode();
  
  document.addEventListener('keydown', function(e) {
    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'SELECT') {
      if (e.key === 'ArrowLeft') {
        const prevBtn = document.getElementById('prevPage');
        if (!prevBtn.disabled) changePage(-1);
      } else if (e.key === 'ArrowRight') {
        const nextBtn = document.getElementById('nextPage');
        if (!nextBtn.disabled) changePage(1);
      }
    }
  });
});

function initDarkMode() {
  const darkModeToggle = document.getElementById('darkModeToggle');
  
  if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
  
  darkModeToggle.addEventListener('click', function() {
    if (document.documentElement.classList.contains('dark')) {
      document.documentElement.classList.remove('dark');
      localStorage.theme = 'light';
    } else {
      document.documentElement.classList.add('dark');
      localStorage.theme = 'dark';
    }
  });
}

function resetSearch() {
  document.getElementById("q").value = '';
  document.getElementById("category").value = 'Semua';
  hideElement("noResults");
  hideElement("results");
  hideElement("searchStats");
  hideElement("pagination");
  showElement("welcome");
  document.getElementById("q").focus();
}

function handleEnter(event) {
  if (event.key === 'Enter') {
    doSearch();
  }
}

function quickSearch(query) {
  document.getElementById("q").value = query;
  document.getElementById("category").value = 'Semua';
  currentPage = 1;
  doSearch();
}

async function checkDatabaseStatus() {
  try {
    const res = await fetch('/stats');
    const data = await res.json();
    
    if (data.error) {
      displayDatabaseError();
    } else if (data.total_documents === 0) {
      displayDatabaseEmpty();
    }
  } catch (error) {
    console.error('Database status check error:', error);
  }
}

function displayDatabaseError() {
  const welcome = document.getElementById("welcome");
  welcome.innerHTML = `
    <div class="text-center py-8">
      <div class="text-7xl mb-6 text-red-500 dark:text-red-400">
        <i class="fas fa-database"></i>
      </div>
      <h2 class="text-2xl font-bold text-red-600 dark:text-red-500 mb-4">Database belum diindeks</h2>
      <p class="text-slate-600 dark:text-slate-400 mb-6 max-w-md mx-auto">Silakan jalankan proses indexing terlebih dahulu</p>
      <button onclick="reindexDatabase()" 
        class="px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 shadow-md hover:shadow-lg transition-all"
        aria-label="Reindex database">
        <i class="fas fa-sync-alt mr-2"></i>Reindex Database
      </button>
    </div>
  `;
}

function displayDatabaseEmpty() {
  const welcome = document.getElementById("welcome");
  welcome.innerHTML = `
    <div class="text-center py-8">
      <div class="text-7xl mb-6 text-amber-500 dark:text-amber-400">
        <i class="fas fa-exclamation-circle"></i>
      </div>
      <h2 class="text-2xl font-bold text-amber-600 dark:text-amber-500 mb-4">Database kosong</h2>
      <p class="text-slate-600 dark:text-slate-400 mb-6 max-w-md mx-auto">Belum ada dokumen yang diindeks</p>
      <button onclick="reindexDatabase()" 
        class="px-6 py-3 bg-amber-600 text-white rounded-xl hover:bg-amber-700 shadow-md hover:shadow-lg transition-all"
        aria-label="Reindex database">
        <i class="fas fa-sync-alt mr-2"></i>Reindex Database
      </button>
    </div>
  `;
}


async function loadCategories() {
  try {
    const res = await fetch('/categories');
    const data = await res.json();
    
    if (!data.error && data.categories) {
      const categorySelect = document.getElementById("category");
      const currentValue = categorySelect.value;
      
      categorySelect.innerHTML = '<option value="Semua">Semua Kategori</option>';
      
      data.categories.forEach(category => {
        if (category) {  
          const option = document.createElement('option');
          option.value = category;
          option.textContent = category;
          categorySelect.appendChild(option);
        }
      });
      
      if (currentValue) {
        categorySelect.value = currentValue;
      }
    }
  } catch (error) {
    console.error('Error loading categories:', error);
  }
}

function showElement(id) {
  document.getElementById(id).classList.remove('hidden');
}

function hideElement(id) {
  document.getElementById(id).classList.add('hidden');
}

function showLoading() {
  document.getElementById("loading").classList.add('show');
}

function hideLoading() {
  document.getElementById("loading").classList.remove('show');
}

async function reindexDatabase() {
  try {
    const confirmed = confirm("Yakin ingin mengindeks ulang database? Proses ini mungkin memakan waktu beberapa saat.");
    if (!confirmed) return;

    document.getElementById('reindexBtn').innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Reindexing...';
    document.getElementById('reindexBtn').disabled = true;
    
    const res = await fetch('/reindex');
    const data = await res.json();
    
    alert(`Proses reindexing dimulai dari folder: ${data.folder}`);
    
    setTimeout(() => {
      document.getElementById('reindexBtn').innerHTML = '<i class="fas fa-sync-alt mr-2"></i> Reindex Database';
      document.getElementById('reindexBtn').disabled = false;
      loadCategories(); 
    }, 3000);
  } catch (error) {
    console.error('Reindex error:', error);
    alert('Terjadi kesalahan saat mengindeks ulang database.');
    document.getElementById('reindexBtn').innerHTML = '<i class="fas fa-sync-alt mr-2"></i> Reindex Database';
    document.getElementById('reindexBtn').disabled = false;
  }
}

// Analyze corpus
async function analyzeCorpus() {
  try {
    document.getElementById('analyzeBtn').innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Menganalisis...';
    document.getElementById('analyzeBtn').disabled = true;
    
    const res = await fetch('/analyze');
    if (!res.ok) {
      throw new Error(`HTTP error: ${res.status}`);
    }
    
    const data = await res.json();
    displayAnalysis(data);
    document.getElementById('analyzeBtn').innerHTML = '<i class="fas fa-chart-bar mr-2"></i> Analisis Korpus';
    document.getElementById('analyzeBtn').disabled = false;
  } catch (error) {
    console.error('Analysis error:', error);
    alert('Terjadi kesalahan saat menganalisis korpus.');
    document.getElementById('analyzeBtn').innerHTML = '<i class="fas fa-chart-bar mr-2"></i> Analisis Korpus';
    document.getElementById('analyzeBtn').disabled = false;
  }
}

function displayAnalysis(data) {
  const content = document.getElementById('analysisContent');
  
  if (data.error) {
    content.innerHTML = `
      <div class="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg text-red-700 dark:text-red-400">
        <p><i class="fas fa-exclamation-circle mr-2"></i>${data.error}</p>
      </div>
    `;
  } else {
    let html = `
      <div class="grid md:grid-cols-2 gap-6">
        <div class="bg-sky-50 dark:bg-sky-900/20 p-5 rounded-lg">
          <h4 class="font-semibold mb-3 text-sky-800 dark:text-sky-300">Statistik Dokumen</h4>
          <p class="mb-2"><span class="font-medium">Total dokumen:</span> ${data.total_documents}</p>
          <div class="mt-4">
            <h5 class="font-medium mb-2 text-sky-700 dark:text-sky-400">Distribusi Kategori:</h5>
            <ul class="space-y-2">
    `;
    
    const totalCount = data.categories.reduce((sum, cat) => sum + cat.count, 0);
    
    data.categories.forEach(cat => {
      const percentage = (cat.count / totalCount * 100).toFixed(1);
      const barWidth = `${percentage}%`;
      const category = cat.category || 'Tanpa kategori';
      
      let colorClass = 'bg-sky-500';
      if (category.toLowerCase().includes('wisata')) {
        colorClass = 'bg-green-500';
      } else if (category.toLowerCase().includes('budaya')) {
        colorClass = 'bg-purple-500';
      } else if (category.toLowerCase().includes('sejarah')) {
        colorClass = 'bg-blue-500';
      }
      
      html += `
        <li>
          <div class="flex items-center justify-between mb-1">
            <span class="font-medium text-slate-700 dark:text-slate-300">${category}</span>
            <span class="text-xs font-medium text-slate-600 dark:text-slate-400">${cat.count} (${percentage}%)</span>
          </div>
          <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2.5">
            <div class="${colorClass} h-2.5 rounded-full" style="width: ${barWidth}"></div>
          </div>
        </li>`;
    });
    
    html += `
            </ul>
          </div>
        </div>
        
        <div class="bg-green-50 dark:bg-green-900/20 p-5 rounded-lg">
          <h4 class="font-semibold mb-3 text-green-800 dark:text-green-300">Kata Paling Sering Muncul</h4>
          <ul class="space-y-2">
    `;

    const maxCount = Math.max(...data.top_words.map(w => w.count));
    
    data.top_words.forEach(word => {
      const percentage = (word.count / maxCount * 100).toFixed(0);
      const barWidth = `${percentage}%`;
      
      html += `
        <li>
          <div class="flex items-center justify-between mb-1">
            <span class="font-mono text-slate-700 dark:text-slate-300">${word.word}</span>
            <span class="text-xs font-medium text-slate-600 dark:text-slate-400">${word.count} kali</span>
          </div>
          <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2.5">
            <div class="bg-green-500 h-2.5 rounded-full" style="width: ${barWidth}"></div>
          </div>
        </li>`;
    });
    
    html += `
          </ul>
        </div>
      </div>
    `;
    
    content.innerHTML = html;
  }
  
  showElement('analysisModal');
  
  setTimeout(() => {
    document.querySelector('#analysisModal button').focus();
  }, 100);
  
  const modal = document.getElementById('analysisModal');
  const focusableElements = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];
  
  modal.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeAnalysisModal();
    }
    
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    }
  });
}

function closeAnalysisModal() {
  hideElement('analysisModal');
  document.getElementById('analyzeBtn').focus();
}

function changePage(delta) {
  const newPage = currentPage + delta;
  if (newPage >= 1 && newPage <= totalPages) {
    currentPage = newPage;
    doSearch(false); 
  }
}


function updatePaginationUI() {
  document.getElementById("currentPage").textContent = currentPage;
  document.getElementById("totalPages").textContent = totalPages;
  
  const prevBtn = document.getElementById("prevPage");
  const nextBtn = document.getElementById("nextPage");
  
  prevBtn.disabled = currentPage <= 1;
  nextBtn.disabled = currentPage >= totalPages;

  if (totalPages > 1) {
    showElement("pagination");
  } else {
    hideElement("pagination");
  }
}

async function doSearch(resetPage = true) {
  const q = document.getElementById("q").value.trim();
  const category = document.getElementById("category").value;
  
  if (!q) {
    alert("Silakan masukkan kata kunci pencarian");
    return;
  }

  currentQuery = q;
  currentCategory = category;
  if (resetPage) currentPage = 1;

  searchStartTime = Date.now();
  showLoading();
  hideElement("welcome");
  hideElement("results");
  hideElement("noResults");
  hideElement("searchStats");
  hideElement("pagination");

  try {s
    const params = new URLSearchParams({
      q: q,
      limit: RESULTS_PER_PAGE,
      page: currentPage
    });
    
    if (category !== 'Semua') {
      params.append('category', category);
    }
    
    const url = `/search?${params.toString()}`;
    const res = await fetch(url);
    
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    
    const data = await res.json();
    const searchTime = Date.now() - searchStartTime;
    
    totalPages = data.pages || 1;
    
    hideLoading();
    displayResults(data, q, searchTime);
    updatePaginationUI();
    
  } catch (error) {
    hideLoading();
    console.error('Search error:', error);
    displayError("Terjadi kesalahan saat mencari. Silakan coba lagi.");
  }
}

function displayResults(data, query, searchTime) {
  const resultsBox = document.getElementById("results");
  resultsBox.innerHTML = "";

  if (!data.results || data.results.length === 0) {
    showElement("noResults");
    return;
  }

  document.getElementById("resultCount").textContent = data.total;
  document.getElementById("queryText").textContent = query;
  document.getElementById("searchTime").textContent = searchTime;
  showElement("searchStats");

  const startIndex = (currentPage - 1) * RESULTS_PER_PAGE;

  data.results.forEach((result, index) => {
    const resultNumber = startIndex + index + 1;
    const item = document.createElement("div");
    item.className = "result-item bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-slate-200/70 dark:border-slate-700/50 hover:shadow-md";
    
    const snippet = result.snippet || "Tidak ada preview tersedia.";
    const cleanSnippet = snippet.replace(/<\/?mark>/g, (match) => 
      match === '<mark>' ? '<mark>' : '</mark>'
    );
    
    let categoryClass = "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300";
    if (result.category) {
      const category = result.category.toLowerCase();
      if (category.includes('sejarah')) {
        categoryClass = "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300";
      } else if (category.includes('wisata')) {
        categoryClass = "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300";
      } else if (category.includes('budaya')) {
        categoryClass = "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300";
      } else if (category.includes('tradisi')) {
        categoryClass = "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300";
      }
    }
    
    item.innerHTML = `
      <div class="flex items-start gap-4">
        <div class="hidden sm:flex shrink-0">
          <div class="w-12 h-12 bg-gradient-to-br from-sky-400 to-indigo-500 dark:from-sky-500 dark:to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
            <span class="text-white font-semibold text-lg">${resultNumber}</span>
          </div>
        </div>
        <div class="flex-1">
          <div class="flex flex-wrap items-center gap-3 mb-3">
            <span class="inline-flex sm:hidden items-center justify-center w-6 h-6 bg-sky-100 dark:bg-sky-900/50 text-sky-600 dark:text-sky-400 rounded-full text-xs font-semibold">
              ${resultNumber}
            </span>
            <h3 class="font-bold text-xl text-slate-800 dark:text-slate-100 hover:text-sky-600 dark:hover:text-sky-400 transition-colors line-clamp-2">
              ${escapeHtml(result.title)}
            </h3>
            <span class="${categoryClass} px-2.5 py-1 rounded-full text-xs font-medium">
              ${result.category || "Lainnya"}
            </span>
          </div>
          <p class="text-slate-600 dark:text-slate-300 mb-4 leading-relaxed">${cleanSnippet}</p>
          <div class="flex items-center justify-between">
            <div>
              ${result.url ? `
                <a href="${escapeHtml(result.url)}" target="_blank" 
                  class="inline-flex items-center text-sky-600 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-300 font-medium text-sm transition-colors"
                  aria-label="Baca dokumen ${escapeHtml(result.title)}">
                  <i class="fas fa-external-link-alt mr-2"></i>
                  Baca selengkapnya
                </a>
              ` : ''}
            </div>
            <span class="text-xs text-slate-500 dark:text-slate-400 font-mono">
              Skor: <span class="font-semibold">${parseFloat(result.score).toFixed(2)}</span>
            </span>
          </div>
        </div>
      </div>
    `;
    
    resultsBox.appendChild(item);
  });

  showElement("results");
}

function displayError(message) {
  const resultsBox = document.getElementById("results");
  resultsBox.innerHTML = `
    <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/30 rounded-xl p-6 text-center">
      <div class="text-5xl mb-4 text-red-500 dark:text-red-400">
        <i class="fas fa-exclamation-triangle"></i>
      </div>
      <h3 class="text-lg font-semibold text-red-800 dark:text-red-300 mb-2">Terjadi Kesalahan</h3>
      <p class="text-red-600 dark:text-red-400">${message}</p>
      <button onclick="location.reload()" 
              class="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              aria-label="Muat ulang halaman">
        <i class="fas fa-redo mr-2"></i>Muat Ulang Halaman
      </button>
    </div>
  `;
  showElement("results");
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}