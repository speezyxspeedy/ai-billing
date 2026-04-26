// ── State ──────────────────────────────────
// Auto-detect API base: if opened via file://, use localhost; if via http(s), use same host
let API_BASE = '';
if (window.location.protocol === 'file:') {
  API_BASE = 'http://127.0.0.1:8001';
} else if (
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') &&
  window.location.port !== '8001'
) {
  API_BASE = 'http://127.0.0.1:8001';
}
let CURRENCY  = '₹';
let DEFAULT_GST = 18;
let currentItems = [];
let currentShop = null;
let isLoggedIn = false;

// ── Load login state from localStorage ──────
function loadLoginState() {
  const saved = localStorage.getItem('shop_data');
  if (saved) {
    try {
      const data = JSON.parse(saved);
      currentShop = data.shop;
      isLoggedIn = true;
    } catch (e) {
      localStorage.removeItem('shop_data');
    }
  }
}

function saveLoginState() {
  if (isLoggedIn && currentShop) {
    localStorage.setItem('shop_data', JSON.stringify({ shop: currentShop }));
  }
}

function clearLoginState() {
  localStorage.removeItem('shop_data');
  currentShop = null;
  isLoggedIn = false;
}

loadLoginState();

// ── Tab routing ────────────────────────────
function setActivePage(page) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

  const tab = document.querySelector(`.nav-tab[data-page="${page}"]`);
  const pageEl = document.getElementById('page-' + page);
  if (tab) tab.classList.add('active');
  if (pageEl) pageEl.classList.add('active');

  if (page === 'billing' && isLoggedIn) {
    loadBillingHistory();
  }
}

function updateTabVisibility() {
  const softwareTabs = document.querySelectorAll('.software-tab');
  softwareTabs.forEach(tab => {
    // Billing tab is always visible; others require login
    if (tab.dataset.page === 'billing') {
      tab.style.display = 'flex';
    } else {
      tab.style.display = isLoggedIn ? 'flex' : 'none';
    }
  });

  const authTabs = document.querySelectorAll('.nav-tab[data-page="login"], .nav-tab[data-page="register"]');
  authTabs.forEach(tab => {
    tab.style.display = isLoggedIn ? 'none' : 'flex';
  });
  
  // Update navbar elements
  const avatar = document.getElementById('userAvatar');
  const logoutBtn = document.getElementById('logoutBtn');
  
  if (isLoggedIn && currentShop) {
    avatar.textContent = currentShop.shop_name.substring(0, 2).toUpperCase();
    avatar.style.display = 'flex';
    logoutBtn.style.display = 'inline-block';
  } else {
    avatar.style.display = 'none';
    logoutBtn.style.display = 'none';
  }

  // Only auto-redirect on initial page load, not when already on a valid page
  const activePage = document.querySelector('.page.active');
  const currentPageId = activePage?.id;
  // Billing page is accessible without login; other software pages require auth
  const authRequiredPages = ['page-products', 'page-history', 'page-reports', 'page-settings'];
  const isAuthRequiredPage = authRequiredPages.includes(currentPageId);
  const isAuthPage = ['page-login', 'page-register'].includes(currentPageId);
  
  if (isLoggedIn && isAuthPage) {
    // Redirect from auth pages to billing if logged in
    setActivePage('billing');
  } else if (!isLoggedIn && isAuthRequiredPage) {
    // Redirect from auth-required software pages to login if not logged in
    setActivePage('login');
  } else if (!activePage) {
    // Default to billing page (accessible without login)
    setActivePage('billing');
  }
}

document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const page = tab.dataset.page;
    
    // If trying to access non-billing software pages without login, redirect to login
    if (!isLoggedIn && ['products', 'history', 'reports', 'settings'].includes(page)) {
      setActivePage('login');
      setStatus('Please sign in first', 'warn');
      return;
    }
    
    setActivePage(page);
  });
});

