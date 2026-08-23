/* ==========================================================================
   RAHSA DEV - Interactive Javascript Architecture
   Smart Glass Scroll Navbar, Off-canvas Mobile Drawer, AJAX Cart, Quick Search
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {
    
    // ==================== Section A: Navbar Scroll Transition ====================
    const siteNavbar = document.getElementById('site-navbar');
    if (siteNavbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                siteNavbar.classList.add('scrolled');
            } else {
                siteNavbar.classList.remove('scrolled');
            }
        });
    }

    // ==================== Off-canvas Mobile Drawer ====================
    const drawerOverlay = document.getElementById('mobile-drawer-overlay');
    const mobileDrawer = document.getElementById('mobile-drawer');
    const openDrawerBtn = document.getElementById('open-drawer-btn');
    const closeDrawerBtn = document.getElementById('close-drawer-btn');

    function openDrawer() {
        if (mobileDrawer && drawerOverlay) {
            mobileDrawer.classList.add('active');
            drawerOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeDrawer() {
        if (mobileDrawer && drawerOverlay) {
            mobileDrawer.classList.remove('active');
            drawerOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    if (openDrawerBtn) openDrawerBtn.addEventListener('click', openDrawer);
    if (closeDrawerBtn) closeDrawerBtn.addEventListener('click', closeDrawer);
    if (drawerOverlay) drawerOverlay.addEventListener('click', closeDrawer);

    // ==================== Quick Search API ====================
    const searchInputs = document.querySelectorAll('.js-quick-search');
    searchInputs.forEach(input => {
        let debounceTimer;
        const resultsContainer = input.parentElement.querySelector('.search-results-dropdown') || 
                                 document.getElementById('search-results');

        input.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const query = this.value.trim();

            if (query.length < 2) {
                if (resultsContainer) {
                    resultsContainer.classList.remove('show');
                    resultsContainer.innerHTML = '';
                }
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`/api/quick-search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (!resultsContainer) return;
                        
                        if (data.results && data.results.length > 0) {
                            let html = '<div style="font-size:0.78rem; font-weight:700; color:#9ca3af; padding:0.4rem 0.6rem; border-bottom:1px solid rgba(255,255,255,0.1);">نتایج جستجو:</div>';
                            data.results.forEach(item => {
                                html += `
                                    <a href="${item.url}" style="display:flex; align-items:center; gap:0.75rem; padding:0.6rem; text-decoration:none; border-bottom:1px solid rgba(255,255,255,0.05); color:#ffffff;">
                                        <div style="font-size:1.2rem;">${item.type === 'product' ? '📦' : '📁'}</div>
                                        <div style="flex:1;">
                                            <div style="font-weight:700; font-size:0.875rem;">${item.title}</div>
                                            <div style="font-size:0.75rem; color:#fca311; font-weight:800;">${item.price ? item.price : ''}</div>
                                        </div>
                                    </a>
                                `;
                            });
                            resultsContainer.innerHTML = html;
                            resultsContainer.classList.add('show');
                        } else {
                            resultsContainer.innerHTML = '<div style="padding:0.75rem; text-align:center; color:#9ca3af; font-size:0.85rem;">هیچ دیتایی یافت نشد.</div>';
                            resultsContainer.classList.add('show');
                        }
                    })
                    .catch(err => console.error('Search API error:', err));
            }, 250);
        });
    });

    document.addEventListener('click', function(e) {
        if (!e.target.closest('.header-search-wrap') && !e.target.closest('.search-form')) {
            document.querySelectorAll('.search-results-dropdown').forEach(el => el.classList.remove('show'));
        }
    });

    // ==================== AJAX Add to Cart ====================
    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            if (!productId) return;

            const origText = this.innerHTML;
            this.innerHTML = '⏳ ثبت...';
            this.disabled = true;

            fetch('/api/cart/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
                },
                body: JSON.stringify({ product_id: parseInt(productId), quantity: 1 })
            })
            .then(res => res.json())
            .then(data => {
                this.innerHTML = origText;
                this.disabled = false;
                if (data.success) {
                    showToast('با موفقیت ثبت نام / به سبد اضافه شد! 🛒', 'success');
                    document.querySelectorAll('.cart-badge-count').forEach(badge => {
                        badge.textContent = data.cart_count || 0;
                    });
                } else {
                    showToast(data.message || 'خطا در انجام درخواست', 'error');
                }
            })
            .catch(err => {
                this.innerHTML = origText;
                this.disabled = false;
                showToast('خطایی رخ داد.', 'error');
            });
        });
    });

    // ==================== Toast Notifications ====================
    function showToast(message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = 'position:fixed; bottom:80px; inset-inline-end:1.5rem; z-index:9999; display:flex; flex-direction:column; gap:0.5rem;';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.style.cssText = `
            background:#14213d; color:#fff; padding:0.85rem 1.25rem; border-radius:0.75rem; 
            box-shadow:0 10px 25px rgba(0,0,0,0.5); font-size:0.875rem; border-inline-start:4px solid ${type === 'success' ? '#10b981' : '#ef4444'};
            animation: fadeIn 0.3s ease;
        `;
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3500);
    }

    // ==================== Back To Top ====================
    const backToTopBtn = document.getElementById('back-to-top');
    if (backToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 300) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        });
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ==================== FAQ Accordion ====================
    document.querySelectorAll('.faq-question-toggle').forEach(button => {
        button.addEventListener('click', () => {
            const faqItem = button.parentElement;
            const answer = faqItem.querySelector('.faq-answer-body');
            const isVisible = answer.style.display === 'block';

            document.querySelectorAll('.faq-answer-body').forEach(ans => ans.style.display = 'none');
            document.querySelectorAll('.faq-icon-arrow').forEach(arrow => arrow.textContent = '➕');

            if (!isVisible) {
                answer.style.display = 'block';
                button.querySelector('.faq-icon-arrow').textContent = '➖';
            }
        });
    });
});
