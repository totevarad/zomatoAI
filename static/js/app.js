document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('recommend-form');
    const minRatingInput = document.getElementById('min_rating');
    const ratingValue = document.getElementById('rating-value');
    const resultsContainer = document.getElementById('results-container');
    const resultsHeader = document.getElementById('results-header');
    const candidateCount = document.getElementById('candidate-count');
    
    const initialState = document.getElementById('initial-state');
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const errorMessage = document.getElementById('error-message');

    // Update rating value display
    minRatingInput.addEventListener('input', (e) => {
        ratingValue.textContent = e.target.value;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Switch to loading state
        showState('loading');
        
        const formData = new FormData(form);
        const data = {
            location: formData.get('location'),
            cuisine: formData.get('cuisine') || null,
            budget: formData.get('budget'),
            min_rating: parseFloat(formData.get('min_rating')),
            notes: formData.get('notes') || null,
            top_n: parseInt(formData.get('top_n'))
        };

        try {
            const response = await fetch('/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to fetch recommendations');
            }

            const result = await response.json();
            renderResults(result);
        } catch (error) {
            console.error('Error:', error);
            showError(error.message);
        }
    });

    function showState(state) {
        initialState.classList.add('hidden');
        loadingState.classList.add('hidden');
        errorState.classList.add('hidden');
        resultsContainer.classList.add('hidden');
        resultsHeader.classList.add('hidden');

        if (state === 'loading') {
            loadingState.classList.remove('hidden');
        } else if (state === 'error') {
            errorState.classList.remove('hidden');
        } else if (state === 'results') {
            resultsContainer.classList.remove('hidden');
            resultsHeader.classList.remove('hidden');
        } else {
            initialState.classList.remove('hidden');
        }
    }

    function showError(message) {
        errorMessage.textContent = message;
        showState('error');
    }

    function renderResults(data) {
        resultsContainer.innerHTML = '';
        
        if (data.results.length === 0) {
            showError(data.meta.message || 'No restaurants found matching your criteria.');
            return;
        }

        candidateCount.textContent = `Found ${data.meta.candidate_count} candidates`;
        
        data.results.forEach((res, index) => {
            const card = document.createElement('div');
            card.className = 'restaurant-card';
            card.style.animationDelay = `${index * 0.1}s`;
            
            card.innerHTML = `
                <div class="card-header">
                    <h3 class="res-name">${res.name}</h3>
                    <div class="res-rating">
                        <i data-lucide="star" style="width:16px;height:16px;fill:currentColor"></i>
                        <span>${res.rating.toFixed(1)}</span>
                    </div>
                </div>
                <div class="card-meta">
                    <span class="meta-tag">${res.cuisine}</span>
                    <span class="meta-tag" style="text-transform: uppercase">${res.cost_band}</span>
                </div>
                <div class="explanation-box">
                    <div class="explanation-label">
                        <i data-lucide="sparkles" style="width:14px;height:14px"></i>
                        <span>AI Recommendation</span>
                    </div>
                    <p class="explanation-text">"${res.explanation}"</p>
                </div>
            `;
            
            resultsContainer.appendChild(card);
        });

        // Re-initialize icons for new elements
        if (window.lucide) {
            window.lucide.createIcons();
        }
        
        showState('results');
    }
});
