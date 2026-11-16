// Клиентская логика Keitaro Manager с быстрым кэшем и удобным поиском

let allOffers = [];
let currentCampaignId = null;
let currentEditorState = null;

// Инициализация при загрузке страницы
document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([loadOffersDictionary(), loadCampaignsList()]);
});

// Переключение табов
function switchTab(tabName) {
  const createTab = document.getElementById("tab-create");
  const editTab = document.getElementById("tab-edit");
  const createBtn = document.getElementById("tab-create-btn");
  const editBtn = document.getElementById("tab-edit-btn");

  if (tabName === "create") {
    createTab.classList.remove("hidden");
    editTab.classList.add("hidden");
    createBtn.className = "px-3.5 py-1.5 text-xs font-semibold rounded-md transition-all bg-white text-slate-900 shadow-sm flex items-center gap-1.5";
    editBtn.className = "px-3.5 py-1.5 text-xs font-medium rounded-md transition-all text-slate-600 hover:text-slate-900 flex items-center gap-1.5";
  } else {
    createTab.classList.add("hidden");
    editTab.classList.remove("hidden");
    editBtn.className = "px-3.5 py-1.5 text-xs font-semibold rounded-md transition-all bg-white text-slate-900 shadow-sm flex items-center gap-1.5";
    createBtn.className = "px-3.5 py-1.5 text-xs font-medium rounded-md transition-all text-slate-600 hover:text-slate-900 flex items-center gap-1.5";
  }
}

// Загрузка словаря офферов (с кэшированием в localStorage)
async function loadOffersDictionary() {
  const cached = localStorage.getItem("keitaro_offers_cache");
  if (cached) {
    try {
      allOffers = JSON.parse(cached);
    } catch (e) {}
  }
  try {
    const res = await fetch("/api/dictionaries/offers");
    allOffers = await res.json();
    localStorage.setItem("keitaro_offers_cache", JSON.stringify(allOffers));
  } catch (err) {
    if (!allOffers.length) showToast("Не удалось загрузить офферы", "error");
  }
}

// Поиск офферов с выпадающим автокомплитом
function handleOfferSearch(query) {
  const dropdown = document.getElementById("offer-search-dropdown");
  const q = query.trim().toLowerCase();
  if (!q) {
    dropdown.classList.add("hidden");
    return;
  }
  const matches = allOffers.filter(o => 
    String(o.value).includes(q) || (o.name && o.name.toLowerCase().includes(q))
  ).slice(0, 15);

  if (matches.length === 0) {
    dropdown.innerHTML = `<div class="p-3 text-slate-400 text-center">Офферы не найдены</div>`;
  } else {
    dropdown.innerHTML = matches.map(o => `
      <div onclick="selectOfferFromSearch(${o.value}, '${escapeHtml(o.name)}')" class="px-3 py-2 hover:bg-slate-50 cursor-pointer border-b border-slate-100 flex items-center justify-between">
        <span class="font-medium text-slate-800">${escapeHtml(o.name)}</span>
        <span class="font-mono text-slate-400 text-[11px] ml-2">ID ${o.value}</span>
      </div>
    `).join("");
  }
  dropdown.classList.remove("hidden");
}

function selectOfferFromSearch(offerId, offerName) {
  document.getElementById("campaign-offer-id").value = offerId;
  document.getElementById("offer-search-input").value = `[ID ${offerId}] ${offerName}`;
  document.getElementById("offer-search-dropdown").classList.add("hidden");
}

function escapeHtml(text) {
  return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Загрузка списка кампаний
async function loadCampaignsList(force = false) {
  try {
    const res = await fetch("/api/campaigns");
    const campaigns = await res.json();
    const select = document.getElementById("campaigns-select");

    let html = '<option value="">-- Выберите кампанию --</option>';
    campaigns.forEach(c => {
      const id = c.value || c.id;
      const name = c.name || `Кампания #${id}`;
      html += `<option value="${id}">[ID ${id}] ${name}</option>`;
    });
    select.innerHTML = html;
  } catch (err) {
    showToast("Ошибка при загрузке списка кампаний", "error");
  }
}

// Создание кампании
async function handleCreateCampaign(e) {
  e.preventDefault();
  const submitBtn = document.getElementById("submit-create-btn");
  const rawName = document.getElementById("campaign-name").value.trim();
  const geo = document.getElementById("campaign-geo").value.trim().toUpperCase();
  const offerId = parseInt(document.getElementById("campaign-offer-id").value, 10);

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Создание...';

  try {
    const res = await fetch("/api/campaigns", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: rawName, geo_country: geo, offer_id: offerId })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data, "error");
      return;
    }

    showToast(`Кампания "${data.name}" создана!`, "success");
    displayCreateResult(data);
    await loadCampaignsList(true);
    document.getElementById("campaign-name").value = "";
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Создать кампанию';
  }
}

