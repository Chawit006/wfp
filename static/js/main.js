/* ============================================================
   E-Sports Manager — Main JavaScript
   CS104 Introduction to Database
   ============================================================ */

/**
 * Confirm delete dialogs.
 * Called from inline onsubmit="return confirmDelete('...')" on delete forms.
 */
function confirmDelete(itemName) {
    return confirm(`Are you sure you want to delete "${itemName}"?\n\nThis action cannot be undone.`);
}

document.addEventListener('DOMContentLoaded', function () {

    // ------------------------------------------------------------------
    // Auto-hide flash messages after 4 seconds
    // ------------------------------------------------------------------
    const alerts = document.querySelectorAll('.flash-message');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(function () {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 500);
        }, 4000);
    });

    // ------------------------------------------------------------------
    // Search input — debounce 500 ms then submit form automatically
    // ------------------------------------------------------------------
    var searchInput = document.getElementById('search');
    if (searchInput) {
        var debounceTimer;
        searchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            var form = this.closest('form');
            if (form) {
                debounceTimer = setTimeout(function () {
                    form.submit();
                }, 500);
            }
        });
    }

    // ------------------------------------------------------------------
    // Highlight the active sidebar link based on current URL path
    // (Jinja2 also handles this server-side; this is a client-side fallback)
    // ------------------------------------------------------------------
    var currentPath = window.location.pathname;
    var navLinks = document.querySelectorAll('.sidebar-link');
    navLinks.forEach(function (link) {
        var href = link.getAttribute('href');
        if (href && href !== '/' && currentPath.startsWith(href)) {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });

    // ------------------------------------------------------------------
    // Prize pool / salary formatting hint on blur
    // ------------------------------------------------------------------
    var moneyInputs = document.querySelectorAll('input[name="prize_pool"], input[name="salary"]');
    moneyInputs.forEach(function (input) {
        input.addEventListener('blur', function () {
            var val = parseFloat(this.value);
            if (!isNaN(val)) {
                this.value = val.toFixed(2);
            }
        });
    });

    // ------------------------------------------------------------------
    // KDA formatting hint on blur
    // ------------------------------------------------------------------
    var kdaInput = document.querySelector('input[name="kda"]');
    if (kdaInput) {
        kdaInput.addEventListener('blur', function () {
            var val = parseFloat(this.value);
            if (!isNaN(val)) {
                this.value = val.toFixed(2);
            }
        });
    }

    // ------------------------------------------------------------------
    // End date must not be before start date (client-side hint)
    // ------------------------------------------------------------------
    var startDate = document.getElementById('start_date');
    var endDate   = document.getElementById('end_date');
    if (startDate && endDate) {
        startDate.addEventListener('change', function () {
            if (endDate.value && endDate.value < startDate.value) {
                endDate.value = startDate.value;
            }
            endDate.min = startDate.value;
        });
        // Set initial min
        if (startDate.value) {
            endDate.min = startDate.value;
        }
    }

    // ------------------------------------------------------------------
    // Table row click → navigate to edit page (optional UX enhancement)
    // Rows with data-href attribute become clickable
    // ------------------------------------------------------------------
    var clickableRows = document.querySelectorAll('tr[data-href]');
    clickableRows.forEach(function (row) {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function (e) {
            // Don't navigate if user clicked a button or link inside the row
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' ||
                e.target.closest('a') || e.target.closest('button') ||
                e.target.closest('form')) {
                return;
            }
            window.location.href = row.getAttribute('data-href');
        });
    });

});
