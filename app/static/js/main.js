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
