// project_page.js - Handle task creation on project page

document.addEventListener('DOMContentLoaded', function() {
    const newTaskInput = document.getElementById('newTaskInput');
    const addTaskButton = document.getElementById('addTaskButton');
    const tasksContainer = document.querySelector('.tasks');

    // Get project ID from URL
    const projectId = window.location.pathname.split('/').filter(Boolean).pop();

    // Function to create task element
    function createTaskElement(task) {
        const taskDiv = document.createElement('div');
        taskDiv.className = `task status-${task.status}`;
        taskDiv.id = `task-${task.id}`;
        
        const taskTitle = document.createElement('p');
        // Escape HTML to prevent XSS
        taskTitle.textContent = task.title;
        
        taskDiv.appendChild(taskTitle);
        return taskDiv;
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

        // Disable button while sending request
        addTaskButton.disabled = true;
        addTaskButton.textContent = 'Добавление...';

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
                tasksContainer.appendChild(taskElement);
                
                // Clear input
                newTaskInput.value = '';
                
                // Show success feedback (optional)
                taskElement.style.animation = 'fadeIn 0.3s ease-in';
            }
        } catch (error) {
            console.error('Error adding task:', error);
            alert(error.message || 'Не удалось добавить задачу');
        } finally {
            // Re-enable button
            addTaskButton.disabled = false;
            addTaskButton.textContent = 'Добавить';
        }
    }

    // Add click event listener to button
    addTaskButton.addEventListener('click', addTask);

    // Add Enter key support
    newTaskInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            addTask();
        }
    });
});
