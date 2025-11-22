// Delete confirmation functionality
document.addEventListener('DOMContentLoaded', () => {
    const deleteButton = document.getElementById('delete-project-button');
    const modal = document.getElementById('delete-confirmation-modal');
    const confirmButton = document.getElementById('confirm-delete-button');
    const cancelButton = document.getElementById('cancel-delete-button');
    const modalOverlay = modal.querySelector('.modal-overlay');

    deleteButton.addEventListener('click', () => {
        modal.style.display = 'flex';
    });

    cancelButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    modalOverlay.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    confirmButton.addEventListener('click', () => {
        // Create a form and submit it
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = confirmButton.dataset.deleteUrl;
        
        // Add CSRF token
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
    });
});
