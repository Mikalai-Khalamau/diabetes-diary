const API_BASE = '/api';
const TOKEN_KEY = 'diabetes_token';

let foodsCache = [];

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}
function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}
function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

async function parseError(response) {
    try {
        const data = await response.json();
        if (data && data.detail) {
            return Array.isArray(data.detail) ? data.detail[0].msg : data.detail;
        }
        return `Ошибка сервера (${response.status})`;
    } catch (e) {
        return `Ошибка сервера (${response.status})`;
    }
}

async function apiFetch(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token = getToken();
    if (token) headers['Authorization'] = 'Bearer ' + token;
    if (options.body !== undefined && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }
    const response = await fetch(path, { ...options, headers });
    if (response.status === 401) {
        clearToken();
        showAuthScreen('Сессия истекла. Войдите снова.');
        throw new Error('Не авторизован');
    }
    return response;
}

function showAuthScreen(message) {
    document.getElementById('app-screen').classList.add('hidden');
    const authScreen = document.getElementById('auth-screen');
    authScreen.classList.remove('hidden');
    const msgEl = document.getElementById('auth-message');
    if (message) {
        msgEl.textContent = message;
        msgEl.classList.remove('hidden');
    } else {
        msgEl.classList.add('hidden');
    }
}

function showAppScreen() {
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
}

function switchAuthTab(mode) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const msgEl = document.getElementById('auth-message');
    msgEl.classList.add('hidden');

    if (mode === 'login') {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
    } else {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        tabLogin.classList.remove('active');
        tabRegister.classList.add('active');
    }
}

async function doLogin(email, password) {
    const response = await fetch(`${API_BASE}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
        throw new Error(await parseError(response));
    }
    const data = await response.json();
    setToken(data.access_token);
}

async function enterApp() {
    const meResp = await apiFetch(`${API_BASE}/auth/me/`);
    if (!meResp.ok) throw new Error(await parseError(meResp));
    const user = await meResp.json();
    document.getElementById('current-user-email').textContent = user.email;
    showAppScreen();
    await Promise.all([loadFoods(), loadRecentEvents(), loadRecentStats()]);
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('tab-login').addEventListener('click', () => switchAuthTab('login'));
    document.getElementById('tab-register').addEventListener('click', () => switchAuthTab('register'));
    document.getElementById('logout-btn').addEventListener('click', () => {
        clearToken();
        showAuthScreen();
    });

    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        try {
            await doLogin(email, password);
            await enterApp();
        } catch (err) {
            showAuthScreen(err.message);
        }
    });

    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        try {
            const response = await fetch(`${API_BASE}/auth/register/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            await doLogin(email, password);
            await enterApp();
        } catch (err) {
            showAuthScreen(err.message);
        }
    });

    document.getElementById('glucose-form').addEventListener('submit', handleGlucoseSubmit);
    document.getElementById('insulin-form').addEventListener('submit', handleInsulinSubmit);
    document.getElementById('meal-form').addEventListener('submit', handleMealSubmit);
    document.getElementById('food-form').addEventListener('submit', handleFoodSubmit);

    if (getToken()) {
        enterApp().catch(() => {});
    } else {
        showAuthScreen();
    }
});

async function loadFoods() {
    try {
        const response = await apiFetch(`${API_BASE}/foods/`);
        if (!response.ok) throw new Error(await parseError(response));
        foodsCache = await response.json();
        if (!Array.isArray(foodsCache)) foodsCache = [];
        renderFoodsList();
        updateFoodDatalist();
    } catch (error) {
        console.error('Ошибка загрузки продуктов:', error);
    }
}

async function loadRecentEvents() {
    try {
        const response = await apiFetch(`${API_BASE}/events/recent?t=${Date.now()}`);
        if (!response.ok) throw new Error(await parseError(response));
        renderEvents(await response.json());
    } catch (error) {
        console.error('Ошибка загрузки событий:', error);
    }
}

