// ExpenseTrack main JavaScript

document.addEventListener("DOMContentLoaded", function () {
    // Enable Bootstrap tooltips if any
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto close flash alerts after 6 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 6000);
    });

    // Transaction form: filter categories by selected type (income/expense)
    const typeSelect = document.getElementById("type");
    const categorySelect = document.getElementById("category_id");

    if (typeSelect && categorySelect) {
        function filterCategories() {
            const selectedType = typeSelect.value;
            const options = categorySelect.querySelectorAll("option");
            let firstVisible = null;

            options.forEach(function (opt) {
                const text = opt.textContent;
                // Category options format: "Name (income)" or "Name (expense)"
                if (text.includes(`(${selectedType})`)) {
                    opt.style.display = "";
                    if (!firstVisible) firstVisible = opt;
                } else if (opt.value === "" || opt.value === "0") {
                    opt.style.display = "";
                } else {
                    opt.style.display = "none";
                }
            });

            // If current selected category doesn't match type, switch to first visible
            const currentSelected = categorySelect.querySelector(`option[value="${categorySelect.value}"]`);
            if (currentSelected && currentSelected.style.display === "none" && firstVisible) {
                categorySelect.value = firstVisible.value;
            }
        }

        typeSelect.addEventListener("change", filterCategories);
        filterCategories();
    }
});
