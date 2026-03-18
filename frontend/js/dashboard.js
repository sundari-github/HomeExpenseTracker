/** dashboard.js - Dashboard & User Management Logic */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initial Setup and Routing Simulation
    const navLinks = document.querySelectorAll('.nav-link');
    const viewSections = document.querySelectorAll('.view-section');

    function switchView(viewId) {
        // Update navigation
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.dataset.view === viewId) {
                link.classList.add('active');
            }
        });

        // Show/hide sections
        viewSections.forEach(section => {
            if (section.id === `view-${viewId}`) {
                section.style.display = 'block';
                // Trigger any specific data loading if necessary
                if (viewId === 'user-management') {
                    loadCurrentUser();
                }
            } else {
                section.style.display = 'none';
            }
        });

        // On mobile, close sidebar after clicking
        const sidebar = document.getElementById('sidebar');
        if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
        }
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const viewId = link.dataset.view;
            if (viewId) switchView(viewId);
        });
    });

    // 2. User Management Functionality

    // Elements
    const currentUserLoader = document.getElementById('currentUserLoader');
    const currentUserContent = document.getElementById('currentUserContent');
    const displayUsername = document.getElementById('displayUsername');
    const displayEmail = document.getElementById('displayEmail');
    const displayFirstName = document.getElementById('displayFirstName');

    const editProfileBtn = document.getElementById('editProfileBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    const modifyUserCard = document.getElementById('modifyUserCard');
    const modifyUserForm = document.getElementById('modifyUserForm');

    const createUserForm = document.getElementById('createUserForm');

    const changePasswordToggleBtn = document.getElementById('changePasswordToggleBtn');
    const cancelPasswordBtn = document.getElementById('cancelPasswordBtn');
    const changePasswordCard = document.getElementById('changePasswordCard');
    const changePasswordForm = document.getElementById('changePasswordForm');

    let currentUserData = null;

    // A. Load Current User
    async function loadCurrentUser() {
        if (!checkAuth()) return;

        currentUserLoader.style.display = 'flex';
        currentUserContent.style.display = 'none';

        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/users/getUserDetails`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                localStorage.removeItem('authToken');
                window.location.href = 'index.html';
                return;
            }

            if (!response.ok) {
                throw new Error('Failed to fetch user details');
            }

            const userData = await response.json();
            currentUserData = userData;

            // Populate UI with PascalCase keys from backend Model
            displayUsername.textContent = userData.UserName || '-';
            displayEmail.textContent = userData.EmailAddress || '-';
            displayFirstName.textContent = userData.FirstName || '-';

            // Show content
            currentUserLoader.style.display = 'none';
            currentUserContent.style.display = 'block';

            // Check admin role to show Create New User form
            const createUserCard = document.getElementById('createUserCard');
            if (createUserCard) {
                if (userData.UserName === 'admin') {
                    createUserCard.style.display = 'block';
                } else {
                    createUserCard.style.display = 'none';
                }
            }

        } catch (error) {
            console.error('Error fetching user:', error);
            showToast(error.message, 'error');
            currentUserLoader.style.display = 'none';
            displayUsername.textContent = 'Error loading user';
            currentUserContent.style.display = 'block';
        }
    }

    // Toggle Edit Profile Form
    if (editProfileBtn && modifyUserCard) {
        editProfileBtn.addEventListener('click', () => {
            // Pre-fill form
            if (currentUserData) {
                document.getElementById('modFirstName').value = currentUserData.FirstName || '';
                document.getElementById('modEmail').value = currentUserData.EmailAddress || '';
            }
            modifyUserCard.style.display = 'block';
            modifyUserCard.scrollIntoView({ behavior: 'smooth' });
        });
    }

    if (cancelEditBtn && modifyUserCard) {
        cancelEditBtn.addEventListener('click', () => {
            modifyUserCard.style.display = 'none';
        });
    }

    // Toggle Change Password Form
    if (changePasswordToggleBtn && changePasswordCard) {
        changePasswordToggleBtn.addEventListener('click', () => {
            changePasswordForm.reset();
            changePasswordCard.style.display = 'block';
            changePasswordCard.scrollIntoView({ behavior: 'smooth' });
        });
    }

    if (cancelPasswordBtn && changePasswordCard) {
        cancelPasswordBtn.addEventListener('click', () => {
            changePasswordCard.style.display = 'none';
        });
    }

    // B. Modify User Details
    if (modifyUserForm) {
        modifyUserForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const btn = document.getElementById('saveProfileBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = `<span class="spinner" style="display:inline-block; border-color:white; border-left-color:transparent; width:16px; height:16px;"></span> Saving...`;
            btn.disabled = true;

            try {
                const token = localStorage.getItem('authToken');
                const firstName = document.getElementById('modFirstName').value;
                const email = document.getElementById('modEmail').value;

                // Backend expects PUT with query parameters
                const queryParams = new URLSearchParams();
                if (firstName) queryParams.append('first_name', firstName);
                if (email) queryParams.append('email_addr', email);

                const response = await fetch(`${API_BASE_URL}/users/modifyUserDetails?${queryParams.toString()}`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.status === 401) {
                    window.location.href = 'index.html';
                    return;
                }

                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || 'Failed to update profile');
                }

                showToast('Profile updated successfully!', 'success');
                modifyUserCard.style.display = 'none';

                // Reload user data to show changes
                loadCurrentUser();

            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // C. Change User Password
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const btn = document.getElementById('savePasswordBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = `<span class="spinner" style="display:inline-block; border-color:white; border-left-color:transparent; width:16px; height:16px;"></span> Saving...`;
            btn.disabled = true;

            try {
                const token = localStorage.getItem('authToken');
                const oldPassword = document.getElementById('oldPassword').value;
                const newPassword = document.getElementById('newPasswordChange').value;

                // Backend expects POST with query parameters
                const queryParams = new URLSearchParams();
                queryParams.append('old_password', oldPassword);
                queryParams.append('new_password', newPassword);

                const response = await fetch(`${API_BASE_URL}/users/changeUserPassword?${queryParams.toString()}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.status === 401) {
                    const data = await response.json().catch(() => ({}));
                    // The backend returns 401 for both invalid token and wrong old password
                    // If the detail says "Invalid User" or "Old Password does not match", we shouldn't redirect
                    if (data.detail && data.detail.includes("Old Password")) {
                        throw new Error(data.detail);
                    } else if (data.detail === "Invalid User") {
                        throw new Error("Invalid User");
                    } else {
                        // Otherwise it's probably actual unauth, let's redirect
                        window.location.href = 'index.html';
                        return;
                    }
                }

                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || 'Failed to change password');
                }

                showToast('Password changed successfully!', 'success');
                changePasswordCard.style.display = 'none';
                changePasswordForm.reset();

            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // D. Create New User
    if (createUserForm) {
        createUserForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const btn = document.getElementById('createUserBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = `<span class="spinner" style="display:inline-block; border-color:white; border-left-color:transparent; width:16px; height:16px;"></span> Creating...`;
            btn.disabled = true;

            try {
                const token = localStorage.getItem('authToken');

                // Backend UserInput model expects specific PascalCase keys
                const payload = {
                    FirstName: document.getElementById('newFirstName').value,
                    EmailAddress: document.getElementById('newEmail').value,
                    UserName: document.getElementById('newUsername').value,
                    Password: document.getElementById('newPassword').value
                };

                const response = await fetch(`${API_BASE_URL}/users/createUser`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (response.status === 401) {
                    window.location.href = 'index.html';
                    return;
                }

                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || 'Failed to create user');
                }

                showToast(`User ${payload.username} created successfully!`, 'success');
                createUserForm.reset();

            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // Initialize Active View
    const activeLink = document.querySelector('.nav-link.active');
    if (activeLink) {
        switchView(activeLink.dataset.view);
    } else {
        switchView('dashboard');
    }
});