// ── Status badge ───────────────────────────
const statusBadge = document.getElementById('statusBadge');
function setStatus(text, kind = 'info') {
  statusBadge.textContent = text;
  const map = {
    info:    ['#eef4ff', '#1d4ed8'],
    success: ['#ecfdf3', '#15803d'],
    error:   ['#fef2f2', '#dc2626'],
    warn:    ['#fff7ed', '#d97706']
  };
  const [bg, fg] = map[kind] || map.info;
  statusBadge.style.background = bg;
  statusBadge.style.color = fg;
}

// ── Helpers ────────────────────────────────
function money(v) {
  return `${CURRENCY}${Number(v || 0).toFixed(2)}`;
}
function computeLineTotal(item) {
  const sub = Number(item.price) * Number(item.quantity);
  return sub + sub * Number(item.gst) / 100;
}

// ── Generic API call ───────────────────────
async function apiCall(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  const apiKey = document.getElementById('apiKeyInput')?.value?.trim();
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;
  let res;
  try {
    res = await fetch(API_BASE + path, { headers, ...opts });
  } catch (networkErr) {
    throw new Error(`Backend unreachable. Is the server running at ${API_BASE}?`);
  }
  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const text = await res.text();
    throw new Error(
      `Server returned HTML (status ${res.status}). ` +
      (res.status >= 500 ? 'The backend may be down or restarting.' : 'Check the API path.')
    );
  }
  let data;
  try {
    data = await res.json();
  } catch (e) {
    throw new Error('Invalid JSON received from server.');
  }
  if (!res.ok) throw new Error(data.message || data.detail || `API error ${res.status}`);
  // Some endpoints return HTTP 200 with an error message
  if (data.message && (data.message.toLowerCase().includes('error') || !data.shop && !data.shop_id && !Array.isArray(data))) {
    // Only treat as error if it's clearly not a successful data response
    if (!data.items && !data.bill_id && !data.products) {
      throw new Error(data.message);
    }
  }
  return data;
}

// ── Bill table ─────────────────────────────
function refreshSummary(lastBillId = null) {
  let subtotal = 0;
  let totalGst = 0;
  
  currentItems.forEach(item => {
    const sub = Number(item.price) * Number(item.quantity);
    const gst = sub * Number(item.gst) / 100;
    subtotal += sub;
    totalGst += gst;
  });
  
  const grandTotal = subtotal + totalGst;
  
  document.getElementById('subtotal').textContent = money(subtotal);
  document.getElementById('totalGst').textContent = money(totalGst);
  document.getElementById('grandTotal').textContent = money(grandTotal);
  document.getElementById('itemsCount').textContent = String(currentItems.length);
  document.getElementById('itemCountBadge').textContent = `${currentItems.length} items`;
  
  // Populate items list in summary
  const summaryItemsList = document.getElementById('summaryItemsList');
  if (currentItems.length === 0) {
    summaryItemsList.innerHTML = '<div style="color:var(--muted);">No items added</div>';
  } else {
    let itemsHtml = '';
    currentItems.forEach(item => {
      const itemTotal = Number(item.price) * Number(item.quantity);
      itemsHtml += `
        <div style="display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid #f0f0f0;">
          <span><strong>${item.item_name || '(unnamed)'}</strong></span>
          <span>${item.quantity}x ${money(item.price)}</span>
        </div>
      `;
    });
    summaryItemsList.innerHTML = itemsHtml;
  }
  
  if (lastBillId !== null) document.getElementById('billId').textContent = lastBillId;
}

