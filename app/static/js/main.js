/**
 * Rahsa Dev — Interactive Behaviors
 * Mobile drawer, back-to-top, loading states, flash auto-dismiss, etc.
 * Vanilla JS, no dependencies.
 */

(function () {
    'use strict';

    // ============================================================
    // Mobile Drawer
    // ============================================================
    const drawer = document.querySelector('.mobile-drawer-container');
    const overlay = document.querySelector('.mobile-drawer-overlay');
    const openBtn = document.getElementById('open-drawer-btn');
    const closeBtn = document.getElementById('close-drawer-btn');

    function openDrawer() {
        if (!drawer || !overlay) return;
        drawer.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        // Focus the close button for keyboard users
        if (closeBtn) setTimeout(() => closeBtn.focus(), 100);
    }

    function closeDrawer() {
        if (!drawer || !overlay) return;
        drawer.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (openBtn) openBtn.addEventListener('click', openDrawer);
    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
    if (overlay) overlay.addEventListener('click', closeDrawer);

    // ESC to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && drawer && drawer.classList.contains('active')) {
            closeDrawer();
        }
    });

    // ============================================================
    // Back to Top
    // ============================================================
    const backToTop = document.getElementById('back-to-top');
    if (backToTop) {
        // Throttled scroll listener
        let ticking = false;
        window.addEventListener('scroll', () => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    if (window.scrollY > 400) {
                        backToTop.classList.add('show');
                    } else {
                        backToTop.classList.remove('show');
                    }
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });

        backToTop.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ============================================================
    // Flash Messages Auto-Dismiss
    // ============================================================
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((msg) => {
        // Auto-dismiss after 5s
        setTimeout(() => {
            msg.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(-20px)';
            setTimeout(() => msg.remove(), 400);
        }, 5000);

        // Manual close button
        const closeBtn = msg.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                msg.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                msg.style.opacity = '0';
                msg.style.transform = 'translateX(-20px)';
                setTimeout(() => msg.remove(), 300);
            });
        }
    });

    // ============================================================
    // Loading State on Form Submit
    // ============================================================
    document.querySelectorAll('form').forEach((form) => {
        form.addEventListener('submit', (e) => {
            const submitBtn = form.querySelector('[type="submit"]');
            // Skip if form has data-no-loading
            if (form.hasAttribute('data-no-loading')) return;
            // Skip if button is explicitly marked
            if (submitBtn && submitBtn.hasAttribute('data-no-loading')) return;

            if (submitBtn && !submitBtn.disabled) {
                submitBtn.classList.add('is-loading');
                submitBtn.disabled = true;

                // Re-enable after 15s as a safety net (in case the server hangs)
                setTimeout(() => {
                    submitBtn.classList.remove('is-loading');
                    submitBtn.disabled = false;
                }, 15000);
            }
        });
    });

    // ============================================================
    // Persian Numeral Conversion (display-only, doesn't change DOM value)
    // ============================================================
    function toPersianDigits(str) {
        const en = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
        const fa = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
        let result = String(str);
        for (let i = 0; i < 10; i++) {
            result = result.replace(new RegExp(en[i], 'g'), fa[i]);
        }
        return result;
    }

    // Apply to all elements with [data-persian-num] attribute
    document.querySelectorAll('[data-persian-num]').forEach((el) => {
        // For text nodes only (don't change input values)
        if (el.children.length === 0) {
            el.textContent = toPersianDigits(el.textContent);
        }
    });

    // ============================================================
    // Auto-dismiss alerts after action (e.g., added to cart)
    // ============================================================
    const cartCountBadge = document.querySelector('.bottom-nav-tab .badge-count');
    if (cartCountBadge) {
        // Pulse animation when count changes
        const observer = new MutationObserver(() => {
            cartCountBadge.style.animation = 'none';
            setTimeout(() => {
                cartCountBadge.style.animation = 'pulse 0.4s ease';
            }, 10);
        });
        observer.observe(cartCountBadge, { childList: true, characterData: true, subtree: true });
    }

    // ============================================================
    // Smooth anchor scroll for in-page links
    // ============================================================
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#' || href.length < 2) return;
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                const offset = 80; // header height
                const top = target.getBoundingClientRect().top + window.scrollY - offset;
                window.scrollTo({ top, behavior: 'smooth' });
            }
        });
    });

    // ============================================================
    // Image Lazy Loading Fallback (for older browsers)
    // ============================================================
    if ('loading' in HTMLImageElement.prototype) {
        // Native lazy loading is supported — no-op
    } else {
        // Fallback: IntersectionObserver
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                        }
                        imageObserver.unobserve(img);
                    }
                });
            });
            lazyImages.forEach((img) => imageObserver.observe(img));
        } else {
            // Last resort: load all
            lazyImages.forEach((img) => {
                if (img.dataset.src) img.src = img.dataset.src;
            });
        }
    }

    // ============================================================
    // Add pulse animation (used by cart badge)
    // ============================================================
    if (!document.getElementById('pulse-keyframes')) {
        const style = document.createElement('style');
        style.id = 'pulse-keyframes';
        style.textContent = `
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.4); }
            }
        `;
        document.head.appendChild(style);
    }

    // ============================================================
    // Active link highlighting in mobile bottom nav
    // ============================================================
    const currentPath = window.location.pathname;
    document.querySelectorAll('.bottom-nav-tab').forEach((tab) => {
        const href = tab.getAttribute('href');
        if (href && href !== '/' && currentPath.startsWith(href)) {
            tab.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            tab.classList.add('active');
        }
    });

})();

