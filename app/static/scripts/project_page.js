// project_page.js - Handle task creation, editing, and deletion on project page

document.addEventListener('DOMContentLoaded', function() {
    const newTaskInput = document.getElementById('newTaskInput');
    const tasksContainer = document.querySelector('.tasks');
    const modal = document.getElementById('taskModal');
    const modalOverlay = modal.querySelector('.modal-overlay');
    const editTaskInput = document.getElementById('editTaskInput');
    const saveTaskBtn = document.getElementById('saveTaskBtn');
    const deleteTaskBtn = document.getElementById('deleteTaskBtn');
    const cancelTaskBtn = document.getElementById('cancelTaskBtn');

    // Get project ID from URL
    const projectId = window.location.pathname.split('/').filter(Boolean).pop();
    
    // Track current task being edited
    let currentTaskId = null;
    let currentTaskElement = null;
    
    // Long press handling
    let pressTimer = null;
    const LONG_PRESS_DURATION = 500; // milliseconds

    // Function to create task element
    function createTaskElement(task) {
        const taskDiv = document.createElement('div');
        taskDiv.className = `task status-${task.status}`;
        taskDiv.id = `task-${task.id}`;
        taskDiv.dataset.taskId = task.id;
        
        const taskTitle = document.createElement('p');
        // Escape HTML to prevent XSS
        taskTitle.textContent = task.title;
        
        taskDiv.appendChild(taskTitle);
        
        // Add long press event listeners
        setupLongPress(taskDiv);
        
        return taskDiv;
    }

    // Setup long press on task element
    function setupLongPress(taskElement) {
        let touchMoved = false;
        
        // Mouse events
        taskElement.addEventListener('mousedown', function(e) {
            e.preventDefault();
            startPress(taskElement);
        });
        
        taskElement.addEventListener('mouseup', cancelPress);
        taskElement.addEventListener('mouseleave', cancelPress);
        
        // Touch events for mobile
        taskElement.addEventListener('touchstart', function(e) {
            touchMoved = false;
            startPress(taskElement);
        }, { passive: true });
        
        taskElement.addEventListener('touchmove', function(e) {
            touchMoved = true;
            cancelPress();
        }, { passive: true });
        
        taskElement.addEventListener('touchend', function(e) {
            if (!touchMoved && pressTimer) {
                // Touch ended without moving - long press might trigger
                // Don't cancel immediately to allow long press to complete
            } else {
                cancelPress();
            }
        });
        
        taskElement.addEventListener('touchcancel', cancelPress);
        
        // Prevent context menu on long press
        taskElement.addEventListener('contextmenu', function(e) {
            if (pressTimer || currentTaskId) {
                e.preventDefault();
            }
        });
    }

    // Start press timer
    function startPress(taskElement) {
        taskElement.classList.add('pressing');
        pressTimer = setTimeout(function() {
            openEditModal(taskElement);
            taskElement.classList.remove('pressing');
        }, LONG_PRESS_DURATION);
    }

    // Cancel press timer
    function cancelPress() {
        if (pressTimer) {
            clearTimeout(pressTimer);
            pressTimer = null;
        }
        document.querySelectorAll('.task.pressing').forEach(el => {
            el.classList.remove('pressing');
        });
    }

    // Open edit modal
    function openEditModal(taskElement) {
        currentTaskId = taskElement.dataset.taskId;
        currentTaskElement = taskElement;
        
        const taskTitle = taskElement.querySelector('p').textContent;
        editTaskInput.value = taskTitle;
        
        modal.style.display = 'flex';
        editTaskInput.focus();
    }

    // Close modal
    function closeModal() {
        modal.style.display = 'none';
        currentTaskId = null;
        currentTaskElement = null;
        editTaskInput.value = '';
    }

    // Function to add task
    async function addTask() {
        const title = newTaskInput.value.trim();
        
        if (!title) {
            alert('Пожалуйста, введите название задачи');
            return;
        }

        if (title.length > 128) {
            alert('Название задачи слишком длинное (максимум 128 символов)');
            return;
        }

        try {
            const response = await fetch(`/api/project/${projectId}/task`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title: title })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Ошибка при создании задачи');
            }

            const data = await response.json();
            
            if (data.success && data.task) {
                // Add new task to the list
                const taskElement = createTaskElement(data.task);
                
                // Add appearing class before appending to DOM
                taskElement.classList.add('task-appearing');
                tasksContainer.appendChild(taskElement);
                
                // Trigger animation by removing class after a brief moment
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        taskElement.classList.remove('task-appearing');
                        
                        // Scroll to new task after animation starts
                        setTimeout(() => {
                            taskElement.scrollIntoView({ 
                                behavior: 'smooth', 
                                block: 'nearest',
                                inline: 'nearest'
                            });
                        }, 50); // Small delay to let animation begin
                    });
                });
                
                // Clear input
                newTaskInput.value = '';
            }
        } catch (error) {
            console.error('Error adding task:', error);
            alert(error.message || 'Не удалось добавить задачу');
        }
    }

    // Function to update task
    async function updateTask() {
        const title = editTaskInput.value.trim();
        
        if (!title) {
            alert('Пожалуйста, введите название задачи');
            return;
        }

        if (title.length > 128) {
            alert('Название задачи слишком длинное (максимум 128 символов)');
            return;
        }

        try {
            saveTaskBtn.disabled = true;
            
            const response = await fetch(`/api/project/${projectId}/task/${currentTaskId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title: title })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Ошибка при обновлении задачи');
            }

            const data = await response.json();
            
            if (data.success && data.task) {
                // Update task title in the DOM
                currentTaskElement.querySelector('p').textContent = data.task.title;
                closeModal();
            }
        } catch (error) {
            console.error('Error updating task:', error);
            alert(error.message || 'Не удалось обновить задачу');
        } finally {
            saveTaskBtn.disabled = false;
        }
    }

    // Function to delete task
    async function deleteTask() {
        if (!confirm('Вы уверены, что хотите удалить эту задачу?')) {
            return;
        }

        try {
            deleteTaskBtn.disabled = true;
            
            const response = await fetch(`/api/project/${projectId}/task/${currentTaskId}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Ошибка при удалении задачи');
            }

            const data = await response.json();
            
            if (data.success) {
                // Save reference before closing modal
                const taskElementToRemove = currentTaskElement;
                
                // Close modal first
                closeModal();
                
                // Add deleting class for smooth collapse animation
                taskElementToRemove.classList.add('deleting');
                
                // Remove from DOM after animation completes
                setTimeout(() => {
                    taskElementToRemove.remove();
                }, 300); // Match transition duration in CSS
            }
        } catch (error) {
            console.error('Error deleting task:', error);
            alert(error.message || 'Не удалось удалить задачу');
        } finally {
            deleteTaskBtn.disabled = false;
        }
    }

    // Add Enter key support for new task input
    newTaskInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            addTask();
        }
    });

    // Add Enter key support for edit task input
    editTaskInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            updateTask();
        }
    });

    // Modal button handlers
    saveTaskBtn.addEventListener('click', updateTask);
    deleteTaskBtn.addEventListener('click', deleteTask);
    cancelTaskBtn.addEventListener('click', closeModal);
    
    // Close modal when clicking overlay
    modalOverlay.addEventListener('click', closeModal);

    // Setup long press for existing tasks
    document.querySelectorAll('.task').forEach(setupLongPress);
});
