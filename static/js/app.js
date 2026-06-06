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

    // Mobile Sidebar Elements
    const sidebarNav = document.getElementById('sidebar-nav');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const mobileFilterBtn = document.getElementById('mobile-filter-btn');
    const sidebarCloseBtn = document.getElementById('sidebar-close-btn');

    // Cuisine Pills Elements
    const cuisinePills = document.getElementById('cuisine-pills');
    const cuisineInput = document.getElementById('cuisine');

    // Top Search Elements
    const topSearch = document.getElementById('top-search');
    const notesInput = document.getElementById('notes');

    // Update rating value display
    minRatingInput.addEventListener('input', (e) => {
        ratingValue.textContent = e.target.value;
    });

    // Budget slider listener
    const budgetSlider = document.getElementById('budget-slider');
    const budgetValueDisplay = document.getElementById('budget-value-display');
    const budgetInput = document.getElementById('budget');

    if (budgetSlider && budgetValueDisplay && budgetInput) {
        budgetSlider.addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            let band = 'high';
            let bandName = 'High';
            
            if (val <= 400) {
                band = 'low';
                bandName = 'Low';
            } else if (val <= 800) {
                band = 'medium';
                bandName = 'Med';
            }
            
            budgetValueDisplay.textContent = `₹${val} (${bandName})`;
            budgetInput.value = band;
        });
    }


    // Mobile Sidebar controls
    function openSidebar() {
        sidebarNav.classList.remove('-translate-x-full');
        sidebarNav.classList.add('translate-x-0');
        sidebarOverlay.classList.remove('hidden');
    }

    function closeSidebar() {
        sidebarNav.classList.remove('translate-x-0');
        sidebarNav.classList.add('-translate-x-full');
        sidebarOverlay.classList.add('hidden');
    }

    if (mobileFilterBtn) {
        mobileFilterBtn.addEventListener('click', openSidebar);
    }
    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener('click', closeSidebar);
    }
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    // Cuisine pills quick select
    if (cuisinePills) {
        cuisinePills.addEventListener('click', (e) => {
            const pill = e.target.closest('[data-value]');
            if (pill) {
                const val = pill.getAttribute('data-value');
                cuisineInput.value = val;
                // Highlight active pill (optional enhancement)
                Array.from(cuisinePills.children).forEach(child => {
                    child.classList.remove('border-primary-container', 'text-on-surface');
                });
                pill.classList.add('border-primary-container', 'text-on-surface');
            }
        });
    }

    // Top search bar integration
    if (topSearch) {
        topSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = topSearch.value.trim();
                if (query) {
                    notesInput.value = query;
                    // Trigger form submit
                    form.dispatchEvent(new Event('submit', { cancelable: true }));
                    closeSidebar();
                }
            }
        });
    }

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
            // On mobile, automatically close the filter drawer when showing results
            closeSidebar();
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

    function getCuisineImage(cuisineStr) {
        const lower = (cuisineStr || "").toLowerCase();
        if (lower.includes("pizza") || lower.includes("italian") || lower.includes("pasta")) {
            return "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60"; // Pasta/Salad
        } else if (lower.includes("sushi") || lower.includes("japanese") || lower.includes("asian")) {
            return "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=500&auto=format&fit=crop&q=60"; // Sushi
        } else if (lower.includes("burger") || lower.includes("fast food") || lower.includes("american")) {
            return "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500&auto=format&fit=crop&q=60"; // Burger
        } else if (lower.includes("indian") || lower.includes("biryani") || lower.includes("kebab") || lower.includes("curry")) {
            return "https://images.unsplash.com/photo-1585938338392-50a59970d8ee?w=500&auto=format&fit=crop&q=60"; // Indian Biryani/Curry
        } else if (lower.includes("chinese") || lower.includes("noodle") || lower.includes("dim sum")) {
            return "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=500&auto=format&fit=crop&q=60"; // Chinese Noodles
        } else if (lower.includes("dessert") || lower.includes("sweet") || lower.includes("bakery") || lower.includes("cake")) {
            return "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=500&auto=format&fit=crop&q=60"; // Donuts/Desserts
        } else if (lower.includes("cafe") || lower.includes("coffee") || lower.includes("beverage")) {
            return "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=500&auto=format&fit=crop&q=60"; // Coffee Cafe
        }
        // Default high-end dining interior or food photo
        return "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=500&auto=format&fit=crop&q=60"; // Fine Dining Plate
    }

    function renderResults(data) {
        resultsContainer.innerHTML = '';
        
        if (data.results.length === 0) {
            showError(data.meta.message || 'No restaurants found matching your criteria.');
            return;
        }

        candidateCount.textContent = `${data.meta.candidate_count} candidates found`;
        
        data.results.forEach((res, index) => {
            const card = document.createElement('article');
            card.className = 'bg-white/5 backdrop-blur-md border border-white/10 rounded-xl overflow-hidden hover:bg-white/[0.08] hover:border-white/20 transition-all duration-300 group flex flex-col opacity-0 translate-y-4';
            card.style.animation = `fadeIn 0.5s ease-out forwards`;
            card.style.animationDelay = `${index * 0.08}s`;
            
            const actionButton = res.url 
                ? `<a href="${res.url}" target="_blank" class="w-full bg-gradient-to-r from-primary-container to-secondary-container text-white py-2.5 rounded-lg font-label-caps text-[12px] uppercase tracking-wider flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all duration-300">
                     <span class="material-symbols-outlined text-[16px] font-bold">open_in_new</span>
                     View on Zomato
                   </a>`
                : `<button class="w-full bg-[rgba(255,255,255,0.05)] border border-white/10 text-white py-2.5 rounded-lg font-label-caps text-[12px] uppercase tracking-wider hover:bg-white/10 active:scale-[0.98] transition-all">
                     View Menu
                   </button>`;

            const imageUrl = res.image_url || getCuisineImage(res.cuisine);

            
            card.innerHTML = `
                <div class="relative h-44 w-full overflow-hidden bg-surface-container-low">
                    <img alt="Restaurant Image" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" src="${imageUrl}"/>
                    <div class="absolute top-4 right-4 bg-black/60 backdrop-blur-sm px-2.5 py-1 rounded-full flex items-center gap-1 border border-white/10">
                        <span class="material-symbols-outlined text-[#FF9F43] text-[15px] font-fill-1">star</span>
                        <span class="font-label-caps text-[11px] font-bold text-white leading-none">${res.rating.toFixed(1)}</span>
                    </div>
                </div>
                <div class="p-5 flex flex-col flex-1 gap-3.5">
                    <div>
                        <h3 class="font-title-md text-[17px] leading-snug text-on-surface font-semibold group-hover:text-primary transition-colors">${res.name}</h3>
                        <p class="font-body-sm text-[12px] text-on-surface-variant mt-1">${res.cuisine}</p>
                        <span class="inline-block mt-2 px-2.5 py-0.5 bg-white/5 border border-white/10 rounded-full font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider">${res.cost_band} cost</span>
                    </div>
                    <!-- AI Explanation Block -->
                    <div class="bg-[rgba(255,255,255,0.03)] border border-white/5 rounded-lg p-3.5 flex gap-2.5 items-start mt-auto relative overflow-hidden">
                        <div class="absolute top-0 left-0 w-[2px] h-full bg-gradient-to-b from-primary-container to-secondary-container"></div>
                        <span class="material-symbols-outlined text-primary-container text-[16px] mt-0.5">auto_awesome</span>
                        <p class="font-body-sm text-[12px] leading-relaxed text-on-surface-variant flex-1">
                            ${res.explanation}
                        </p>
                    </div>
                    <div class="pt-1">
                        ${actionButton}
                    </div>
                </div>
            `;
            
            resultsContainer.appendChild(card);
        });

        // Inject animation style dynamically if not already present
        if (!document.getElementById('card-animations')) {
            const style = document.createElement('style');
            style.id = 'card-animations';
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(16px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `;
            document.head.appendChild(style);
        }
        
        showState('results');
    }
});