// ============================================================
// NEW FEATURES JS — تم روشن/تیره، پیش‌بارگر، استوری‌ساز، سواچ،
// گالری ویدئو، فیلتر ایجکسی (الگوی قالب‌های شرکتی راست‌چین)
// ============================================================
(function () {
    'use strict';

    // ---------------- Theme Toggle (تم تیره/روشن) ----------------
    const themeToggle = document.getElementById('theme-toggle');
    const htmlEl = document.documentElement;

    // Apply saved theme before paint (also handled by inline script in main.js head)
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') { htmlEl.setAttribute('data-theme', 'light'); }

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const isLight = htmlEl.getAttribute('data-theme') === 'light';
            if (isLight) {
                htmlEl.removeAttribute('data-theme');
                localStorage.setItem('theme', 'dark');
            } else {
                htmlEl.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
            }
        });
    }

    // ---------------- Preloader (پیش‌بارگر) ----------------
    const preloader = document.getElementById('preloader');
    if (preloader) {
        document.body.classList.add('preloader-active');
        window.addEventListener('load', function () {
            setTimeout(function () {
                preloader.classList.add('hide');
                document.body.classList.remove('preloader-active');
                setTimeout(function () { preloader.remove(); }, 500);
            }, 350);
        });
        // Fallback: اگر load دیر شد (مثلاً تصویر کند)
        setTimeout(function () {
            if (preloader && preloader.parentNode) {
                preloader.classList.add('hide');
                document.body.classList.remove('preloader-active');
            }
        }, 4000);
    }

    // ---------------- Story Viewer (استوری‌ساز) ----------------
    const storyViewer = document.getElementById('story-viewer');
    if (storyViewer) {
        const storyButtons = Array.from(document.querySelectorAll('.story-item'));
        const mediaBox = document.getElementById('story-viewer-media');
        const titleEl = document.getElementById('story-viewer-title');
        const ctaEl = document.getElementById('story-cta');
        const viewsEl = document.getElementById('story-view-views');
        const progressBar = document.getElementById('story-progress-bar');
        let current = 0, progressTimer = null;

        function showStory(index) {
            if (index < 0 || index >= storyButtons.length) { closeStory(); return; }
            current = index;
            const btn = storyButtons[index];
            const data = btn.dataset;

            titleEl.textContent = data.title || '';
            mediaBox.innerHTML = '';

            let mediaEl;
            if (data.video) {
                mediaEl = document.createElement('video');
                mediaEl.src = data.video;
                mediaEl.autoplay = true; mediaEl.controls = true; mediaEl.playsInline = true;
            } else if (data.image) {
                mediaEl = document.createElement('img');
                mediaEl.src = data.image;
                mediaEl.alt = data.title || 'استوری';
            }
            if (mediaEl) { mediaBox.appendChild(mediaEl); }

            if (data.link && data.link !== '') {
                ctaEl.href = data.link;
                ctaEl.textContent = data.linkText || 'مشاهده';
                ctaEl.hidden = false;
            } else {
                ctaEl.hidden = true;
            }

            storyViewer.hidden = false;
            document.body.style.overflow = 'hidden';

            // ثبت بازدید
            if (data.viewUrl && navigator.sendBeacon) {
                navigator.sendBeacon(data.viewUrl);
                if (viewsEl) {
                    viewsEl.textContent = '👁 در حال نمایش';
                    viewsEl.hidden = false;
                }
            }

            // نوار پیشرفت
            const duration = (parseInt(data.duration, 10) || 5) * 1000;
            if (progressBar) {
                progressBar.style.transition = 'none';
                progressBar.style.width = '0%';
                requestAnimationFrame(function () {
                    progressBar.style.transition = 'width ' + duration + 'ms linear';
                    progressBar.style.width = '100%';
                });
            }
            clearInterval(progressTimer);
            progressTimer = setInterval(function () {
                nextStory();
            }, duration);
        }

        function nextStory() { showStory(current + 1); }
        function prevStory() { showStory(current - 1); }

        function closeStory() {
            clearInterval(progressTimer);
            storyViewer.hidden = true;
            mediaBox.innerHTML = '';
            document.body.style.overflow = '';
        }

        storyButtons.forEach(function (btn, i) {
            btn.addEventListener('click', function () { showStory(i); });
        });

        const closeBtn = document.getElementById('story-close');
        const nextBtn = document.getElementById('story-next');
        const prevBtn = document.getElementById('story-prev');
        if (closeBtn) closeBtn.addEventListener('click', closeStory);
        if (nextBtn) nextBtn.addEventListener('click', function () { clearInterval(progressTimer); nextStory(); });
        if (prevBtn) prevBtn.addEventListener('click', function () { clearInterval(progressTimer); prevStory(); });

        document.addEventListener('keydown', function (e) {
            if (storyViewer.hidden) return;
            if (e.key === 'Escape') closeStory();
            if (e.key === 'ArrowLeft') { clearInterval(progressTimer); nextStory(); }
            if (e.key === 'ArrowRight') { clearInterval(progressTimer); prevStory(); }
        });
    }

    // ---------------- Variation Swatches (سواچ رنگ/تصویر) ----------------
    const swatchWrap = document.getElementById('product-swatches');
    if (swatchWrap) {
        const priceEl = document.getElementById('product-price-display');
        const nameEl = document.getElementById('swatch-selected-name');
        const basePrice = parseFloat(priceEl ? (priceEl.dataset.basePrice || 0) : 0);

        swatchWrap.querySelectorAll('.swatch-rahsa').forEach(function (sw) {
            sw.addEventListener('click', function () {
                if (sw.disabled) return;
                swatchWrap.querySelectorAll('.swatch-rahsa').forEach(function (s) {
                    s.classList.remove('selected');
                    s.setAttribute('aria-checked', 'false');
                });
                sw.classList.add('selected');
                sw.setAttribute('aria-checked', 'true');

                if (nameEl) { nameEl.textContent = 'نسخه انتخاب‌شده: ' + (sw.dataset.name || ''); }

                const delta = parseFloat(sw.dataset.price || 0);
                if (priceEl && basePrice > 0) {
                    const newPrice = basePrice + (delta || 0);
                    priceEl.textContent = newPrice.toLocaleString('fa-IR') + ' تومان';
                }
            });
        });
    }

    // ---------------- Product Video Modal (گالری ویدئو) ----------------
    const videoModal = document.getElementById('product-video-modal');
    if (videoModal) {
        const frame = document.getElementById('product-video-frame');
        const openModal = function (embedUrl, title) {
            frame.innerHTML = '';
            const isFile = /\.(mp4|webm|ogg)(\?|$)/i.test(embedUrl);
            let el;
            if (isFile) {
                el = document.createElement('video');
                el.src = embedUrl; el.controls = true; el.autoplay = true;
            } else {
                el = document.createElement('iframe');
                el.src = embedUrl;
                el.title = title || 'ویدئو محصول';
                el.allow = 'accelerometer; autoplay; encrypted-media; picture-in-picture';
                el.allowFullscreen = true;
            }
            frame.appendChild(el);
            videoModal.hidden = false;
            document.body.style.overflow = 'hidden';
        };
        const closeModal = function () {
            videoModal.hidden = true;
            frame.innerHTML = '';
            document.body.style.overflow = '';
        };
        document.querySelectorAll('.video-thumb-rahsa').forEach(function (thumb) {
            thumb.addEventListener('click', function () {
                openModal(thumb.dataset.embed, thumb.dataset.title);
            });
        });
        const closeBtn = videoModal.querySelector('.video-modal-close');
        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        videoModal.addEventListener('click', function (e) { if (e.target === videoModal) closeModal(); });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !videoModal.hidden) closeModal();
        });
    }

    // ---------------- AJAX Product Filter (فیلتر ایجکسی) ----------------
    const filterBar = document.getElementById('products-filter-bar');
    if (filterBar) {
        const apiBase = filterBar.dataset.api;
        const categorySlug = filterBar.dataset.category;
        const grid = document.getElementById('products-grid');
        const emptyState = document.getElementById('products-empty-state');

        const esc = function (s) {
            const d = document.createElement('div');
            d.textContent = s == null ? '' : String(s);
            return d.innerHTML;
        };

        const renderCard = function (p) {
            const col = document.createElement('div');
            col.className = 'col-12 col-md-6 col-lg-4';

            // سواچ‌های رنگی نسخه‌ها روی کارت (الگوی قالب‌های فروشگاهی)
            let swatches = '';
            try {
                const vars = (typeof p.variations === 'string') ? JSON.parse(p.variations) : (p.variations || []);
                const colors = (vars || []).filter(function (v) { return v && v.type === 'color' && v.value; });
                if (colors.length) {
                    swatches = '<div class="card-swatch-row">' +
                        colors.slice(0, 5).map(function (v) {
                            return '<span class="card-swatch" title="' + esc(v.name || '') + '" style="background:' + esc(v.value) + ';' + (!v.stock ? 'opacity:0.35;' : '') + '"></span>';
                        }).join('') +
                        (colors.length > 5 ? '<span class="card-swatch-more">+' + (colors.length - 5) + '</span>' : '') +
                        '<span class="card-swatch-more">' + colors.length + ' رنگ</span>' +
                        '</div>';
                }
            } catch (e) { /* variations نبود یا خراب — بی‌صدا رد شو */ }

            col.innerHTML = '' +
                '<article class="product-card">' +
                '  <a href="' + esc(p.url) + '" class="product-card-link">' +
                '    <div class="product-card-image">' +
                '      <img src="' + esc(p.image || '/static/images/no-image.png') + '" alt="' + esc(p.title) + '" loading="lazy">' +
                (p.discount_percent ? '<span class="badge-rahsa gold">' + esc(p.discount_percent) + '٪ تخفیف</span>' : '') +
                '    </div>' +
                '    <div class="product-card-body">' +
                '      <h3 class="product-card-title">' + esc(p.title) + '</h3>' +
                swatches +
                '      <div class="product-card-price" data-persian-num>' +
                '        ' + (p.price ? parseInt(p.price, 10).toLocaleString('fa-IR') + ' تومان' : 'استعلام قیمت') +
                (p.old_price ? ' <s class="product-card-price-old">' + parseInt(p.old_price, 10).toLocaleString('fa-IR') + '</s>' : '') +
                '      </div>' +
                '      ' + (p.in_stock ? '' : '<span class="badge-rahsa muted">ناموجود</span>') +
                '    </div>' +
                '  </a>' +
                '</article>';
            return col;
        };

        const applyFilters = function (reset) {
            const params = new URLSearchParams();
            params.set('category', categorySlug);
            if (!reset) {
                const sort = document.getElementById('filter-sort');
                const minP = document.getElementById('filter-min-price');
                const maxP = document.getElementById('filter-max-price');
                const inStock = document.getElementById('filter-in-stock');
                const onSale = document.getElementById('filter-on-sale');
                if (sort && sort.value) params.set('sort', sort.value);
                if (minP && minP.value) params.set('min_price', minP.value);
                if (maxP && maxP.value) params.set('max_price', maxP.value);
                if (inStock && inStock.checked) params.set('in_stock', '1');
                if (onSale && onSale.checked) params.set('on_sale', '1');
            }

            filterBar.classList.add('loading');

            // آدرس مرورگر را هم سئو-پذیر بروزرسانی می‌کنیم (history — بدون رفرش)
            try { history.replaceState(null, '', '?' + params.toString()); } catch (e) { /* noop */ }

            fetch(apiBase + '?' + params.toString(), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    grid.querySelectorAll('.filter-product-item').forEach(function (el) { el.remove(); });
                    if (emptyState) { emptyState.remove(); }

                    if (data.items && data.items.length) {
                        data.items.forEach(function (p) { grid.appendChild(renderCard(p)); });
                    } else {
                        const empty = document.createElement('div');
                        empty.className = 'col-12';
                        empty.id = 'products-empty-state';
                        empty.innerHTML = '<div class="empty-state">' +
                            '<div class="empty-state-icon" aria-hidden="true">🔍</div>' +
                            '<h2 class="empty-state-title">نتیجه‌ای مطابق فیلترها یافت نشد</h2>' +
                            '<p class="empty-state-message">فیلترها را تغییر دهید یا حذف کنید.</p></div>';
                        grid.appendChild(empty);
                    }
                })
                .catch(function () { /* خطا → وضعیت قبلی می‌ماند */ })
                .finally(function () { filterBar.classList.remove('loading'); });
        };

        const applyBtn = document.getElementById('filter-apply');
        const resetBtn = document.getElementById('filter-reset');
        if (applyBtn) applyBtn.addEventListener('click', function () { applyFilters(false); });
        if (resetBtn) resetBtn.addEventListener('click', function () {
            ['filter-min-price', 'filter-max-price'].forEach(function (id) {
                const el = document.getElementById(id); if (el) el.value = '';
            });
            ['filter-in-stock', 'filter-on-sale'].forEach(function (id) {
                const el = document.getElementById(id); if (el) el.checked = false;
            });
            const sort = document.getElementById('filter-sort'); if (sort) sort.value = 'newest';
            applyFilters(true);
        });
    }
})();
