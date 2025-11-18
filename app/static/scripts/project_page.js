// project_page.js - Handle task creation, editing, and deletion on project page

document.addEventListener('DOMContentLoaded', function() {
    const newTaskInput = document.getElementById('newTaskInput');
    const tasksContainer = document.querySelector('.tasks-timeline');
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
    let isLongPress = false; // Track if it's a long press to prevent click

    // Function to create task element with timeline
    function createTaskElement(task) {
        // Create task row container
        const taskRow = document.createElement('div');
        taskRow.className = 'task-row';
        
        // Create task div
        const taskDiv = document.createElement('div');
        taskDiv.className = `task status-${task.status}`;
        taskDiv.id = `task-${task.id}`;
        taskDiv.dataset.taskId = task.id;
        taskDiv.dataset.completedAt = task.completed_at || '';
        
        const taskTitle = document.createElement('p');
        // Escape HTML to prevent XSS
        taskTitle.textContent = task.title;
        taskDiv.appendChild(taskTitle);
        
        // Create timeline
        const timeline = document.createElement('div');
        timeline.className = 'timeline';
        
        const timelineLine = document.createElement('div');
        timelineLine.className = 'timeline-line';
        
        const timelineDot = document.createElement('div');
        timelineDot.className = `timeline-dot ${task.status === 'done' ? 'completed' : ''}`;
        
        timeline.appendChild(timelineLine);
        timeline.appendChild(timelineDot);
        
        // Add time if task is completed
        if (task.status === 'done' && task.completed_at) {
            const timelineTime = document.createElement('div');
            timelineTime.className = 'timeline-time';
            const date = new Date(task.completed_at);
            timelineTime.textContent = date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
            timeline.appendChild(timelineTime);
        }
        
        // Assemble task row
        taskRow.appendChild(taskDiv);
        taskRow.appendChild(timeline);
        
        // Add long press event listeners
        setupLongPress(taskDiv);
        
        // Add click event listener for status toggle
        setupClickHandler(taskDiv);
        
        return taskRow;
    }

    // Setup long press on task element
    function setupLongPress(taskElement) {
        let touchMoved = false;
        
        // Mouse events
        taskElement.addEventListener('mousedown', function(e) {
            e.preventDefault();
            isLongPress = false;
            startPress(taskElement);
        });
        
        taskElement.addEventListener('mouseup', function(e) {
            const wasLongPress = isLongPress;
            cancelPress();
            // Don't trigger click if it was a long press
            if (!wasLongPress) {
                // Allow click handler to fire
            }
        });
        taskElement.addEventListener('mouseleave', cancelPress);
        
        // Touch events for mobile
        taskElement.addEventListener('touchstart', function(e) {
            touchMoved = false;
            isLongPress = false;
            startPress(taskElement);
        }, { passive: true });
        
        taskElement.addEventListener('touchmove', function(e) {
            touchMoved = true;
            cancelPress();
        }, { passive: true });
        
        taskElement.addEventListener('touchend', function(e) {
            const wasLongPress = isLongPress;
            cancelPress();
            
            // If it was a long press, prevent the default click event
            if (wasLongPress) {
                e.preventDefault();
                e.stopPropagation();
            } else if (!touchMoved) {
                // It was a short tap without movement - trigger status toggle directly
                e.preventDefault(); // Prevent the click event from firing
                toggleTaskStatus(taskElement);
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

    // Setup click handler for status toggle (for mouse/desktop only)
    function setupClickHandler(taskElement) {
        taskElement.addEventListener('click', function(e) {
            // Don't toggle status if it was a long press
            if (isLongPress) {
                isLongPress = false; // Reset the flag
                return;
            }
            
            // Check if this is a touch-generated click (we handle it in touchend)
            if (e.detail === 0) {
                // This might be a synthetic click from touch, ignore it
                return;
            }
            
            toggleTaskStatus(taskElement);
        });
    }

    // Start press timer
    function startPress(taskElement) {
        taskElement.classList.add('pressing');
        pressTimer = setTimeout(function() {
            isLongPress = true;
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

    // Toggle task status
    async function toggleTaskStatus(taskElement) {
        const taskId = taskElement.dataset.taskId;
        const taskRow = taskElement.closest('.task-row');
        const timeline = taskRow.querySelector('.timeline');
        const timelineDot = timeline.querySelector('.timeline-dot');
        
        // Get current status
        const oldStatus = taskElement.className.match(/status-(\w+)/)[1];
        
        // Determine new status (toggle between todo and done)
        const newStatus = oldStatus === 'done' ? 'todo' : 'done';
        
        // Immediately update UI (optimistic update)
        taskElement.classList.remove(`status-${oldStatus}`);
        taskElement.classList.add(`status-${newStatus}`);
        
        // Update timeline dot
        if (newStatus === 'done') {
            timelineDot.classList.add('completed');
            // Add time placeholder
            const now = new Date();
            const timelineTime = document.createElement('div');
            timelineTime.className = 'timeline-time';
            timelineTime.textContent = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
            timeline.appendChild(timelineTime);
        } else {
            timelineDot.classList.remove('completed');
            // Remove time if exists
            const timelineTime = timeline.querySelector('.timeline-time');
            if (timelineTime) {
                timelineTime.remove();
            }
        }
        
        try {
            const response = await fetch(`/api/project/${projectId}/task/${taskId}/status`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Ошибка при изменении статуса задачи');
            }

            const data = await response.json();
            
            // Verify server response matches our optimistic update
            if (data.success && data.task) {
                // Update completed_at data attribute
                taskElement.dataset.completedAt = data.task.completed_at || '';
                
                // If server returned different status, update to match
                if (data.task.status !== newStatus) {
                    taskElement.classList.remove(`status-${newStatus}`);
                    taskElement.classList.add(`status-${data.task.status}`);
                }
                
                // Update time with actual server time if completed
                if (data.task.status === 'done' && data.task.completed_at) {
                    const serverDate = new Date(data.task.completed_at);
                    const timelineTime = timeline.querySelector('.timeline-time');
                    if (timelineTime) {
                        timelineTime.textContent = serverDate.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
                    }
                }
            }
        } catch (error) {
            console.error('Error toggling task status:', error);
            
            // Rollback to old status on error
            taskElement.classList.remove(`status-${newStatus}`);
            taskElement.classList.add(`status-${oldStatus}`);
            
            // Rollback timeline
            if (oldStatus === 'done') {
                timelineDot.classList.add('completed');
            } else {
                timelineDot.classList.remove('completed');
                const timelineTime = timeline.querySelector('.timeline-time');
                if (timelineTime) {
                    timelineTime.remove();
                }
            }
            
            alert(error.message || 'Не удалось изменить статус задачи');
        }
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
        isLongPress = false; // Reset long press flag when closing modal
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
                // Save reference to the task row (parent of task element)
                const taskRow = currentTaskElement.closest('.task-row');
                
                // Close modal first
                closeModal();
                
                // Add deleting class for smooth collapse animation
                currentTaskElement.classList.add('deleting');
                
                // Remove task row from DOM after animation completes
                setTimeout(() => {
                    taskRow.remove();
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

    // Setup long press and click handlers for existing tasks
    document.querySelectorAll('.task').forEach(function(taskElement) {
        setupLongPress(taskElement);
        setupClickHandler(taskElement);
    });
});
