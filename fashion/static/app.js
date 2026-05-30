// Service Worker registration (PWA)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
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

// ---------- Profile ----------
async function loadProfile() {
  const res = await fetch('/api/profile');
  const p = await res.json();
  if (p.age) document.getElementById('age').value = p.age;
  if (p.height) document.getElementById('height').value = p.height;
  if (p.weight) document.getElementById('weight').value = p.weight;
  if (p.body_note) document.getElementById('body-note').value = p.body_note;
  const bRadio = document.querySelector(`input[name="budget"][value="${p.budget || 'high'}"]`);
  if (bRadio) bRadio.checked = true;
  const fRadio = document.querySelector(`input[name="family"][value="${p.family || 'children_small'}"]`);
  if (fRadio) fRadio.checked = true;
}

document.getElementById('profile-form').addEventListener('submit', async e => {
  e.preventDefault();
  const data = {
    age: document.getElementById('age').value,
    height: document.getElementById('height').value,
    weight: document.getElementById('weight').value,
    budget: document.querySelector('input[name="budget"]:checked')?.value || 'high',
    family: document.querySelector('input[name="family"]:checked')?.value || 'children_small',
    body_note: document.getElementById('body-note').value.trim(),
  };
  await fetch('/api/profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const msg = document.getElementById('profile-saved');
  msg.classList.remove('hidden');
  setTimeout(() => msg.classList.add('hidden'), 2500);
});

// ---------- Wardrobe ----------
let items = [];

async function loadWardrobe() {
  const res = await fetch('/api/wardrobe');
  const data = await res.json();
  items = data.items || [];
  renderWardrobe();
}

function esc(str) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(str || ''));
  return d.innerHTML;
}

function renderWardrobe() {
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
      items.splice(Number(btn.dataset.i), 1);
      saveWardrobe();
      renderWardrobe();
    });
  });
}

async function saveWardrobe() {
  await fetch('/api/wardrobe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items }),
  });
}

document.getElementById('add-item-form').addEventListener('submit', e => {
  e.preventDefault();
  const name = document.getElementById('item-name').value.trim();
  if (!name) return;
  items.push({
    name,
    category: document.getElementById('item-category').value,
    color: document.getElementById('item-color').value.trim(),
  });
  saveWardrobe();
  renderWardrobe();
  document.getElementById('item-name').value = '';
  document.getElementById('item-color').value = '';
  document.getElementById('item-name').focus();
});

// ---------- Recommend ----------
let selectedSeason = 'spring';

document.querySelectorAll('.season-btn').forEach(btn => {
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

  try {
    const res = await fetch('/api/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ season: selectedSeason }),
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
loadWardrobe();
