#!/usr/bin/env python3
"""
Auto-fix remaining admin/user templates:
- Replace Bootstrap classes with our CSS classes
- Remove inline light-theme styles
- Add proper semantic structure
"""
import os
import re
from pathlib import Path

REPO = Path(__file__).parent.parent

# Mapping of Bootstrap/unused classes to our classes
CLASS_REPLACEMENTS = [
    # Buttons
    (r'class="btn btn-primary([^"]*)"', r'class="btn-rahsa-cta\1"'),
    (r'class="btn btn-outline-primary([^"]*)"', r'class="btn-rahsa-outline\1"'),
    (r'class="btn btn-outline-secondary([^"]*)"', r'class="btn-rahsa-outline\1"'),
    (r'class="btn btn-danger([^"]*)"', r'class="btn-rahsa-danger\1"'),
    (r'class="btn btn-success([^"]*)"', r'class="btn-rahsa-success\1"'),
    (r'class="btn btn-lg w-100"', r'class="btn-rahsa-cta w-100"'),
    # Form controls
    (r'class="form-control([^"]*)"', r'class="form-control-rahsa\1"'),
    (r'class="form-select([^"]*)"', r'class="form-select-rahsa\1"'),
    (r'class="form-label"', r'class="form-label-rahsa"'),
    # Alerts
    (r'class="alert alert-(\w+)([^"]*)"',
     lambda m: f'class="flash-message {m.group(1) if m.group(1) != "error" else "danger"}{m.group(2)}"'),
    # Badges
    (r'class="badge bg-(\w+)"', r'class="badge-rahsa \1"'),
    # Cards
    (r'class="card([^"]*)" style="background:#fff; border-radius:1rem; padding:1\.5rem; border:1px solid #e2e8f0;"',
     r'class="glass-card\1" style="padding:1.5rem;"'),
    # Bg-light
    (r'class="bg-light"', r''),
    # Text-right rtl redundancy
    (r' class="text-right rtl"', r''),
    # Fix: 'text-center' typo (common)
    (r' text-center;', r' text-align:center;'),
]

# Inline style replacements: light theme -> dark theme
STYLE_REPLACEMENTS = [
    # Card background light -> dark glass
    (
        r'style="background:#fff; border-radius:1rem; padding:1\.5rem; border:1px solid #e2e8f0; box-shadow:0 4px 6px -1px rgba\(0,0,0,0\.05\);"',
        'style="padding:1.5rem;" class="glass-card"'
    ),
    (
        r'style="background:#fff; border-radius:1rem; padding:2rem; border:1px solid #e2e8f0; max-width:(\d+)px; margin:0 auto; box-shadow:0 4px 6px -1px rgba\(0,0,0,0\.05\);"',
        r'style="padding:2rem; max-width:\1px; margin:0 auto;" class="glass-card"'
    ),
    (
        r'style="background:#fff; border-radius:1rem; padding:2\.5rem; border:1px solid #e2e8f0; max-width:900px; margin:0 auto;"',
        'style="padding:2.5rem; max-width:900px; margin:0 auto;" class="glass-card"'
    ),
    (
        r'style="background:#fff; border-radius:1rem; padding:1\.5rem; border:1px solid #e2e8f0; border-right:4px solid #(\w+);"',
        r'class="stat-card" style="padding:1.5rem;"'
    ),
    # Body bg-light
    (
        r'<body class="bg-light">',
        '<body>'
    ),
    # Logo badge style
    (
        r'class="logo-badge"',
        'class="brand-badge-rahsa"'
    ),
]

