const API_BASE = '/api';

let foodsCache = [];

// Безопасный парсер ошибок: не упадет, если сервер вернет HTML вместо JSON
async function parseError(response) {
    try {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            const data = await response.json();
            if (data && data.detail) {
                if (Array.isArray(data.detail)) {
                    return data.detail[0].msg || 'Ошибка валидации данных';
                }
                return data.detail;
            }
        }
        return `Ошибка сервера (${response.status})`;
    } catch (e) {
        return `Ошибка сервера (${response.status})`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadFoods();
    loadRecentEvents();
    loadRecentStats();

    document.getElementById('glucose-form').addEventListener('submit', handleGlucoseSubmit);
    document.getElementById('insulin-form').addEventListener('submit', handleInsulinSubmit);
    document.getElementById('meal-form').addEventListener('submit', handleMealSubmit);
    document.getElementById('food-form').addEventListener('submit', handleFoodSubmit);
});

async function loadFoods() {
    try {
        const response = await fetch(`${API_BASE}/foods`);
        if (!response.ok) throw new Error(await parseError(response));

        foodsCache = await response.json();
        renderFoodsList();
        updateFoodDatalist();
    } catch (error) {
        console.error('Ошибка загрузки продуктов:', error);
    }
}

async function loadRecentEvents() {
    try {
        const response = await fetch(`${API_BASE}/events/recent`);
        if (!response.ok) throw new Error(await parseError(response));

        const data = await response.json();
        renderEvents(data);
    } catch (error) {
        console.error('Ошибка загрузки событий:', error);
        alert('Ошибка загрузки событий: ' + error.message);
    }
}

async function loadRecentStats() {
    try {
        const response = await fetch(`${API_BASE}/stats/recent`);
        if (!response.ok) throw new Error(await parseError(response));

        const data = await response.json();
        renderStats(data);
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
        alert('Ошибка загрузки статистики: ' + error.message);
    }
}

async function handleGlucoseSubmit(event) {
    event.preventDefault();
    const value = parseFloat(document.getElementById('glucose-value').value);

    try {
        const response = await fetch(`${API_BASE}/glucose-events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: value })
        });

        if (!response.ok) throw new Error(await parseError(response));

        document.getElementById('glucose-form').reset();
        await loadRecentEvents();
        await loadRecentStats();
        alert('Измерение сахара добавлено!');
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

async function handleInsulinSubmit(event) {
    event.preventDefault();
    const insulin_type = document.getElementById('insulin-type').value;
    const dose = parseFloat(document.getElementById('insulin-dose').value);

    try {
        const response = await fetch(`${API_BASE}/insulin-events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ insulin_type, dose })
        });

        if (!response.ok) throw new Error(await parseError(response));

        document.getElementById('insulin-form').reset();
        await loadRecentEvents();
        await loadRecentStats();
        alert('Инсулин добавлен!');
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

async function handleMealSubmit(event) {
    event.preventDefault();

    const foodNameInput = document.getElementById('meal-food-name');
    const gramsInput = document.getElementById('meal-grams');

    const foodName = foodNameInput.value.trim();
    const grams = parseFloat(gramsInput.value);

    // Ищем продукт по имени (игнорируем регистр)
    const food = foodsCache.find(f => f.name.toLowerCase() === foodName.toLowerCase());

    if (!food) {
        alert('Продукт не найден в справочнике. Введите точное название из подсказок или сначала добавьте его.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/meal-events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                food_id: food.id,
                grams: grams
            })
        });

        if (!response.ok) throw new Error(await parseError(response));

        foodNameInput.value = '';
        gramsInput.value = '';

        await loadRecentEvents();
        await loadRecentStats();
        alert('Приём пищи добавлен!');
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

async function handleFoodSubmit(event) {
    event.preventDefault();
    const name = document.getElementById('food-name').value;
    const carbs_per_100g = parseFloat(document.getElementById('food-carbs').value);

    try {
        const response = await fetch(`${API_BASE}/foods`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, carbs_per_100g })
        });

        if (!response.ok) throw new Error(await parseError(response));

        document.getElementById('food-form').reset();
        await loadFoods();
        alert('Продукт добавлен!');
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

