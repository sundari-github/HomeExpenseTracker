/** expenses.js - Expense Management Logic */

document.addEventListener('DOMContentLoaded', () => {
    // Basic elements
    const expenseTableBody = document.getElementById('expenseTableBody');
    const expenseLoader = document.getElementById('expenseLoader');
    const expenseEmptyState = document.getElementById('expenseEmptyState');
    const expenseTableContainer = document.getElementById('expenseTableContainer');

    // Forms
    const addExpenseForm = document.getElementById('addExpenseForm');
    const filterDateForm = document.getElementById('filterDateForm');
    const filterCategoryForm = document.getElementById('filterCategoryForm');

    // Modals
    const editExpenseModal = document.getElementById('editExpenseModal');
    const updateExpenseForm = document.getElementById('updateExpenseForm');
    const cancelUpdateExpBtn = document.getElementById('cancelUpdateExpBtn');

    // Filter Tabs
    const filterBtnAll = document.getElementById('filterBtnAll');
    const filterBtnDate = document.getElementById('filterBtnDate');
    const filterBtnCategory = document.getElementById('filterBtnCategory');

    // Base API URL
    const API_BASE = 'https://home-expense-tracker-api.onrender.com';

    // 1. Core API Fetcher for Expenses
    async function fetchExpenses(endpoint, method = 'GET', body = null) {
        if (!checkAuth()) return null;

        const token = localStorage.getItem('authToken');
        const options = {
            method,
            headers: { 'Authorization': `Bearer ${token}` }
        };

        if (body) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }

        try {
            expenseTableContainer.style.display = 'none';
            expenseEmptyState.style.display = 'none';
            expenseLoader.style.display = 'flex';

            const response = await fetch(`${API_BASE}${endpoint}`, options);

            if (response.status === 401) {
                window.location.href = 'index.html';
                return null;
            }

            if (response.status === 204) {
                // No Content found
                showEmptyState();
                return [];
            }

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || 'Failed to fetch expenses');
            }

            const data = await response.json();

            // Render the data
            if (data && data.length > 0) {
                renderExpenseTable(data);
            } else {
                showEmptyState();
            }

            return data;
        } catch (error) {
            console.error('Expense API Error:', error);
            showToast(error.message, 'error');
            showEmptyState();
            return null;
        } finally {
            expenseLoader.style.display = 'none';
        }
    }

    // 2. Rendering Table & States
    function showEmptyState() {
        expenseEmptyState.style.display = 'block';
        expenseTableContainer.style.display = 'none';
    }

    function renderExpenseTable(expenses) {
        expenseTableBody.innerHTML = '';
        expenses.forEach(exp => {
            const tr = document.createElement('tr');

            // Date formatting
            const dateStr = exp.PurchaseDate ? exp.PurchaseDate : exp.Date; // Fallback

            tr.innerHTML = `
                <td>${dateStr}</td>
                <td>${exp.Store}</td>
                <td class="font-medium">$${parseFloat(exp.Amount).toFixed(2)}</td>
                <td>${exp.Card}</td>
                <td class="actions">
                    <button class="btn-icon edit-exp-btn" title="Edit" 
                        data-date="${dateStr}" 
                        data-store="${exp.Store}" 
                        data-amount="${exp.Amount}" 
                        data-card="${exp.Card}"
                        onclick="window.editExpenseRow(this, event)">
                        <i data-lucide="edit-2"></i>
                    </button>
                    <button class="btn-icon danger delete-exp-btn" title="Delete"
                        data-date="${dateStr}" 
                        data-store="${exp.Store}"
                        onclick="window.deleteExpenseRow(this, event)">
                        <i data-lucide="trash-2"></i>
                    </button>
                </td>
            `;
            expenseTableBody.appendChild(tr);
        });

        // Re-init newly created lucide icons
        lucide.createIcons();

        expenseEmptyState.style.display = 'none';
        expenseTableContainer.style.display = 'block';
    }

    // Filter Modals
    const filterDateModal = document.getElementById('filterDateModal');
    const filterCategoryModal = document.getElementById('filterCategoryModal');

    // Close Filter Modals
    document.querySelectorAll('.cancel-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const modalId = btn.getAttribute('data-modal');
            if (modalId) {
                document.getElementById(modalId).style.display = 'none';
            }
        });
    });

    // 3. Tab Toggling Logic
    function switchFilterTab(activeBtn) {
        if (activeBtn === filterBtnAll) {
            [filterBtnAll, filterBtnDate, filterBtnCategory].forEach(btn => btn.classList.remove('active-filter'));
            activeBtn.classList.add('active-filter');
            fetchExpenses('/expense/getAllExpenses');
        } else if (activeBtn === filterBtnDate) {
            filterDateModal.style.display = 'flex';
        } else if (activeBtn === filterBtnCategory) {
            filterCategoryModal.style.display = 'flex';
        }
    }

    if (filterBtnAll) filterBtnAll.addEventListener('click', () => switchFilterTab(filterBtnAll));
    if (filterBtnDate) filterBtnDate.addEventListener('click', () => switchFilterTab(filterBtnDate));
    if (filterBtnCategory) filterBtnCategory.addEventListener('click', () => switchFilterTab(filterBtnCategory));

    // 4. Form Submissions

    // Add Expense
    if (addExpenseForm) {
        addExpenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('addExpenseBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = `<span class="spinner" style="display:inline-block; border-color:white; border-left-color:transparent; width:16px; height:16px;"></span> Saving...`;
            btn.disabled = true;

            const payload = {
                PurchaseDate: document.getElementById('expDate').value,
                Amount: parseFloat(document.getElementById('expAmount').value),
                Store: document.getElementById('expStore').value,
                Card: document.getElementById('expCard').value
            };

            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE}/expense/addExpense`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (response.status === 401) return window.location.href = 'index.html';

                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || 'Failed to add expense');
                }

                showToast('Expense added successfully!', 'success');
                addExpenseForm.reset();

                // Refresh table and force switch to "All" filter
                switchFilterTab(filterBtnAll);

            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // Filter By Date (Modal)
    const filterDateFormModal = document.getElementById('filterDateFormModal');
    if (filterDateFormModal) {
        filterDateFormModal.addEventListener('submit', (e) => {
            e.preventDefault();
            const start = document.getElementById('filterStartDate').value;
            const end = document.getElementById('filterEndDate').value;

            [filterBtnAll, filterBtnDate, filterBtnCategory].forEach(btn => btn.classList.remove('active-filter'));
            filterBtnDate.classList.add('active-filter');
            filterDateModal.style.display = 'none';

            fetchExpenses(`/expense/getExpensesByDate/${start}/${end}`);
        });
    }

    // Filter By Category (Modal)
    const filterCategoryFormModal = document.getElementById('filterCategoryFormModal');
    if (filterCategoryFormModal) {
        filterCategoryFormModal.addEventListener('submit', (e) => {
            e.preventDefault();
            const categoryName = document.getElementById('filterCategoryName').value;
            const categoryValue = document.getElementById('filterCategoryValue').value;

            [filterBtnAll, filterBtnDate, filterBtnCategory].forEach(btn => btn.classList.remove('active-filter'));
            filterBtnCategory.classList.add('active-filter');
            filterCategoryModal.style.display = 'none';

            const params = new URLSearchParams({
                category_name: categoryName,
                category_value: categoryValue
            });

            fetchExpenses(`/expense/getExpenses?${params.toString()}`);
        });
    }

    // Custom Delete Modal Handlers
    const deleteConfirmModal = document.getElementById('deleteConfirmModal');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', () => {
            deleteConfirmModal.style.display = 'none';
            window.expenseToDeleteStore = null;
            window.expenseToDeleteDate = null;
        });
    }

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            const store = window.expenseToDeleteStore;
            const date = window.expenseToDeleteDate;

            if (!store || !date) return;

            try {
                confirmDeleteBtn.disabled = true;
                confirmDeleteBtn.innerHTML = `<span class="spinner" style="display:inline-block; border-color:white; border-left-color:transparent; width:14px; height:14px;"></span>`;

                const token = localStorage.getItem('authToken');
                const url = `${API_BASE}/expense/deleteExpense/${encodeURIComponent(store)}/${encodeURIComponent(date)}`;

                const response = await fetch(url, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.status === 401) return window.location.href = 'index.html';

                if (!response.ok) {
                    let errorMsg = 'Failed to delete expense';
                    if (response.status === 404) {
                        errorMsg = 'Expense not found on server.';
                    } else if (response.status === 422) {
                        errorMsg = 'Invalid date format sent to server.';
                    } else {
                        const data = await response.json().catch(() => ({}));
                        if (data.detail && typeof data.detail === 'string') {
                            errorMsg = data.detail;
                        }
                    }
                    throw new Error(errorMsg);
                }

                showToast('Expense deleted successfully!', 'success');
                deleteConfirmModal.style.display = 'none';
                refreshActiveView();

            } catch (error) {
                console.error("Delete Expense Error: ", error);
                showToast(error.message, 'error');
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.innerHTML = 'Delete';
            }
        });
    }

    // Modal Close
    if (cancelUpdateExpBtn) {
        cancelUpdateExpBtn.addEventListener('click', () => {
            editExpenseModal.style.display = 'none';
        });
    }

    // Modal Submit Update (PUT)
    if (updateExpenseForm) {
        updateExpenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('saveUpdateExpBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = `Updating...`;
            btn.disabled = true;

            const payload = {
                PurchaseDate: document.getElementById('editExpDate').value,
                Store: document.getElementById('editExpStore').value,
                Amount: parseFloat(document.getElementById('editExpAmount').value),
                Card: document.getElementById('editExpCard').value
            };

            try {
                const token = localStorage.getItem('authToken');
                const response = await fetch(`${API_BASE}/expense/updateExpense`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (response.status === 401) return window.location.href = 'index.html';

                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || 'Failed to update expense');
                }

                showToast('Expense updated successfully!', 'success');
                editExpenseModal.style.display = 'none';

                // Resubmit active filter to refresh
                refreshActiveView();

            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    function refreshActiveView() {
        if (filterBtnAll.classList.contains('active-filter')) {
            fetchExpenses('/expense/getAllExpenses');
        } else if (filterBtnDate.classList.contains('active-filter')) {
            const start = document.getElementById('filterStartDate').value;
            const end = document.getElementById('filterEndDate').value;
            if (start && end) fetchExpenses(`/expense/getExpensesByDate/${start}/${end}`);
        } else if (filterBtnCategory.classList.contains('active-filter')) {
            const catName = document.getElementById('filterCategoryName').value;
            const catVal = document.getElementById('filterCategoryValue').value;
            if (catVal) fetchExpenses(`/expense/getExpenses?category_name=${catName}&category_value=${catVal}`);
        }
    }

    // Setup initial view hook via custom event or observer if needed, 
    // but the safest approach is to hijack the nav-link click for Expense Management
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            if (link.dataset.view === 'expense-management') {
                // When navigating to expenses, load "All" by default
                switchFilterTab(filterBtnAll);
            }
        });
    });

});

// 5. Update & Delete Action Handlers (Global Inline Binding - Moved Outside DOMContentLoaded)
window.editExpenseRow = function (btn, event) {
    if (event) event.preventDefault();

    const { date, store, amount, card } = btn.dataset;
    document.getElementById('editExpDate').value = date;
    document.getElementById('editExpStore').value = store;
    document.getElementById('editExpAmount').value = amount;
    document.getElementById('editExpCard').value = card;
    document.getElementById('editExpenseModal').style.display = 'flex';
};

window.deleteExpenseRow = function (btn, event) {
    if (event) event.preventDefault();

    // Stop event bubbling in case icons swallow the click
    if (event) event.stopPropagation();

    const { date, store } = btn.dataset;

    console.log("Delete triggered globally for:", store, date);

    // Store target globally for the modal to use
    window.expenseToDeleteStore = store;
    window.expenseToDeleteDate = date;

    document.getElementById('deleteConfirmText').textContent = `Are you sure you want to delete the expense at ${store} on ${date}?`;
    document.getElementById('deleteConfirmModal').style.display = 'flex';

    // Reset modal button state in case of previous errors
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    confirmBtn.disabled = false;
    confirmBtn.innerHTML = 'Delete';
};