function renderTable() {
  const tbody = document.getElementById('billTableBody');
  tbody.innerHTML = '';
  if (currentItems.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:24px;font-size:13px;">No items yet. Use AI Quick Entry above or click "+ Add Row".</td></tr>`;
    refreshSummary();
    return;
  }
  currentItems.forEach((item, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="text"   value="${item.item_name || ''}" data-index="${idx}" data-field="item_name" style="width:100%;"></td>
      <td><input type="number" value="${item.quantity}" min="1" max="1000" data-index="${idx}" data-field="quantity" style="width:68px;"></td>
      <td><input type="number" value="${item.price}"   min="0" max="1000000" step="0.01" data-index="${idx}" data-field="price" style="width:90px;"></td>
      <td><input type="number" value="${item.gst}"     min="0" max="100" step="0.5"  data-index="${idx}" data-field="gst" style="width:68px;"></td>
      <td style="font-weight:600; color:var(--primary);">${money(computeLineTotal(item))}</td>
      <td><button class="btn-danger" data-remove="${idx}" style="padding:5px 10px; font-size:12px;">Del</button></td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll('input').forEach(inp => {
    inp.addEventListener('input', e => {
      const i = Number(e.target.dataset.index);
      const f = e.target.dataset.field;
      let value = e.target.value;

      if (f === 'item_name') {
        currentItems[i][f] = value;
      } else {
        let numValue = Number(value);
        if (Number.isNaN(numValue)) numValue = 0;

        if (f === 'quantity') {
          numValue = Math.max(1, Math.min(1000, Math.floor(numValue)));
          e.target.value = numValue;
        }

        if (f === 'price') {
          numValue = Math.max(0, numValue);
        }

        if (f === 'gst') {
          numValue = Math.max(0, Math.min(100, numValue));
          e.target.value = numValue;
        }

        currentItems[i][f] = numValue;
      }

      // update only line total cell, not full re-render (avoid cursor jump)
      const row = e.target.closest('tr');
      if (row) {
        const totalCell = row.cells[4];
        if (totalCell) totalCell.textContent = money(computeLineTotal(currentItems[i]));
      }
      refreshSummary();
    });
  });

  tbody.querySelectorAll('[data-remove]').forEach(btn => {
    btn.addEventListener('click', () => {
      currentItems.splice(Number(btn.dataset.remove), 1);
      renderTable();
    });
  });
  refreshSummary();
}

// ── Generate AI bill ───────────────────────
document.getElementById('generateBtn').addEventListener('click', async () => {
  const text = document.getElementById('billText').value.trim();
  if (!text) { setStatus('Please enter bill text', 'warn'); return; }
  setStatus('Generating AI bill...', 'warn');
  try {
    const data = await apiCall('/ai/auto-bill', {
      method: 'POST',
      body: JSON.stringify({ text })
    });
    if (data.message?.toLowerCase().includes('error')) throw new Error(data.message);
    currentItems = data.items || [];
    renderTable();
    refreshSummary(data.bill_id ?? '—');
    setStatus(data.message || 'Bill created successfully', 'success');
  } catch (e) {
    setStatus(e.message || 'Could not generate bill', 'error');
  }
});

// ── Parse only ────────────────────────────
document.getElementById('parseBtn').addEventListener('click', async () => {
  const text = document.getElementById('billText').value.trim();
  if (!text) { setStatus('Please enter bill text', 'warn'); return; }
  setStatus('Parsing bill text...', 'warn');
  try {
    const data = await apiCall('/ai/parse-bill', {
      method: 'POST',
      body: JSON.stringify({ text })
    });
    currentItems = (data.items || []).map(i => ({
      item_name: i.item_name || i.matched_item || i.input_item || '',
      quantity: i.quantity || 1,
      price: i.price || 0,
      gst: i.gst || DEFAULT_GST
    }));
    renderTable();
    refreshSummary();
    setStatus('Parsed. Fill price/GST manually or use Generate.', 'success');
  } catch (e) {
    setStatus(e.message || 'Parse failed', 'error');
  }
});

// ── Clear ─────────────────────────────────
document.getElementById('clearBtn').addEventListener('click', () => {
  document.getElementById('billText').value = '';
  currentItems = [];
  renderTable();
  document.getElementById('billId').textContent = '—';
  setStatus('Cleared', 'info');
});

// ── Save grid ─────────────────────────────
document.getElementById('saveManualBtn').addEventListener('click', async () => {
  if (!currentItems.length) { setStatus('No items to save', 'warn'); return; }
  setStatus('Saving bill...', 'warn');
  try {
    const payload = {
      items: currentItems.map(i => ({
        item_name: i.item_name,
        quantity:  Number(i.quantity),
        price:     Number(i.price),
        gst:       Number(i.gst)
      }))
    };
    const data = await apiCall('/bill', { method: 'POST', body: JSON.stringify(payload) });
    if (data.message?.toLowerCase().includes('error')) throw new Error(data.message);
    refreshSummary(data.bill_id ?? '—');
    setStatus(data.message || 'Bill saved successfully', 'success');
  } catch (e) {
    setStatus(e.message || 'Save failed', 'error');
  }
});

// ── Add row ───────────────────────────────
document.getElementById('addRowBtn').addEventListener('click', () => {
  currentItems.push({ item_name: '', quantity: 1, price: 0, gst: DEFAULT_GST });
  renderTable();
  setStatus('Row added', 'info');
});

// ── Add multiple rows ──────────────────────
if (document.getElementById('addMultipleRowsBtn')) {
  document.getElementById('addMultipleRowsBtn').addEventListener('click', () => {
    for (let i = 0; i < 10; i++) {
      currentItems.push({ item_name: '', quantity: 1, price: 0, gst: DEFAULT_GST });
    }
    renderTable();
    setStatus('10 rows added', 'success');
  });
}

// ── Clear all ──────────────────────────────
if (document.getElementById('clearAllBtn')) {
  document.getElementById('clearAllBtn').addEventListener('click', () => {
    if (currentItems.length === 0) {
      setStatus('Already empty', 'info');
      return;
    }
    if (confirm(`Clear all ${currentItems.length} items? This cannot be undone.`)) {
      currentItems = [];
      renderTable();
      document.getElementById('billId').textContent = '—';
      setStatus('All items cleared', 'success');
    }
  });
}

// ── Print bill ────────────────────────────
if (document.getElementById('printBillBtn')) {
  document.getElementById('printBillBtn').addEventListener('click', () => {
    if (currentItems.length === 0) {
      setStatus('No items to print', 'warn');
      return;
    }
    
    // Populate print template
    let subtotal = 0;
    let totalGst = 0;
    const printItemsBody = document.getElementById('printItemsBody');
    printItemsBody.innerHTML = '';
    
    currentItems.forEach(item => {
      const sub = Number(item.price) * Number(item.quantity);
      const gst = sub * Number(item.gst) / 100;
      subtotal += sub;
      totalGst += gst;
      
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${item.item_name}</td>
        <td>${item.quantity}</td>
        <td>${money(item.price)}</td>
        <td>${item.gst}%</td>
        <td>${money(sub + gst)}</td>
      `;
      printItemsBody.appendChild(tr);
    });
    
    const grandTotal = subtotal + totalGst;
    document.getElementById('printSubtotal').textContent = money(subtotal);
    document.getElementById('printTotalGst').textContent = money(totalGst);
    document.getElementById('printGrandTotal').textContent = money(grandTotal);
    document.getElementById('printDateTime').textContent = new Date().toLocaleString();
    document.getElementById('printBillId').textContent = document.getElementById('billId').textContent;
    const businessName = document.getElementById('businessName')?.value || 'AI Billing System';
    document.getElementById('printBusinessName').textContent = businessName;
    
    // Trigger print
    window.print();
    setStatus('Printing...', 'info');
  });
}

// ── Email bill ────────────────────────────
if (document.getElementById('emailBillBtn')) {
  document.getElementById('emailBillBtn').addEventListener('click', () => {
    if (currentItems.length === 0) {
      setStatus('No items to email', 'warn');
      return;
    }
    setStatus('Email feature coming soon', 'warn');
  });
}

// ── Predict price ─────────────────────────
document.getElementById('predictPriceBtn').addEventListener('click', async () => {
  const item = document.getElementById('predictInput').value.trim();
  if (!item) { setStatus('Enter item name for prediction', 'warn'); return; }
  setStatus('Predicting price...', 'warn');
  try {
    const data = await apiCall(`/ai/predict-price?item_name=${encodeURIComponent(item)}`);
    document.getElementById('predictResult').textContent =
      `${data.item_name}: ${money(data.predicted_price)}  |  Method: ${data.method}`;
    setStatus('Prediction ready', 'success');
  } catch (e) {
    setStatus(e.message || 'Prediction failed', 'error');
    document.getElementById('predictResult').textContent = '';
  }
});

// ── Load products ─────────────────────────
async function doLoadProducts() {
  setStatus('Loading products...', 'warn');
  try {
    const data = await apiCall('/products');
    const list = document.getElementById('productsList');
    const search = (document.getElementById('productSearch')?.value || '').toLowerCase();
    const filtered = search ? data.filter(p => p.item_name.toLowerCase().includes(search)) : data;
    list.innerHTML = '';

    if (!filtered.length) {
      list.innerHTML = `<div style="padding:20px; text-align:center; color:var(--muted); font-size:13px;">No products found.</div>`;
      return;
    }

    // Group products by category
    const grouped = {};
    filtered.forEach(p => {
      const cat = p.category || 'Other';
      if (!grouped[cat]) grouped[cat] = [];
      grouped[cat].push(p);
    });

    // Sort categories and create sections
    const sortedCategories = Object.keys(grouped).sort();

    sortedCategories.forEach(category => {
      const products = grouped[category];

      // Category header
      const headerDiv = document.createElement('div');
      headerDiv.style.cssText = `
        padding: 12px 14px;
        background: var(--card);
        border-bottom: 1px solid var(--border);
        font-weight: 600;
        font-size: 14px;
        color: var(--primary);
        position: sticky;
        top: 0;
        z-index: 1;
      `;
      headerDiv.textContent = `${category} (${products.length})`;
      list.appendChild(headerDiv);

      // Products in this category
      products.forEach(p => {
        const div = document.createElement('div');
        div.className = 'product-item';
        div.innerHTML = `
          <div>
            <div class="product-name">${p.item_name}</div>
            <div class="product-meta">GST: ${p.gst}%</div>
          </div>
          <div class="product-price">${money(p.price)}</div>
        `;
        list.appendChild(div);
      });
    });

    setStatus('Products loaded', 'success');
  } catch (e) {
    setStatus(e.message || 'Could not load products', 'error');
  }
}

document.getElementById('loadProductsBtn').addEventListener('click', doLoadProducts);
document.getElementById('refreshProductsBtn').addEventListener('click', doLoadProducts);
document.getElementById('productSearch').addEventListener('input', () => {
  const list = document.getElementById('productsList');
  if (list.children.length && list.firstChild.className === 'product-item') doLoadProducts();
});

// ── Load history ──────────────────────────
document.getElementById('loadHistoryBtn').addEventListener('click', async () => {
  setStatus('Loading history...', 'warn');
  try {
    const data = await apiCall('/bills');
    const tbody = document.getElementById('historyTableBody');
    tbody.innerHTML = '';
    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:30px;font-size:13px;">No bill records found.</td></tr>`;
      return;
    }
    data.forEach(bill => {
      const itemNames = bill.items ? bill.items.map(item => item.item_name).join(', ') : '—';
      const truncatedItems = itemNames.length > 50 ? itemNames.substring(0, 50) + '...' : itemNames;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>#${bill.bill_id}</strong></td>
        <td>${bill.created_at}</td>
        <td title="${itemNames}">${truncatedItems}</td>
        <td style="font-weight:600; color:var(--primary);">${money(bill.total)}</td>
        <td><span class="tag tag-success">Saved</span></td>
        <td><button class="btn-outline" style="padding:5px 10px; font-size:12px;">View</button></td>
      `;
      tbody.appendChild(tr);
    });
    setStatus('History loaded', 'success');
  } catch (e) {
    setStatus(e.message || 'Could not load history', 'error');
  }
});

// ── Load billing history (for billing page) ──
async function loadBillingHistory() {
  try {
    const data = await apiCall('/bills');
    const tbody = document.getElementById('billingHistoryTableBody');
    tbody.innerHTML = '';
    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:20px;font-size:13px;">No recent bills found.</td></tr>`;
      return;
    }

    // Show only last 10 bills for billing page
    const recentBills = data.slice(0, 10);
    recentBills.forEach(bill => {
      const itemNames = bill.items ? bill.items.map(item => item.item_name).join(', ') : '—';
      const truncatedItems = itemNames.length > 40 ? itemNames.substring(0, 40) + '...' : itemNames;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>#${bill.bill_id}</strong></td>
        <td>${bill.created_at}</td>
        <td title="${itemNames}">${truncatedItems}</td>
        <td style="font-weight:600; color:var(--primary);">${money(bill.total)}</td>
        <td><span class="tag tag-success">Saved</span></td>
        <td><button class="btn-outline" style="padding:4px 8px; font-size:11px;" onclick="loadBillToGrid(${bill.bill_id})">Load</button></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    const tbody = document.getElementById('billingHistoryTableBody');
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:20px;font-size:13px;">Could not load history.</td></tr>`;
  }
}

// ── Load bill to grid ──────────────────────
async function loadBillToGrid(billId) {
  try {
    const data = await apiCall('/bills');
    const bill = data.find(b => b.bill_id == billId);
    if (bill && bill.items && bill.items.length) {
      currentItems = bill.items.map(item => ({
        item_name: item.item_name,
        quantity: item.quantity,
        price: item.price,
        gst: item.gst || DEFAULT_GST
      }));
      renderTable();
      refreshSummary(billId);
      setStatus(`Bill #${billId} loaded to grid`, 'success');
    }
  } catch (e) {
    setStatus('Could not load bill details', 'error');
  }
}

// ── Refresh billing history ────────────────
document.getElementById('refreshBillingHistoryBtn').addEventListener('click', () => {
  setStatus('Loading recent bills...', 'warn');
  loadBillingHistory().then(() => {
    setStatus('Recent bills loaded', 'success');
  }).catch(() => {
    setStatus('Could not load recent bills', 'error');
  });
});

// ── Load reports ──────────────────────────
document.getElementById('loadReportsBtn').addEventListener('click', async () => {
  setStatus('Loading reports...', 'warn');
  try {
    const data = await apiCall('/reports');
    document.getElementById('todayRevenue').textContent = money(data.today_revenue);
    document.getElementById('monthBills').textContent = String(data.month_bills);
    document.getElementById('avgBillValue').textContent = money(data.avg_bill_value);
    document.getElementById('topItem').textContent = data.top_item;
    setStatus('Reports loaded', 'success');
  } catch (e) {
    setStatus(e.message || 'Could not load reports', 'error');
  }
});

// ── Settings – API ────────────────────────
document.getElementById('saveApiBtn').addEventListener('click', () => {
  API_BASE = document.getElementById('apiBaseInput').value.trim() || API_BASE;
  document.getElementById('apiSaveMsg').textContent = 'API settings saved for this session.';
  document.getElementById('apiSaveMsg').style.color = 'var(--success)';
  setStatus('API settings updated', 'success');
});

document.getElementById('testApiBtn').addEventListener('click', async () => {
  setStatus('Testing connection...', 'warn');
  try {
    await apiCall('/health');
    setStatus('Connection successful!', 'success');
    document.getElementById('apiSaveMsg').textContent = 'Connection OK!';
    document.getElementById('apiSaveMsg').style.color = 'var(--success)';
  } catch (e) {
    setStatus('Connection failed', 'error');
    document.getElementById('apiSaveMsg').textContent = `Failed: ${e.message}`;
    document.getElementById('apiSaveMsg').style.color = 'var(--danger)';
  }
});

// ── Settings – Preferences ────────────────
document.getElementById('savePrefBtn').addEventListener('click', () => {
  DEFAULT_GST = Number(document.getElementById('defaultGstInput').value) || 18;
  CURRENCY    = document.getElementById('currencyInput').value || '₹';
  document.getElementById('prefSaveMsg').textContent = 'Preferences saved for this session.';
  document.getElementById('prefSaveMsg').style.color = 'var(--success)';
  setStatus('Preferences updated', 'success');
  renderTable();
});

// ── Feature toggles ───────────────────────
document.querySelectorAll('.toggle').forEach(toggle => {
  toggle.addEventListener('click', () => {
    toggle.classList.toggle('on');
  });
});

// ── Login ─────────────────────────────────
  document.getElementById('loginBtn').addEventListener('click', async (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    if (!email || !password) {
      document.getElementById('loginMsg').textContent = 'Please fill all fields';
      document.getElementById('loginMsg').style.color = 'var(--danger)';
      return;
    }
    document.getElementById('loginMsg').textContent = 'Signing in...';
    document.getElementById('loginMsg').style.color = 'var(--muted)';
    try {
      const data = await apiCall('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
      if (!data.shop) throw new Error(data.message || 'Sign in failed');
      currentShop = data.shop;
      isLoggedIn = true;
      saveLoginState();
      updateTabVisibility();
      document.getElementById('loginMsg').textContent = `Welcome, ${data.shop.shop_name}!`;
      document.getElementById('loginMsg').style.color = 'var(--success)';
      setStatus(`Signed in as ${data.shop.shop_name}`, 'success');
      // Clear form
      document.getElementById('loginEmail').value = '';
      document.getElementById('loginPassword').value = '';
      setActivePage('billing');
    } catch (e) {
      document.getElementById('loginMsg').textContent = e.message || 'Sign in failed';
      document.getElementById('loginMsg').style.color = 'var(--danger)';
    }
});

// ── Register ──────────────────────────────
  document.getElementById('registerBtn').addEventListener('click', async (e) => {
    e.preventDefault();
    const shop_name = document.getElementById('regShopName').value.trim();
    const owner_name = document.getElementById('regOwnerName').value.trim();
    const mobile = document.getElementById('regMobile').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value.trim();
    const business_type = document.getElementById('regBusinessType').value;

    if (!shop_name || !owner_name || !email || !password) {
      document.getElementById('registerMsg').textContent = 'Please fill required fields';
      document.getElementById('registerMsg').style.color = 'var(--danger)';
      return;
    }
    document.getElementById('registerMsg').textContent = 'Signing up...';
    document.getElementById('registerMsg').style.color = 'var(--muted)';
    try {
      const dob = document.getElementById('regDob').value.trim();
      const data = await apiCall('/register', {
        method: 'POST',
        body: JSON.stringify({
          shop_name,
          owner_name,
          dob: dob || null,
          mobile: mobile || null,
          email,
          password,
          business_type,
          modules: ["billing", "inventory"],
          ai_enabled: true,
          inventory_enabled: true
        })
      });
      document.getElementById('registerMsg').textContent = `Shop signed up! Shop ID: ${data.shop_id}`;
      document.getElementById('registerMsg').style.color = 'var(--success)';
      setStatus('Sign up successful! Please sign in.', 'success');
      // Clear form
      document.getElementById('regShopName').value = '';
      document.getElementById('regOwnerName').value = '';
      document.getElementById('regDob').value = '';
      document.getElementById('regMobile').value = '';
      document.getElementById('regEmail').value = '';
      document.getElementById('regPassword').value = '';
    setActivePage('login');
  } catch (e) {
    document.getElementById('registerMsg').textContent = e.message || 'Sign up failed';
    document.getElementById('registerMsg').style.color = 'var(--danger)';
  }
});

// ── Logout ────────────────────────────────
  document.getElementById('logoutBtn').addEventListener('click', (e) => {
    e.preventDefault();
    clearLoginState();
    currentItems = [];
    document.getElementById('loginEmail').value = '';
    document.getElementById('loginPassword').value = '';
  renderTable();
  setStatus('Signed out successfully', 'info');
  // Switch to login tab
  setActivePage('login');
});

// ── Init ──────────────────────────────────
updateTabVisibility();
setActivePage('billing'); // Default to billing page on startup
renderTable();
if (isLoggedIn) {
  loadBillingHistory(); // Load recent bills on startup if logged in
}

// Show auto-detected API URL in settings
document.getElementById('apiBaseInput').value = API_BASE;
document.getElementById('detectedApiUrl').textContent = API_BASE;

// Auto-check backend connection on startup
(async function checkBackendOnLoad() {
  setStatus('Checking backend...', 'warn');
  try {
    await apiCall('/health');
    setStatus('Backend connected', 'success');
  } catch (e) {
    setStatus('Backend offline - run start.bat', 'error');
  }
})();
