// Service Worker registration (PWA)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}

// ---------- Current season detection ----------
function currentSeason() {
  const m = new Date().getMonth() + 1;
  if (m >= 3 && m <= 5) return 'spring';
  if (m >= 6 && m <= 8) return 'summer';
  if (m >= 9 && m <= 11) return 'autumn';
  return 'winter';
}

// ---------- Tab switching ----------
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  });
});

// ---------- Profile (localStorage) ----------
const DEFAULT_PROFILE = {
  age: '38', height: '178', weight: '80',
  budget: 'high', family: 'children_small',
  body_note: 'スポーツ体型で太ももが太め。市販のパンツは太もも周りがきつくなりやすい。',
};

function loadProfile() {
  const stored = localStorage.getItem('wc_profile');
  const p = stored ? JSON.parse(stored) : DEFAULT_PROFILE;
  document.getElementById('age').value = p.age || '';
  document.getElementById('height').value = p.height || '';
  document.getElementById('weight').value = p.weight || '';
  document.getElementById('body-note').value = p.body_note || '';
  const bRadio = document.querySelector(`input[name="budget"][value="${p.budget || 'high'}"]`);
  if (bRadio) bRadio.checked = true;
  const fRadio = document.querySelector(`input[name="family"][value="${p.family || 'children_small'}"]`);
  if (fRadio) fRadio.checked = true;
}

function getProfileFromForm() {
  return {
    age: document.getElementById('age').value,
    height: document.getElementById('height').value,
    weight: document.getElementById('weight').value,
    budget: document.querySelector('input[name="budget"]:checked')?.value || 'high',
    family: document.querySelector('input[name="family"]:checked')?.value || 'children_small',
    body_note: document.getElementById('body-note').value.trim(),
  };
}

document.getElementById('profile-form').addEventListener('submit', e => {
  e.preventDefault();
  const data = getProfileFromForm();
  localStorage.setItem('wc_profile', JSON.stringify(data));
  const msg = document.getElementById('profile-saved');
  msg.classList.remove('hidden');
  setTimeout(() => msg.classList.add('hidden'), 2500);
});

// ---------- Wardrobe (localStorage) ----------
function loadItems() {
  const stored = localStorage.getItem('wc_wardrobe');
  return stored ? JSON.parse(stored) : [];
}

function saveItems(arr) {
  localStorage.setItem('wc_wardrobe', JSON.stringify(arr));
}

function esc(str) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(str || ''));
  return d.innerHTML;
}

function renderWardrobe() {
  const items = loadItems();
  const list = document.getElementById('wardrobe-list');
  if (items.length === 0) {
    list.innerHTML = '<div class="empty-state">まだアイテムが登録されていません</div>';
    return;
  }
  list.innerHTML = items.map((item, i) => `
    <div class="wardrobe-item">
      <div class="wardrobe-item-left">
        <div class="wardrobe-item-name">${esc(item.name)}</div>
        <div class="wardrobe-item-tags">
          <span class="tag">${esc(item.category || 'その他')}</span>
          ${item.color ? `<span class="tag">${esc(item.color)}</span>` : ''}
        </div>
      </div>
      <button class="btn-del" data-i="${i}" title="削除">&times;</button>
    </div>
  `).join('');

  list.querySelectorAll('.btn-del').forEach(btn => {
    btn.addEventListener('click', () => {
      const arr = loadItems();
      arr.splice(Number(btn.dataset.i), 1);
      saveItems(arr);
      renderWardrobe();
    });
  });
}

document.getElementById('add-item-form').addEventListener('submit', e => {
  e.preventDefault();
  const name = document.getElementById('item-name').value.trim();
  if (!name) return;
  const arr = loadItems();
  arr.push({
    name,
    category: document.getElementById('item-category').value,
    color: document.getElementById('item-color').value.trim(),
  });
  saveItems(arr);
  renderWardrobe();
  document.getElementById('item-name').value = '';
  document.getElementById('item-color').value = '';
  document.getElementById('item-name').focus();
});

// ---------- Recommend ----------
let selectedSeason = currentSeason();

document.querySelectorAll('.season-btn').forEach(btn => {
  const isCurrent = btn.dataset.season === selectedSeason;
  btn.classList.toggle('active', isCurrent);
  if (isCurrent) {
    const badge = document.createElement('span');
    badge.className = 'season-now';
    badge.textContent = '今';
    btn.appendChild(badge);
  }
  btn.addEventListener('click', () => {
    document.querySelectorAll('.season-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedSeason = btn.dataset.season;
  });
});

document.getElementById('recommend-btn').addEventListener('click', async () => {
  const btn = document.getElementById('recommend-btn');
  const loading = document.getElementById('recommend-loading');
  const output = document.getElementById('recommend-output');
  const content = document.getElementById('recommend-content');

  btn.disabled = true;
  loading.classList.remove('hidden');
  output.classList.add('hidden');
  content.innerHTML = '';

  // プロフィールと手持ちをリクエストに含める（サーバー再起動後もデータが使われる）
  const stored = localStorage.getItem('wc_profile');
  const profile = stored ? JSON.parse(stored) : DEFAULT_PROFILE;
  const wardrobeItems = loadItems();

  try {
    const res = await fetch('/api/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ season: selectedSeason, profile, wardrobe_items: wardrobeItems }),
    });

    if (!res.ok) throw new Error('API error');

    loading.classList.add('hidden');
    output.classList.remove('hidden');

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6);
        if (payload === '[DONE]') continue;
        try {
          const { text } = JSON.parse(payload);
          fullText += text;
          content.innerHTML = marked.parse(fullText);
        } catch (_) {}
      }
    }
  } catch (err) {
    loading.classList.add('hidden');
    output.classList.remove('hidden');
    content.innerHTML = '<p class="error-msg">エラーが発生しました。しばらく経ってから再度お試しください。</p>';
    console.error(err);
  } finally {
    btn.disabled = false;
  }
});

// ---------- Init ----------
loadProfile();
renderWardrobe();