function displayCreateResult(data) {
  const resultDiv = document.getElementById("create-result");
  resultDiv.innerHTML = `
    <div class="flex items-center justify-between">
      <div>
        <p class="font-semibold text-emerald-800 text-sm">Кампания успешно создана в Keitaro</p>
        <p class="text-slate-600 mt-0.5">ID: <span class="font-mono font-bold">${data.campaign_id}</span> | Название: <span class="font-mono">${data.name}</span></p>
      </div>
      <button onclick="goToCampaignInEditor(${data.campaign_id})" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg text-xs transition-colors">
        Открыть в редакторе
      </button>
    </div>
  `;
  resultDiv.classList.remove("hidden");
}

function goToCampaignInEditor(campaignId) {
  switchTab("edit");
  const select = document.getElementById("campaigns-select");
  select.value = campaignId;
  loadCampaignDetail(campaignId);
}

// Загрузка деталей кампании
async function loadCampaignDetail(campaignId) {
  if (!campaignId) {
    document.getElementById("campaign-editor-panel").classList.add("hidden");
    return;
  }
  currentCampaignId = campaignId;

  try {
    const res = await fetch(`/api/campaigns/${campaignId}/editor`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Не удалось загрузить данные");
    currentEditorState = data;
    renderEditorStreams(data);
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Fetch Streams
async function handleFetchStreams() {
  if (!currentCampaignId) {
    showToast("Выберите кампанию", "error");
    return;
  }
  const btn = document.getElementById("fetch-streams-btn");
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Синхронизация...';

  try {
    const res = await fetch(`/api/campaigns/${currentCampaignId}/fetch_streams`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ошибка синхронизации");

    currentEditorState = data;
    renderEditorStreams(data);
    showToast("Потоки синхронизированы с Keitaro", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-down text-slate-500"></i> Синхронизировать (Fetch)';
  }
}

// Отрисовка потоков кампании
function renderEditorStreams(state) {
  const container = document.getElementById("streams-container");
  container.innerHTML = "";

  (state.streams || []).forEach(st => {
    const streamCard = document.createElement("div");

    if (st.has_offers) {
      const isDirty = state.is_dirty;
      streamCard.className = `border rounded-xl p-5 sm:p-6 transition-all ${
        isDirty ? "stream-draft-active" : "bg-white border-slate-200 shadow-sm"
      }`;

      streamCard.innerHTML = `
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-5 border-b border-slate-100 pb-4">
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-semibold text-slate-900">${st.name}</h3>
              ${isDirty 
                ? '<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">Есть несохранённые изменения</span>'
                : '<span class="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600">Синхронизировано</span>'}
            </div>
            <p class="text-[11px] text-slate-500 mt-0.5">Stream #${st.id} — распределение трафика по офферам</p>
          </div>

          <div class="flex items-center gap-2">
            ${isDirty ? `
              <button onclick="handleCancelChanges()" class="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium transition-colors">
                Отменить (Cancel)
              </button>
              <button onclick="handlePushToKeitaro()" class="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5">
                <i class="fa-solid fa-arrow-up-from-bracket"></i> Push to Keitaro
              </button>
            ` : ''}
          </div>
        </div>

        <!-- Добавление оффера в поток через умный селектор -->
        <div class="bg-slate-50 border border-slate-200/80 rounded-lg p-3 mb-5 flex flex-col sm:flex-row items-center gap-2">
          <div class="flex-1 w-full relative">
            <input type="text" id="stream-offer-search" oninput="handleStreamOfferSearch(this.value)" placeholder="Поиск оффера по названию или ID..." class="w-full rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-slate-800 bg-white">
            <input type="hidden" id="selected-stream-offer-id">
            <div id="stream-offer-dropdown" class="hidden absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-md shadow-lg max-h-48 overflow-y-auto z-50 text-xs"></div>
          </div>
          <button onclick="handleAddOfferToDraft()" class="w-full sm:w-auto px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-xs font-medium transition-colors flex items-center justify-center gap-1.5 whitespace-nowrap">
            Добавить
          </button>
        </div>

        <!-- Таблица офферов -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th class="py-2.5 px-3">ID</th>
                <th class="py-2.5 px-3">Название оффера</th>
                <th class="py-2.5 px-3 text-center">Доля (Share)</th>
                <th class="py-2.5 px-3 text-center">Фиксация (Pin)</th>
                <th class="py-2.5 px-3 text-center">Статус</th>
                <th class="py-2.5 px-3 text-right">Действие</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 text-slate-700">
              ${renderOffersRows(state.offers || [])}
            </tbody>
          </table>
        </div>
      `;
    } else {
      // Поток Google
      streamCard.className = "bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center justify-between";
      streamCard.innerHTML = `
        <div class="flex items-center gap-3">
          <div class="w-7 h-7 rounded-md bg-slate-100 text-slate-600 flex items-center justify-center text-xs font-bold">
            G
          </div>
          <div>
            <h4 class="font-medium text-slate-900 text-xs">${st.name}</h4>
            <p class="text-[11px] text-slate-500">Служебный поток фильтрации страны</p>
          </div>
        </div>
        <span class="text-[11px] font-mono text-slate-400">Stream #${st.id}</span>
      `;
    }

    container.appendChild(streamCard);
  });

  document.getElementById("campaign-editor-panel").classList.remove("hidden");
}

function handleStreamOfferSearch(query) {
  const dropdown = document.getElementById("stream-offer-dropdown");
  const q = query.trim().toLowerCase();
  if (!q) {
    dropdown.classList.add("hidden");
    return;
  }
  const matches = allOffers.filter(o => 
    String(o.value).includes(q) || (o.name && o.name.toLowerCase().includes(q))
  ).slice(0, 10);

  if (matches.length === 0) {
    dropdown.innerHTML = `<div class="p-2 text-slate-400 text-center">Офферы не найдены</div>`;
  } else {
    dropdown.innerHTML = matches.map(o => `
      <div onclick="selectStreamOfferFromSearch(${o.value}, '${escapeHtml(o.name)}')" class="px-3 py-1.5 hover:bg-slate-50 cursor-pointer border-b border-slate-100 flex items-center justify-between">
        <span class="font-medium text-slate-800">${escapeHtml(o.name)}</span>
        <span class="font-mono text-slate-400 text-[10px] ml-2">ID ${o.value}</span>
      </div>
    `).join("");
  }
  dropdown.classList.remove("hidden");
}

function selectStreamOfferFromSearch(offerId, offerName) {
  document.getElementById("selected-stream-offer-id").value = offerId;
  document.getElementById("stream-offer-search").value = `[ID ${offerId}] ${offerName}`;
  document.getElementById("stream-offer-dropdown").classList.add("hidden");
}

// Строки таблицы офферов
function renderOffersRows(offers) {
  if (offers.length === 0) {
    return `<tr><td colspan="6" class="py-5 text-center text-slate-400">В потоке пока нет офферов</td></tr>`;
  }

  return offers.map(o => {
    const isRemoved = o.status === "removed" || o.status === "pending_del";
    const rowClass = isRemoved ? "row-removed text-slate-400" : "hover:bg-slate-50/60";

    return `
      <tr class="${rowClass} transition-colors">
        <td class="py-2.5 px-3 font-mono font-medium">${o.offer_id}</td>
        <td class="py-2.5 px-3 font-medium">${escapeHtml(o.name)}</td>
        <td class="py-2.5 px-3 text-center">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold ${
            isRemoved ? 'bg-slate-100 text-slate-400' : (o.is_pinned ? 'bg-amber-100 text-amber-900 border border-amber-300' : 'bg-slate-100 text-slate-800')
          }">
            ${o.share}%
          </span>
        </td>
        <td class="py-2.5 px-3 text-center">
          ${isRemoved ? '-' : `
            <button onclick="handleTogglePin(${o.offer_id}, ${!o.is_pinned})" title="${o.is_pinned ? 'Открепить долю' : 'Зафиксировать долю'}" class="p-1 rounded text-xs transition-colors ${
              o.is_pinned ? 'text-amber-600 bg-amber-50 hover:bg-amber-100' : 'text-slate-400 hover:text-slate-600'
            }">
              <i class="fa-solid fa-thumbtack ${o.is_pinned ? 'rotate-45' : ''}"></i>
            </button>
          `}
        </td>
        <td class="py-2.5 px-3 text-center">
          ${isRemoved 
            ? '<span class="text-[10px] text-rose-600 font-medium">удалён</span>'
            : (!o.is_published 
              ? '<span class="text-[10px] text-amber-600 font-medium">черновик</span>'
              : '<span class="text-[10px] text-emerald-600 font-medium">активен</span>')}
        </td>
        <td class="py-2.5 px-3 text-right">
          ${isRemoved ? `
            <button onclick="handleBringBackOffer(${o.offer_id})" class="px-2.5 py-1 bg-white border border-emerald-300 hover:bg-emerald-50 text-emerald-700 rounded text-xs font-medium transition-colors ml-auto">
              Восстановить
            </button>
          ` : `
            <button onclick="handleRemoveOfferDraft(${o.offer_id})" class="px-2.5 py-1 bg-white border border-slate-200 hover:bg-rose-50 hover:border-rose-200 text-slate-600 hover:text-rose-600 rounded text-xs font-medium transition-colors ml-auto">
              Удалить
            </button>
          `}
        </td>
      </tr>
    `;
  }).join("");
}

// Добавление оффера
async function handleAddOfferToDraft() {
  const hiddenInput = document.getElementById("selected-stream-offer-id");
  const offerId = parseInt(hiddenInput.value, 10);
  if (!offerId || !currentCampaignId) {
    showToast("Выберите оффер из списка", "error");
    return;
  }
  const match = allOffers.find(o => o.value === offerId);
  const offerName = match ? match.name : `Offer #${offerId}`;

  try {
    const res = await fetch(`/api/campaigns/${currentCampaignId}/draft_offer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ offer_id: offerId, offer_name: offerName })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ошибка добавления");

    currentEditorState = data;
    renderEditorStreams(data);
    hiddenInput.value = "";
    document.getElementById("stream-offer-search").value = "";
    showToast(`Оффер #${offerId} добавлен в поток`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Удаление оффера (пометка на удаление)
async function handleRemoveOfferDraft(offerId) {
  try {
    const res = await fetch(`/api/campaigns/${currentCampaignId}/remove_offer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ offer_id: offerId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ошибка удаления");

    currentEditorState = data;
    renderEditorStreams(data);
    showToast(`Оффер #${offerId} помечен на удаление (нажмите Push to Keitaro)`, "info");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Восстановление оффера
async function handleBringBackOffer(offerId) {
  try {
    const res = await fetch(`/api/campaigns/${currentCampaignId}/bring_back_offer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ offer_id: offerId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ошибка возврата");

    currentEditorState = data;
    renderEditorStreams(data);
    showToast(`Оффер #${offerId} восстановлен`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Переключение Pin
async function handleTogglePin(offerId, isPinned) {
  try {
    const res = await fetch(`/api/campaigns/${currentCampaignId}/pin_offer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ offer_id: offerId, is_pinned: isPinned })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ошибка Pin");

    currentEditorState = data;
    renderEditorStreams(data);
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Отмена
async function handleCancelChanges() {
  try {
    const res = await fetch(`/api/campaigns/${currentCampaignId}/cancel`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ошибка отмены");

    currentEditorState = data;
    renderEditorStreams(data);
    showToast("Изменения отменены", "info");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Push to Keitaro
async function handlePushToKeitaro() {
  try {
    const res = await fetch(`/api/campaigns/${currentCampaignId}/push`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ошибка публикации");

    currentEditorState = data;
    renderEditorStreams(data);
    showToast("✅ Опубликовано в Keitaro", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Уведомления
function showToast(message, type = "info") {
  const toast = document.getElementById("toast");
  const icon = document.getElementById("toast-icon");
  const text = document.getElementById("toast-text");

  let displayMsg = message;
  if (typeof message === "object" && message !== null) {
    if (Array.isArray(message.detail)) {
      displayMsg = message.detail.map(d => d.msg || JSON.stringify(d)).join(", ");
    } else if (typeof message.detail === "string") {
      displayMsg = message.detail;
    } else {
      displayMsg = message.message || JSON.stringify(message);
    }
  }

  text.innerText = displayMsg;
  if (type === "success") {
    icon.innerHTML = '<i class="fa-solid fa-check text-emerald-600"></i>';
    toast.className = "fixed bottom-5 right-5 z-50 transform transition-all duration-200 translate-y-0 opacity-100 max-w-sm bg-white border border-emerald-200 rounded-lg p-3.5 shadow-lg flex items-center gap-3";
  } else if (type === "error") {
    icon.innerHTML = '<i class="fa-solid fa-triangle-exclamation text-rose-600"></i>';
    toast.className = "fixed bottom-5 right-5 z-50 transform transition-all duration-200 translate-y-0 opacity-100 max-w-sm bg-white border border-rose-200 rounded-lg p-3.5 shadow-lg flex items-center gap-3";
  } else {
    icon.innerHTML = '<i class="fa-solid fa-info text-blue-600"></i>';
    toast.className = "fixed bottom-5 right-5 z-50 transform transition-all duration-200 translate-y-0 opacity-100 max-w-sm bg-white border border-slate-200 rounded-lg p-3.5 shadow-lg flex items-center gap-3";
  }

  setTimeout(() => {
    toast.classList.add("translate-y-16", "opacity-0");
  }, 4000);
}
