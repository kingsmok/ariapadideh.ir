/**
 * Flask Pro - Main JavaScript
 * Version: 1.0
 */

(function() {
    'use strict';

    // ==================== Utilities ====================
    
    const Utils = {
        // Format price to Persian
        formatPrice: function(price) {
            return new Intl.NumberFormat('fa-IR').format(price) + ' تومان';
        },
        
        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Get CSRF token
        getCsrfToken: function() {
            return document.querySelector('meta[name="csrf-token"]')?.content || 
                   document.querySelector('input[name="csrf_token"]')?.value;
        },
        
        // Show toast notification
        toast: function(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <div class="toast-content">
                    <i class="toast-icon fas ${this.getToastIcon(type)}"></i>
                    <span>${message}</span>
                </div>
                <button class="toast-close">&times;</button>
            `;
            
            document.body.appendChild(toast);
            
            // Auto remove
            setTimeout(() => {
                toast.classList.add('show');
            }, 10);
            
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
            
            // Close button
            toast.querySelector('.toast-close').addEventListener('click', () => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            });
        },
        
        getToastIcon: function(type) {
            const icons = {
                success: 'fa-check-circle',
                error: 'fa-times-circle',
                warning: 'fa-exclamation-triangle',
                info: 'fa-info-circle'
            };
            return icons[type] || icons.info;
        }
    };

    // ==================== Header ====================
    
    const Header = {
        init: function() {
            this.categoriesSidebar();
            this.stickyHeader();
            this.backToTop();
        },
        
        categoriesSidebar: function() {
            const toggle = document.getElementById('categories-toggle');
            const sidebar = document.getElementById('categories-sidebar');
            const overlay = document.getElementById('sidebar-overlay');
            const closeBtn = document.getElementById('close-categories');
            
            if (!toggle || !sidebar) return;
            
            toggle.addEventListener('click', () => {
                sidebar.classList.add('open');
                overlay.classList.add('show');
                document.body.style.overflow = 'hidden';
            });
            
            const closeSidebar = () => {
                sidebar.classList.remove('open');
                overlay.classList.remove('show');
                document.body.style.overflow = '';
            };
            
            closeBtn?.addEventListener('click', closeSidebar);
            overlay?.addEventListener('click', closeSidebar);
            
            // Toggle sub categories
            document.querySelectorAll('.toggle-sub').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    const sub = this.nextElementSibling;
                    if (sub) {
                        sub.classList.toggle('show');
                        this.querySelector('i').classList.toggle('fa-chevron-down');
                        this.querySelector('i').classList.toggle('fa-chevron-up');
                    }
                });
            });
        },
        
        stickyHeader: function() {
            let lastScroll = 0;
            const header = document.querySelector('.site-header');
            
            if (!header) return;
            
            window.addEventListener('scroll', () => {
                const currentScroll = window.pageYOffset;
                
                if (currentScroll > 100) {
                    header.classList.add('sticky');
                } else {
                    header.classList.remove('sticky');
                }
                
                lastScroll = currentScroll;
            });
        },
        
        backToTop: function() {
            const btn = document.getElementById('back-to-top');
            if (!btn) return;
            
            window.addEventListener('scroll', Utils.debounce(() => {
                if (window.pageYOffset > 300) {
                    btn.classList.add('show');
                } else {
                    btn.classList.remove('show');
                }
            }, 100));
            
            btn.addEventListener('click', () => {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            });
        }
    };

    // ==================== Search ====================
    
    const Search = {
        init: function() {
            this.quickSearch();
        },
        
        quickSearch: function() {
            const searchInput = document.querySelector('.search-form input[name="q"]');
            const resultsDropdown = document.getElementById('search-results');
            
            if (!searchInput || !resultsDropdown) return;
            
            let timeout;
            
            searchInput.addEventListener('input', function() {
                clearTimeout(timeout);
                const query = this.value.trim();
                
                if (query.length < 2) {
                    resultsDropdown.innerHTML = '';
                    resultsDropdown.classList.remove('show');
                    return;
                }
                
                timeout = setTimeout(() => {
                    fetch(`/api/quick-search?q=${encodeURIComponent(query)}`)
                        .then(res => res.json())
                        .then(data => {
                            this.showResults(data);
                        })
                        .catch(err => console.error('Search error:', err));
                }, 300);
            }.bind(this));
            
            // Hide results on click outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.search-form')) {
                    resultsDropdown.classList.remove('show');
                }
            });
        },
        
        showResults: function(data) {
            const resultsDropdown = document.getElementById('search-results');
            if (!resultsDropdown) return;
            
            let html = '';
            
            if (data.products?.length) {
                html += '<div class="search-section"><h6>محصولات</h6>';
                data.products.forEach(product => {
                    html += `
                        <a href="/product/${product.slug}" class="search-item">
                            <img src="${product.image}" alt="">
                            <div class="search-item-info">
                                <span class="search-item-title">${product.title}</span>
                                <span class="search-item-price">${Utils.formatPrice(product.price)}</span>
                            </div>
                        </a>
                    `;
                });
                html += '</div>';
            }
            
            if (data.categories?.length) {
                html += '<div class="search-section"><h6>دسته‌بندی‌ها</h6>';
                data.categories.forEach(cat => {
                    html += `
                        <a href="/category/${cat.slug}" class="search-item search-item-category">
                            <i class="fas fa-folder"></i>
                            <span>${cat.title}</span>
                        </a>
                    `;
                });
                html += '</div>';
            }
            
            if (!data.products?.length && !data.categories?.length) {
                html = '<div class="search-empty">نتیجه‌ای یافت نشد</div>';
            }
            
            resultsDropdown.innerHTML = html;
            resultsDropdown.classList.add('show');
        }
    };

    // ==================== Cart ====================
    
    const Cart = {
        init: function() {
            this.addToCart();
            this.updateQuantity();
            this.removeFromCart();
        },
        
        addToCart: function() {
            document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
                btn.addEventListener('click', async function(e) {
                    e.preventDefault();
                    
                    const productId = this.dataset.productId;
                    const quantity = parseInt(this.dataset.quantity) || 1;
                    
                    this.disabled = true;
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                    
                    try {
                        const response = await fetch('/api/cart/add', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': Utils.getCsrfToken()
                            },
                            body: JSON.stringify({ product_id: productId, quantity })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            Utils.toast('محصول به سبد خرید اضافه شد', 'success');
                            this.updateCartCount(data.cart_count);
                        } else {
                            Utils.toast(data.message || 'خطا در افزودن به سبد', 'error');
                        }
                    } catch (err) {
                        Utils.toast('خطا در اتصال', 'error');
                    }
                    
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-cart-plus"></i> افزودن به سبد';
                });
            });
        },
        
        updateQuantity: function() {
            document.querySelectorAll('.cart-qty-btn').forEach(btn => {
                btn.addEventListener('click', async function() {
                    const action = this.dataset.action;
                    const itemId = this.closest('.cart-item').dataset.itemId;
                    const qtyInput = this.closest('.cart-item').querySelector('.qty-input');
                    let quantity = parseInt(qtyInput.value);
                    
                    if (action === 'increase') quantity++;
                    else if (action === 'decrease' && quantity > 1) quantity--;
                    else if (action === 'remove') quantity = 0;
                    
                    if (quantity > 0) {
                        qtyInput.value = quantity;
                        await this.updateCartItem(itemId, quantity);
                    } else {
                        await this.removeCartItem(itemId);
                    }
                }.bind(Cart));
            });
        },
        
        removeFromCart: function() {
            document.querySelectorAll('.remove-from-cart').forEach(btn => {
                btn.addEventListener('click', async function() {
                    const itemId = this.closest('.cart-item')?.dataset.itemId;
                    if (itemId) {
                        await Cart.removeCartItem(itemId);
                    }
                });
            });
        },
        
        updateCartCount: function(count) {
            const badges = document.querySelectorAll('.cart-btn .badge, #cart-count');
            badges.forEach(badge => {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'flex' : 'none';
            });
        },
        
        updateCartItem: async function(itemId, quantity) {
            try {
                const response = await fetch('/api/cart/update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': Utils.getCsrfToken()
                    },
                    body: JSON.stringify({ item_id: itemId, quantity })
                });
                
                const data = await response.json();
                if (data.success) {
                    // Update UI
                    location.reload();
                }
            } catch (err) {
                Utils.toast('خطا در بروزرسانی', 'error');
            }
        },
        
        removeCartItem: async function(itemId) {
            try {
                const response = await fetch('/api/cart/remove', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': Utils.getCsrfToken()
                    },
                    body: JSON.stringify({ item_id: itemId })
                });
                
                const data = await response.json();
                if (data.success) {
                    Utils.toast('محصول از سبد حذف شد', 'success');
                    location.reload();
                }
            } catch (err) {
                Utils.toast('خطا در حذف', 'error');
            }
        }
    };

    // ==================== Wishlist ====================
    
    const Wishlist = {
        init: function() {
            this.toggleWishlist();
        },
        
        toggleWishlist: function() {
            document.querySelectorAll('.wishlist-btn').forEach(btn => {
                btn.addEventListener('click', async function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const productId = this.dataset.productId;
                    
                    try {
                        const response = await fetch('/api/wishlist/toggle', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': Utils.getCsrfToken()
                            },
                            body: JSON.stringify({ product_id: productId })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            this.classList.toggle('active');
                            Utils.toast(data.message, 'success');
                        } else if (data.login_required) {
                            window.location.href = '/user/login?next=' + encodeURIComponent(window.location.pathname);
                        }
                    } catch (err) {
                        Utils.toast('خطا در اتصال', 'error');
                    }
                });
            });
        }
    };

    // ==================== Compare ====================
    
    const Compare = {
        init: function() {
            this.addToCompare();
        },
        
        addToCompare: function() {
            document.querySelectorAll('.compare-btn').forEach(btn => {
                btn.addEventListener('click', async function(e) {
                    e.preventDefault();
                    
                    const productId = this.dataset.productId;
                    
                    try {
                        const response = await fetch('/api/compare/add', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': Utils.getCsrfToken()
                            },
                            body: JSON.stringify({ product_id: productId })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            Utils.toast(data.message, 'success');
                            if (data.count) {
                                document.querySelector('.compare-count').textContent = data.count;
                            }
                        }
                    } catch (err) {
                        Utils.toast('خطا در اتصال', 'error');
                    }
                });
            });
        }
    };

    // ==================== Forms ====================
    
    const Forms = {
        init: function() {
            this.ajaxForms();
            this.inputValidation();
        },
        
        ajaxForms: function() {
            document.querySelectorAll('form[data-ajax="true"]').forEach(form => {
                form.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const submitBtn = form.querySelector('[type="submit"]');
                    const originalText = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                    
                    const formData = new FormData(form);
                    const url = form.action || window.location.href;
                    
                    try {
                        const response = await fetch(url, {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            Utils.toast(data.message || 'عملیات موفق', 'success');
                            if (data.redirect) {
                                setTimeout(() => window.location.href = data.redirect, 1000);
                            }
                        } else {
                            Utils.toast(data.message || 'خطا در عملیات', 'error');
                            if (data.errors) {
                                Forms.showErrors(form, data.errors);
                            }
                        }
                    } catch (err) {
                        Utils.toast('خطا در اتصال', 'error');
                    }
                    
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                });
            });
        },
        
        inputValidation: function() {
            document.querySelectorAll('.form-control[required]').forEach(input => {
                input.addEventListener('blur', function() {
                    if (!this.value.trim()) {
                        this.classList.add('is-invalid');
                    } else {
                        this.classList.remove('is-invalid');
                        this.classList.add('is-valid');
                    }
                });
            });
        },
        
        showErrors: function(form, errors) {
            Object.keys(errors).forEach(field => {
                const input = form.querySelector(`[name="${field}"]`);
                if (input) {
                    input.classList.add('is-invalid');
                    const errorDiv = input.parentElement.querySelector('.invalid-feedback');
                    if (errorDiv) {
                        errorDiv.textContent = errors[field][0];
                    }
                }
            });
        }
    };

    // ==================== Image Lazy Loading ====================
    
    const LazyLoad = {
        init: function() {
            if ('IntersectionObserver' in window) {
                this.setupObserver();
            } else {
                this.loadAll();
            }
        },
        
        setupObserver: function() {
            const observer = new IntersectionObserver((entries, obs) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        obs.unobserve(img);
                    }
                });
            });
            
            document.querySelectorAll('img[data-src]').forEach(img => {
                observer.observe(img);
            });
        },
        
        loadAll: function() {
            document.querySelectorAll('img[data-src]').forEach(img => {
                img.src = img.dataset.src;
            });
        }
    };

    // ==================== Initialize ====================
    
    document.addEventListener('DOMContentLoaded', function() {
        Header.init();
        Search.init();
        Cart.init();
        Wishlist.init();
        Compare.init();
        Forms.init();
        LazyLoad.init();
        
        // Flash messages auto-dismiss
        setTimeout(() => {
            document.querySelectorAll('.alert').forEach(alert => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            });
        }, 5000);
    });

    // Export to global
    window.FlaskPro = {
        Utils,
        Header,
        Search,
        Cart,
        Wishlist,
        Compare,
        Forms,
        LazyLoad
    };

})();