async function loadRecentStats() {
    try {
        const response = await apiFetch(`${API_BASE}/stats/recent?t=${Date.now()}`);
        if (!response.ok) throw new Error(await parseError(response));
        renderStats(await response.json());
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

async function handleGlucoseSubmit(event) {
    event.preventDefault();
    const value = parseFloat(document.getElementById('glucose-value').value);
    try {
        const response = await apiFetch(`${API_BASE}/glucose-events/`, {
            method: 'POST',
            body: JSON.stringify({ value }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        document.getElementById('glucose-form').reset();
        await loadRecentEvents();
        await loadRecentStats();
    } catch (error) {
        if (error.message !== 'Не авторизован') alert('Ошибка: ' + error.message);
    }
}

async function handleInsulinSubmit(event) {
    event.preventDefault();
    const insulin_type = document.getElementById('insulin-type').value;
    const dose = parseFloat(document.getElementById('insulin-dose').value);
    try {
        const response = await apiFetch(`${API_BASE}/insulin-events/`, {
            method: 'POST',
            body: JSON.stringify({ insulin_type, dose }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        document.getElementById('insulin-form').reset();
        await loadRecentEvents();
        await loadRecentStats();
    } catch (error) {
        if (error.message !== 'Не авторизован') alert('Ошибка: ' + error.message);
    }
}

async function handleMealSubmit(event) {
    event.preventDefault();
    const foodNameInput = document.getElementById('meal-food-name');
    const gramsInput = document.getElementById('meal-grams');
    const foodName = foodNameInput.value.trim();
    const grams = parseFloat(gramsInput.value);
    const food = foodsCache.find(f => f.name.toLowerCase() === foodName.toLowerCase());
    if (!food) {
        alert('Продукт не найден в справочнике.');
        return;
    }
    try {
        const response = await apiFetch(`${API_BASE}/meal-events/`, {
            method: 'POST',
            body: JSON.stringify({ food_id: food.id, grams }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        foodNameInput.value = '';
        gramsInput.value = '';
        await loadRecentEvents();
        await loadRecentStats();
    } catch (error) {
        if (error.message !== 'Не авторизован') alert('Ошибка: ' + error.message);
    }
}

async function handleFoodSubmit(event) {
    event.preventDefault();
    const name = document.getElementById('food-name').value;
    const carbs_per_100g = parseFloat(document.getElementById('food-carbs').value);
    try {
        const response = await apiFetch(`${API_BASE}/foods/`, {
            method: 'POST',
            body: JSON.stringify({ name, carbs_per_100g }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        document.getElementById('food-form').reset();
        await loadFoods();
    } catch (error) {
        if (error.message !== 'Не авторизован') alert('Ошибка: ' + error.message);
    }
}

async function deleteEvent(eventType, eventId) {
    if (!confirm('Удалить это событие?')) return;
    try {
        const response = await apiFetch(`${API_BASE}/${eventType}/${eventId}`, { method: 'DELETE' });
        if (!response.ok) throw new Error(await parseError(response));
        await loadRecentEvents();
        await loadRecentStats();
    } catch (error) {
        if (error.message !== 'Не авторизован') alert('Ошибка: ' + error.message);
    }
}

async function deleteFood(foodId) {
    if (!confirm('Удалить этот продукт?')) return;
    try {
        const response = await apiFetch(`${API_BASE}/foods/${foodId}`, { method: 'DELETE' });
        if (!response.ok) throw new Error(await parseError(response));
        await loadFoods();
    } catch (error) {
        if (error.message !== 'Не авторизован') alert('Ошибка: ' + error.message);
    }
}

function renderEvents(data) {
    const todayContainer = document.getElementById('today-events');
    const yesterdayContainer = document.getElementById('yesterday-events');
    document.getElementById('today-date').textContent = `Сегодня (${data.today?.date || '---'})`;
    document.getElementById('yesterday-date').textContent = `Вчера (${data.yesterday?.date || '---'})`;
    if (!data.today?.events || data.today.events.length === 0) {
        todayContainer.innerHTML = '<div class="empty-state">Нет событий</div>';
    } else {
        todayContainer.innerHTML = data.today.events.map(renderEventItem).join('');
    }
    if (!data.yesterday?.events || data.yesterday.events.length === 0) {
        yesterdayContainer.innerHTML = '<div class="empty-state">Нет событий</div>';
    } else {
        yesterdayContainer.innerHTML = data.yesterday.events.map(renderEventItem).join('');
    }
}

function renderEventItem(event) {
    const time = new Date(event.occurred_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    let details = '';
    const typeClass = event.event_type || 'unknown';
    if (event.event_type === 'glucose') {
        details = `Сахар: ${escapeHtml(event.value)} ммоль/л`;
    } else if (event.event_type === 'insulin') {
        const typeLabel = event.insulin_type === 'short' ? 'Короткий' : 'Длинный';
        details = `Инсулин ${typeLabel}: ${escapeHtml(event.dose)} ед`;
    } else if (event.event_type === 'meal') {
        const food = foodsCache.find(f => f.id === event.food_id);
        const foodName = (food && food.name) ? escapeHtml(food.name) : 'Неизвестный продукт';
        details = `${foodName}: ${escapeHtml(event.grams)} г (${escapeHtml(event.carbs_grams)} г угл., ${escapeHtml(event.bread_units)} ХЕ)`;
    }
    if (event.note) details += ` — ${escapeHtml(event.note)}`;
    return `
        <div class="event-item ${typeClass}">
            <div class="event-info">
                <div class="event-time">${escapeHtml(time)}</div>
                <div class="event-details">${details}</div>
            </div>
            <button class="event-delete" onclick="deleteEvent('${event.event_type}-events', ${event.id})">Удалить</button>
        </div>
    `;
}

function renderStats(data) {
    document.getElementById('stats-today-date').textContent = `Сегодня (${data.today?.date || '---'})`;
    document.getElementById('stats-yesterday-date').textContent = `Вчера (${data.yesterday?.date || '---'})`;
    document.getElementById('today-stats').innerHTML = renderDayStats(data.today);
    document.getElementById('yesterday-stats').innerHTML = renderDayStats(data.yesterday);
}

function renderDayStats(dayStats) {
    if (!dayStats) return '<div class="empty-state">Нет данных</div>';
    const g = dayStats.glucose || {};
    const i = dayStats.insulin || {};
    const m = dayStats.meal || {};
    const fmtNum = (val, dec = 1) => (val !== null && val !== undefined) ? parseFloat(val).toFixed(dec) : '—';
    const fmtInt = (val) => (val !== null && val !== undefined) ? parseInt(val, 10) : 0;
    return `
        <div class="stat-card">
            <h4>Сахар</h4>
            <div class="stat-value">${fmtNum(g.avg)}</div>
            <div class="stat-label">Среднее (ммоль/л)</div>
            <div class="stat-label">Мин: ${fmtNum(g.min)}, Макс: ${fmtNum(g.max)}</div>
            <div class="stat-label">Замеров: ${fmtInt(g.count)}</div>
        </div>
        <div class="stat-card">
            <h4>Инсулин</h4>
            <div class="stat-value">${fmtNum(i.total_dose)}</div>
            <div class="stat-label">Всего (ед)</div>
            <div class="stat-label">Короткий: ${fmtNum(i.short_total_dose)} ед (${fmtInt(i.short_count)})</div>
            <div class="stat-label">Длинный: ${fmtNum(i.long_total_dose)} ед (${fmtInt(i.long_count)})</div>
        </div>
        <div class="stat-card">
            <h4>Еда</h4>
            <div class="stat-value">${fmtNum(m.total_carbs_grams, 0)}</div>
            <div class="stat-label">Углеводы (г)</div>
            <div class="stat-label">ХЕ: ${fmtNum(m.total_bread_units)}</div>
            <div class="stat-label">Приёмов пищи: ${fmtInt(m.count)}</div>
        </div>
    `;
}

function renderFoodsList() {
    const container = document.getElementById('foods-list');
    if (!foodsCache || foodsCache.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет продуктов</div>';
        return;
    }
    container.innerHTML = foodsCache.map(food => `
        <div class="food-item">
            <div class="food-info">
                <div class="food-name">${escapeHtml(food.name)}</div>
                <div class="food-carbs">${escapeHtml(food.carbs_per_100g)} г углеводов на 100 г</div>
            </div>
            <button class="food-delete" onclick="deleteFood(${food.id})">Удалить</button>
        </div>
    `).join('');
}

function updateFoodDatalist() {
    const datalist = document.getElementById('foods-datalist');
    if (!datalist) return;
    datalist.innerHTML = '';
    foodsCache.forEach(food => {
        const option = document.createElement('option');
        option.value = food.name;
        datalist.appendChild(option);
    });
}