async function deleteEvent(eventType, eventId) {
    if (!confirm('Удалить это событие?')) return;

    try {
        const response = await fetch(`${API_BASE}/${eventType}/${eventId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error(await parseError(response));

        await loadRecentEvents();
        await loadRecentStats();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

async function deleteFood(foodId) {
    if (!confirm('Удалить этот продукт?')) return;

    try {
        const response = await fetch(`${API_BASE}/foods/${foodId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error(await parseError(response));

        await loadFoods();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

function renderEvents(data) {
    const todayContainer = document.getElementById('today-events');
    document.getElementById('today-date').textContent = `Сегодня (${data.today.date})`;

    if (data.today.events.length === 0) {
        todayContainer.innerHTML = '<div class="empty-state">Нет событий</div>';
    } else {
        todayContainer.innerHTML = data.today.events.map(event => renderEventItem(event)).join('');
    }

    const yesterdayContainer = document.getElementById('yesterday-events');
    document.getElementById('yesterday-date').textContent = `Вчера (${data.yesterday.date})`;

    if (data.yesterday.events.length === 0) {
        yesterdayContainer.innerHTML = '<div class="empty-state">Нет событий</div>';
    } else {
        yesterdayContainer.innerHTML = data.yesterday.events.map(event => renderEventItem(event)).join('');
    }
}

function renderEventItem(event) {
    const time = new Date(event.occurred_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    let details = '';
    let typeClass = event.event_type;

    if (event.event_type === 'glucose') {
        details = `Сахар: ${event.value} ммоль/л`;
    } else if (event.event_type === 'insulin') {
        const typeLabel = event.insulin_type === 'short' ? 'Короткий' : 'Длинный';
        details = `Инсулин ${typeLabel}: ${event.dose} ед`;
    } else if (event.event_type === 'meal') {
        const food = foodsCache.find(f => f.id === event.food_id);
        const foodName = food ? food.name : 'Неизвестный продукт';
        details = `${foodName}: ${event.grams} г (${event.carbs_grams} г углеводов, ${event.bread_units} ХЕ)`;
    }

    if (event.note) {
        details += ` — ${event.note}`;
    }

    return `
        <div class="event-item ${typeClass}">
            <div class="event-info">
                <div class="event-time">${time}</div>
                <div class="event-details">${details}</div>
            </div>
            <button class="event-delete" onclick="deleteEvent('${event.event_type}-events', ${event.id})">Удалить</button>
        </div>
    `;
}

function renderStats(data) {
    const todayContainer = document.getElementById('today-stats');
    document.getElementById('stats-today-date').textContent = `Сегодня (${data.today.date})`;
    todayContainer.innerHTML = renderDayStats(data.today);

    const yesterdayContainer = document.getElementById('yesterday-stats');
    document.getElementById('stats-yesterday-date').textContent = `Вчера (${data.yesterday.date})`;
    yesterdayContainer.innerHTML = renderDayStats(data.yesterday);
}

function renderDayStats(dayStats) {
    const glucose = dayStats.glucose;
    const insulin = dayStats.insulin;
    const meal = dayStats.meal;

    const formatNum = (val, decimals = 1) => (val !== null && val !== undefined ? parseFloat(val).toFixed(decimals) : '—');
    const formatInt = (val) => (val !== null && val !== undefined ? parseInt(val, 10) : 0);

    return `
        <div class="stat-card">
            <h4>Сахар</h4>
            <div class="stat-value">${formatNum(glucose.avg)}</div>
            <div class="stat-label">Среднее (ммоль/л)</div>
            <div class="stat-label">Мин: ${formatNum(glucose.min)}, Макс: ${formatNum(glucose.max)}</div>
            <div class="stat-label">Замеров: ${formatInt(glucose.count)}</div>
        </div>

        <div class="stat-card">
            <h4>Инсулин</h4>
            <div class="stat-value">${formatNum(insulin.total_dose)}</div>
            <div class="stat-label">Всего (ед)</div>
            <div class="stat-label">Короткий: ${formatNum(insulin.short_total_dose)} ед (${formatInt(insulin.short_count)})</div>
            <div class="stat-label">Длинный: ${formatNum(insulin.long_total_dose)} ед (${formatInt(insulin.long_count)})</div>
        </div>

        <div class="stat-card">
            <h4>Еда</h4>
            <div class="stat-value">${formatNum(meal.total_carbs_grams, 0)}</div>
            <div class="stat-label">Углеводы (г)</div>
            <div class="stat-label">ХЕ: ${formatNum(meal.total_bread_units)}</div>
            <div class="stat-label">Приёмов пищи: ${formatInt(meal.count)}</div>
        </div>
    `;
}

function renderFoodsList() {
    const container = document.getElementById('foods-list');

    if (foodsCache.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет продуктов</div>';
        return;
    }

    container.innerHTML = foodsCache.map(food => `
        <div class="food-item">
            <div class="food-info">
                <div class="food-name">${food.name}</div>
                <div class="food-carbs">${food.carbs_per_100g} г углеводов на 100 г</div>
            </div>
            <button class="food-delete" onclick="deleteFood(${food.id})">Удалить</button>
        </div>
    `).join('');
}

// Новая функция для заполнения datalist вместо select
function updateFoodDatalist() {
    const datalist = document.getElementById('foods-datalist');
    datalist.innerHTML = '';

    foodsCache.forEach(food => {
        const option = document.createElement('option');
        option.value = food.name; // Пользователь видит и выбирает имя
        datalist.appendChild(option);
    });
}