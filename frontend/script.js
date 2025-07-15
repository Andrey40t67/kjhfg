document.addEventListener('DOMContentLoaded', function() {
    // --- НАСТРОЙКИ ---
    // Укажите здесь URL вашего работающего backend-сервера.
    // Для локального теста это 'http://127.0.0.1:5001/api/generate'.
    // После загрузки на хостинг, замените его на реальный URL.
    const BACKEND_URL = 'http://127.0.0.1:5001/api/generate'; 
    const STYLES_URL = 'https://cdn.fusionbrain.ai/static/styles/api';

    // --- ЭЛЕМЕНТЫ DOM ---
    const generateBtn = document.getElementById('generate-btn');
    const promptInput = document.getElementById('prompt-input');
    const styleSelect = document.getElementById('style-select');
    const imageWrapper = document.getElementById('image-wrapper');
    const loader = document.getElementById('loader');
    const statusText = document.getElementById('status-text');

    // --- ФУНКЦИИ ---

    /**
     * Загружает стили из API и заполняет выпадающий список.
     */
    async function fetchAndSetStyles() {
        try {
            const response = await fetch(STYLES_URL);
            if (!response.ok) {
                throw new Error('Не удалось загрузить стили');
            }
            const styles = await response.json();
            
            // Очищаем существующие опции, кроме первой
            styleSelect.innerHTML = '<option value="">Стандартный</option>';
            
            styles.forEach(style => {
                const option = document.createElement('option');
                option.value = style.name;
                // Отображаем английское название, так как оно используется в API
                option.textContent = style.title;
                styleSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Ошибка при загрузке стилей:', error);
            statusText.textContent = 'Не удалось загрузить список стилей.';
        }
    }

    /**
     * Отправляет запрос на бэкенд для генерации изображения.
     */
    async function generateImage() {
        const prompt = promptInput.value.trim();
        const style = styleSelect.value;

        if (!prompt) {
            alert('Пожалуйста, введите текстовый запрос.');
            return;
        }

        // Блокируем кнопку и показываем лоадер
        setLoadingState(true);
        
        try {
            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt, style })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Ошибка сервера: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.image_base64) {
                displayImage(data.image_base64);
            } else {
                throw new Error(data.error || 'Не удалось получить изображение.');
            }

        } catch (error) {
            console.error('Ошибка при генерации:', error);
            statusText.textContent = `Ошибка: ${error.message}`;
            imageWrapper.innerHTML = '<p class="placeholder-text">Не удалось сгенерировать изображение.</p>';
        } finally {
            // Разблокируем кнопку и скрываем лоадер
            setLoadingState(false);
        }
    }

    /**
     * Отображает сгенерированное изображение.
     * @param {string} base64Image - Изображение в формате Base64.
     */
    function displayImage(base64Image) {
        imageWrapper.innerHTML = ''; // Очищаем контейнер
        const img = document.createElement('img');
        img.src = `data:image/jpeg;base64,${base64Image}`;
        img.alt = promptInput.value;
        imageWrapper.appendChild(img);
    }
    
    /**
     * Управляет состоянием загрузки интерфейса.
     * @param {boolean} isLoading - true, если загрузка, иначе false.
     */
    function setLoadingState(isLoading) {
        if (isLoading) {
            generateBtn.disabled = true;
            generateBtn.textContent = 'Генерация...';
            loader.style.display = 'block';
            statusText.textContent = 'Получаем модель, отправляем запрос... Это может занять до минуты.';
            imageWrapper.innerHTML = '<p class="placeholder-text">Здесь появится ваше изображение...</p>';
        } else {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Сгенерировать';
            loader.style.display = 'none';
            statusText.textContent = '';
        }
    }
    
    // --- ИНИЦИАЛИЗАЦИЯ ---
    generateBtn.addEventListener('click', generateImage);
    fetchAndSetStyles();
});