# Color replacements: #0f172a (dark slate) is fine in dark theme, but
# #2563eb (blue) and #64748b (slate) need to map to gold
COLOR_REPLACEMENTS = [
    # Headings: #0f172a -> #ffffff
    (r'color:#0f172a', r'color:var(--text-white)'),
    # Primary blue: #2563eb -> gold
    (r'color:#2563eb', r'color:var(--accent-gold)'),
    (r'color:#1e3a8a', r'color:var(--accent-gold)'),
    (r'color:#1e293b', r'color:var(--text-gray-200)'),
    (r'color:#92400e', r'color:var(--accent-gold)'),
    (r'color:#065f46', r'color:var(--accent-success)'),
    (r'color:#166534', r'color:var(--accent-success)'),
    (r'color:#991b1b', r'color:var(--accent-danger)'),
    # Borders
    (r'border:1px solid #e2e8f0', r'border:1px solid var(--glass-border)'),
    (r'border-bottom:1px solid #e2e8f0', r'border-bottom:1px solid var(--glass-border)'),
    (r'border-bottom:1px solid #f1f5f9', r'border-bottom:1px solid var(--glass-border)'),
    (r'border-right:4px solid #2563eb', r''),
    (r'border-right:4px solid #10b981', r''),
    (r'border-right:4px solid #f59e0b', r''),
    (r'border-right:4px solid #06b6d4', r''),
    (r'border-right:4px solid #64748b', r''),
    (r'border-bottom:2px solid #e2e8f0', r'border-bottom:2px solid var(--glass-border)'),
    (r'background:#f8fafc', r'background:var(--bg-navy-elevated)'),
    (r'background:#eff6ff', r'background:rgba\(251,176,59,0.08\)'),
    (r'background:#ecfdf5', r'background:rgba\(16,185,129,0.08\)'),
    (r'background:#fef3c7', r'background:rgba\(245,158,11,0.08\)'),
    (r'background:#f1f5f9', r'background:var(--bg-navy-elevated)'),
    (r'background:#dcfce7', r'background:rgba\(16,185,129,0.2\)'),
    (r'background:#fee2e2', r'background:rgba\(239,68,68,0.2\)'),
    # Text colors
    (r'color:#475569', r'color:var(--text-gray-400)'),
    (r'color:#334155', r'color:var(--text-gray-200)'),
    (r'color:#64748b', r'color:var(--text-gray-400)'),
    (r'color:#94a3b8', r'color:var(--text-gray-400)'),
    (r'color:#cbd5e1', r'color:var(--text-gray-300)'),
    (r'color:#e2e8f0', r'color:var(--text-gray-200)'),
    # Table headers background
    (r'background:#fff;', r'background:var(--bg-navy-card);'),
]

# Invalid Tailwind classes (project has no Tailwind)
TAILWIND_REPLACEMENTS = [
    (r'\bmin-h-\[\d+vh\]', r'class-min-h'),
    (r'\bgrid-bg\b', r''),
    (r'\banimate-pulse\b', r''),
    (r'\btext-center\b(?=[ "\'])', r''),
]


def fix_file(path: Path) -> tuple[bool, int]:
    """Apply all replacements to a file. Returns (changed, num_replacements)."""
    try:
        original = path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, FileNotFoundError):
        return False, 0

    content = original
    n = 0

    for pattern, replacement in CLASS_REPLACEMENTS + STYLE_REPLACEMENTS + COLOR_REPLACEMENTS + TAILWIND_REPLACEMENTS:
        if callable(replacement):
            new_content, count = re.subn(pattern, replacement, content)
        else:
            new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            content = new_content
            n += count

    if content != original:
        path.write_text(content, encoding='utf-8')
        return True, n
    return False, 0


def main():
    templates_dir = REPO / 'app' / 'templates'
    fixed_count = 0
    total_replacements = 0

    for path in sorted(templates_dir.rglob('*.html')):
        changed, n = fix_file(path)
        if changed:
            print(f"  ✓ {path.relative_to(REPO)}: {n} replacements")
            fixed_count += 1
            total_replacements += n

    print(f"\n✅ Fixed {fixed_count} files, {total_replacements} total replacements")


if __name__ == '__main__':
    main()
