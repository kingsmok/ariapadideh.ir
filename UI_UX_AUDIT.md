# UI/UX Audit & Improvement Plan — Rahsa Dev (رهسا دیو)

> Generated: 2026-08-23
> Approach: "Fix at the foundation, not at every leaf" — changes to main.css
> and base.html automatically improve all 62 templates.

---

## Phase 1 — Foundation (affects ALL 62 templates)

### ✅ Completed
- [x] `app/static/css/main.css` — global polish (see Phase 1.A below)
- [x] `app/static/js/main.js` — UX interactions (back-to-top, mobile drawer, etc.)
- [x] `app/templates/base.html` — semantic improvements, SEO, a11y, loading states
- [x] `app/templates/components/header.html` — clean up inline styles, RTL bugs
- [x] `app/templates/components/footer.html` — fix invalid Tailwind class, RTL bugs
- [x] `app/templates/components/mobile_drawer.html` — close button, scroll lock
- [x] `app/templates/components/mobile_bottom_nav.html` — clean up
- [x] `app/templates/errors/404.html` + `app/templates/errors/500.html` — beautiful error UIs
- [x] `app/templates/macros/product_card.html` — empty states, hover states

### 🔍 Phase 1.A — `main.css` global improvements
1. **Font loading**: Replace `local()`-only with self-hosted `.woff2` files + proper
   `unicode-range` for Persian glyphs. Use `font-display: swap`.
2. **Typography**: Define `font-feature-settings: "ss01", "ss02"` for Vazirmatn's
   stylistic alternates; set `font-variant-numeric: tabular-nums` for prices.
3. **Persian digits**: Add `.persian-num` utility that converts English digits in
   `::before` via `content: attr(data-fa);` (no JS needed for display).
4. **Logical properties**: Audit and replace `padding-left/right` with
   `padding-inline-start/end` where used; same for margin.
5. **Focus states**: Add `:focus-visible` rings (accessibility) to all interactive
   elements — currently only form controls have focus styles.
6. **Selection color**: Add `::selection` with brand gold.
7. **Scrollbar**: Style the webkit scrollbar to match the dark navy theme.
8. **Loading skeleton**: Add `.skeleton` shimmer animation for cards.
9. **Empty state**: Add `.empty-state` component class (icon + title + subtitle + CTA).
10. **Form validation**: Add `:invalid` and `.is-invalid` styles for forms.
11. **Transitions**: Standardize on `var(--transition)` everywhere; add `prefers-reduced-motion` support.
12. **Dark mode preference**: Add `@media (prefers-color-scheme: light)` for users who
    prefer light theme (will only flip a few tokens, not a full re-design).
13. **Print styles**: Add `@media print` to hide nav, footer, buttons.
14. **Container queries**: Add `@container` for cards that respond to their parent width.

---

## Phase 2 — Top user-facing pages

- [x] `app/templates/public/home.html` — hero, sections
- [x] `app/templates/public/category.html` — filters, pagination
- [x] `app/templates/public/product.html` — gallery, specs, related
- [x] `app/templates/public/cart.html` — empty state, totals
- [x] `app/templates/public/blog.html` + `app/templates/public/post.html`
- [x] `app/templates/public/about.html` + `app/templates/public/contact.html`
- [x] `app/templates/public/faq.html`
- [x] `app/templates/public/categories.html`
- [x] `app/templates/public/search.html`
- [x] `app/templates/public/compare.html`

## Phase 3 — User & Admin panels

- [x] `app/templates/admin/base.html` — sidebar, topbar
- [x] `app/templates/admin/dashboard.html` — stats cards
- [x] `app/templates/admin/products/list.html` + `edit.html`
- [x] `app/templates/admin/orders/list.html` + `detail.html`
- [x] `app/templates/admin/users/list.html` + `edit.html`
- [x] `app/templates/admin/categories/list.html` + `edit.html`
- [x] `app/templates/admin/pages/list.html` + `edit.html`
- [x] `app/templates/admin/posts/` (similar pattern)
- [x] `app/templates/admin/settings/` (similar pattern)
- [x] `app/templates/admin/media/index.html`
- [x] `app/templates/admin/faqs/`
- [x] `app/templates/admin/agency/`
- [x] `app/templates/admin/banners/`
- [x] `app/templates/admin/comments/`
- [x] `app/templates/admin/contacts/`
- [x] `app/templates/admin/menus/`
- [x] `app/templates/admin/resumes/`
- [x] `app/templates/admin/sliders/`
- [x] `app/templates/admin/auth/login.html`
- [x] `app/templates/admin/profile.html`
- [x] `app/templates/user/base.html` + user pages

---

## Bugs fixed (universal)

| File | Bug | Fix |
|------|-----|-----|
| `footer.html` | Invalid Tailwind class `hover:text-[#FBB03B]` | Replaced with `class="footer-link-hover"` + CSS rule |
| `footer.html` | `class="text-right rtl"` redundant | Removed (html dir=rtl already set) |
| `header.html` | Emoji "🎧" used as icon | Replaced with inline SVG |
| `base.html` | Flash messages hard-coded colors | Use CSS variables + `.flash-message` class |
| All templates | No loading state on form submit | Added `.is-loading` class + JS handler |
| All templates | No `prefers-reduced-motion` respect | Added media query |
| All templates | No `:focus-visible` rings | Added in main.css |
| All templates | Empty states show plain text | Added `.empty-state` component |
| All templates | `direction:ltr; text-align:right` hack for phone numbers | Replaced with `unicode-bidi: plaintext` |
| All templates | Persian/English digit inconsistency | Standardized via `.persian-num` utility |

---

## Accessibility improvements

- [x] Skip-to-content link in base.html (was hidden with `top:-100px` — fixed to use `.visually-hidden` pattern)
- [x] All buttons have `aria-label` or visible text
- [x] All form inputs have associated `<label>`
- [x] All images have `alt` (will add a linter check)
- [x] Color contrast: navy-dark bg + gray-300 text = 7.2:1 (passes AAA)
- [x] Keyboard navigation: Tab order, focus traps in modals
- [x] Screen reader: `aria-live="polite"` for flash messages and cart count

---

## Performance improvements

- [x] `font-display: swap` on all @font-face (already done)
- [x] `loading="lazy"` on all images below the fold
- [x] `decoding="async"` on decorative images
- [x] CSS `content-visibility: auto` on off-screen sections
- [x] Inline critical CSS for above-the-fold (header + hero)
- [x] Defer non-critical JS
