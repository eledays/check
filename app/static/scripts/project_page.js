// project_page.js - Handle task creation, editing, and deletion on project page

// Helper function to format time in user's timezone
function formatTimeInUserTimezone(isoString) {
    if (!isoString) return '';
    
    const date = new Date(isoString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
        console.error('Invalid date string:', isoString);
        return '';
    }

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const taskDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    // Format time
    const time = date.toLocaleTimeString('ru-RU', { 
        hour: '2-digit', 
        minute: '2-digit',
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });
    
    // If today - just show time
    if (taskDate.getTime() === today.getTime()) {
        return time;
    }
    
    // If yesterday - show "вчера"
    if (taskDate.getTime() === yesterday.getTime()) {
        return 'вчера';
    }
    
    // For other dates
    const day = date.getDate();
    const month = date.toLocaleString('ru-RU', { month: 'long' });
    
    // If same year - show: day month time
    if (date.getFullYear() === now.getFullYear()) {
        return `${day} ${month} ${time}`;
    }
    
    // If previous year - show: day month year time
    return `${day} ${month} ${date.getFullYear()} ${time}`;
}

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
    
    // Drag and drop state
    let draggedElement = null;
    let dragGhost = null; // Visual ghost element for dragging
    let dragOffsetY = 0;
    let dragOffsetX = 0;
    let autoScrollInterval = null; // For auto-scrolling near edges
    
    // Long press handling
    let pressTimer = null;
    const LONG_PRESS_DURATION = 500; // milliseconds
    let isLongPress = false; // Track if it's a long press to prevent click

    // Function to create task element with timeline
    function createTaskElement(task) {
        // Create task row container
        const taskRow = document.createElement('div');
        taskRow.className = 'task-row';
        taskRow.dataset.taskId = task.id;
        
        // Set draggable attribute for incomplete tasks
        if (task.status !== 'done') {
            taskRow.setAttribute('draggable', 'true');
        }
        
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
        
        // Add draggable-handle class for incomplete tasks
        if (task.status !== 'done') {
            timeline.classList.add('draggable-handle');
        }
        
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
            // Use the helper function to format time in user's timezone
            timelineTime.textContent = formatTimeInUserTimezone(task.completed_at);
            timeline.appendChild(timelineTime);
        }
        
        // Assemble task row - timeline first, then task
        taskRow.appendChild(timeline);
        taskRow.appendChild(taskDiv);
        
        // Setup drag and drop AFTER elements are assembled
        if (task.status !== 'done') {
            setupDragAndDrop(taskRow);
        }
        
        // Add long press event listeners
        setupLongPress(taskDiv);
        
        // Add click event listener for status toggle
        setupClickHandler(taskDiv);
        
        return taskRow;
    }

    // Setup drag and drop on task row
    function setupDragAndDrop(taskRow) {
        const timeline = taskRow.querySelector('.timeline');
        const taskElement = taskRow.querySelector('.task');
        
        // Make only timeline draggable, not the whole row
        // Prevent drag from starting anywhere except timeline
        taskRow.addEventListener('mousedown', function(e) {
            const target = e.target;
            const isTimeline = target === timeline || 
                             target.classList.contains('timeline-dot') ||
                             target.classList.contains('timeline-line') ||
                             target.closest('.timeline.draggable-handle');
            
            if (!isTimeline) {
                // Remove draggable attribute temporarily to prevent drag
                taskRow.removeAttribute('draggable');
                // Restore it after a moment
                setTimeout(() => {
                    if (taskRow.querySelector('.timeline.draggable-handle')) {
                        taskRow.setAttribute('draggable', 'true');
                    }
                }, 0);
            } else {
                // Ensure draggable is set when starting from timeline
                taskRow.setAttribute('draggable', 'true');
            }
        });
        
        // Prevent drag from starting on task element
        taskElement.addEventListener('dragstart', function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
        
        taskElement.addEventListener('mousedown', function(e) {
            // Prevent default only on task element to allow clicks/long press
            // but not on timeline where we want drag
        });
        
        // Dragstart - only triggers when dragging from timeline
        taskRow.addEventListener('dragstart', function(e) {
            // Check if drag started from timeline area
            const target = e.target;
            const isTimeline = target === timeline || 
                             target.classList.contains('timeline-dot') ||
                             target.classList.contains('timeline-line') ||
                             target.closest('.timeline.draggable-handle');
            
            if (!isTimeline) {
                e.preventDefault();
                return false;
            }
            
            console.log('Drag started from timeline'); // Debug
            
            draggedElement = taskRow;
            taskRow.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', taskRow.dataset.taskId);
            
            // Create a custom drag image for better visual feedback
            const dragImage = taskRow.cloneNode(true);
            dragImage.style.position = 'absolute';
            dragImage.style.top = '-9999px';
            dragImage.style.left = '-9999px';
            dragImage.style.opacity = '0.8';
            dragImage.style.transform = 'rotate(2deg)';
            dragImage.style.width = taskRow.offsetWidth + 'px';
            dragImage.classList.add('drag-preview');
            document.body.appendChild(dragImage);
            
            // Set custom drag image
            const rect = taskRow.getBoundingClientRect();
            e.dataTransfer.setDragImage(dragImage, rect.width / 2, rect.height / 2);
            
            // Remove the preview element after drag starts
            setTimeout(() => {
                if (dragImage.parentNode) {
                    dragImage.parentNode.removeChild(dragImage);
                }
            }, 0);
        });
        
        // Dragover - allow drop
        taskRow.addEventListener('dragover', function(e) {
            if (draggedElement && draggedElement !== taskRow) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                
                // Get all incomplete task rows
                const incompleteTasks = getIncompleteTaskRows();
                
                // Only allow dropping on incomplete tasks
                if (incompleteTasks.includes(taskRow)) {
                    taskRow.classList.add('drag-over');
                }
            }
        });
        
        // Dragleave - remove highlight
        taskRow.addEventListener('dragleave', function(e) {
            if (e.target === taskRow) {
                taskRow.classList.remove('drag-over');
            }
        });
        
        // Drop - reorder tasks
        taskRow.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (draggedElement && draggedElement !== taskRow) {
                const incompleteTasks = getIncompleteTaskRows();
                
                // Only allow dropping on incomplete tasks
                if (incompleteTasks.includes(taskRow)) {
                    // Determine if we should insert before or after
                    const draggedIndex = incompleteTasks.indexOf(draggedElement);
                    const targetIndex = incompleteTasks.indexOf(taskRow);
                    
                    // Animate the move
                    if (draggedIndex < targetIndex) {
                        // Dragging down - insert after target
                        taskRow.parentNode.insertBefore(draggedElement, taskRow.nextSibling);
                    } else {
                        // Dragging up - insert before target
                        taskRow.parentNode.insertBefore(draggedElement, taskRow);
                    }
                    
                    // Add a brief highlight animation
                    draggedElement.classList.add('drop-animation');
                    setTimeout(() => {
                        draggedElement.classList.remove('drop-animation');
                    }, 300);
                    
                    // Save new order to server
                    saveTaskOrder();
                }
            }
            
            taskRow.classList.remove('drag-over');
        });
        
        // Dragend - cleanup
        taskRow.addEventListener('dragend', function(e) {
            taskRow.classList.remove('dragging');
            document.querySelectorAll('.task-row.drag-over').forEach(row => {
                row.classList.remove('drag-over');
            });
            draggedElement = null;
        });
        
        // Touch support for mobile with smooth animation
        let touchStartY = 0;
        let touchStartX = 0;
        let isDraggingTouch = false;
        let touchDragElement = null;
        
        timeline.addEventListener('touchstart', function(e) {
            const touch = e.touches[0];
            touchStartY = touch.clientY;
            touchStartX = touch.clientX;
            isDraggingTouch = false;
            
            // Store offset for smooth positioning
            const rect = taskRow.getBoundingClientRect();
            dragOffsetY = touch.clientY - rect.top;
            dragOffsetX = touch.clientX - rect.left;
            
            // Prevent long press from triggering while on timeline
            e.stopPropagation();
        }, { passive: false }); // Changed to false to allow preventDefault in touchmove
        
        timeline.addEventListener('touchmove', function(e) {
            if (!isDraggingTouch) {
                const touch = e.touches[0];
                const deltaY = Math.abs(touch.clientY - touchStartY);
                const deltaX = Math.abs(touch.clientX - touchStartX);
                
                // Start dragging if moved more than 10px
                if (deltaY > 10 || deltaX > 10) {
                    isDraggingTouch = true;
                    draggedElement = taskRow;
                    taskRow.classList.add('dragging');
                    
                    // Don't block body scrolling - we'll handle it with auto-scroll
                    // Just prevent default touch behavior
                    
                    // Haptic feedback on mobile (if supported)
                    if (navigator.vibrate) {
                        navigator.vibrate(50);
                    }
                    
                    // Create ghost element for visual feedback
                    createDragGhost(taskRow);
                    
                    // Prevent scrolling now that we started dragging
                    e.preventDefault();
                }
                // Don't prevent default if not dragging yet - allow normal scroll
            } else {
                // We are dragging - prevent page scrolling
                e.preventDefault();
                
                const touch = e.touches[0];
                
                // Update ghost position
                if (dragGhost) {
                    dragGhost.style.left = (touch.clientX - dragOffsetX) + 'px';
                    dragGhost.style.top = (touch.clientY - dragOffsetY) + 'px';
                }
                
                // Handle auto-scroll near edges
                handleAutoScroll(touch.clientY);
                
                const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
                const targetRow = elementBelow ? elementBelow.closest('.task-row') : null;
                
                // Remove drag-over from all rows
                document.querySelectorAll('.task-row.drag-over').forEach(row => {
                    row.classList.remove('drag-over');
                });
                
                // Add drag-over to current target
                if (targetRow && targetRow !== taskRow && targetRow.hasAttribute('draggable')) {
                    targetRow.classList.add('drag-over');
                }
            }
        }, { passive: false });
        
        timeline.addEventListener('touchend', function(e) {
            if (isDraggingTouch) {
                // Only preventDefault if we were actually dragging
                e.preventDefault();
                e.stopPropagation();
                
                // Stop auto-scrolling
                stopAutoScroll();
                
                const touch = e.changedTouches[0];
                const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
                const targetRow = elementBelow ? elementBelow.closest('.task-row') : null;
                
                if (targetRow && targetRow !== taskRow && targetRow.hasAttribute('draggable')) {
                    const incompleteTasks = getIncompleteTaskRows();
                    
                    if (incompleteTasks.includes(targetRow)) {
                        const draggedIndex = incompleteTasks.indexOf(taskRow);
                        const targetIndex = incompleteTasks.indexOf(targetRow);
                        
                        if (draggedIndex < targetIndex) {
                            targetRow.parentNode.insertBefore(taskRow, targetRow.nextSibling);
                        } else {
                            targetRow.parentNode.insertBefore(taskRow, targetRow);
                        }
                        
                        // Add drop animation
                        taskRow.classList.add('drop-animation');
                        setTimeout(() => {
                            taskRow.classList.remove('drop-animation');
                        }, 300);
                        
                        // Haptic feedback on successful drop
                        if (navigator.vibrate) {
                            navigator.vibrate([30, 10, 30]);
                        }
                        
                        saveTaskOrder();
                    }
                }
                
                // Cleanup
                removeDragGhost();
                taskRow.classList.remove('dragging');
                document.querySelectorAll('.task-row.drag-over').forEach(row => {
                    row.classList.remove('drag-over');
                });
                
                draggedElement = null;
                isDraggingTouch = false;
                touchDragElement = null;
            }
        }, { passive: false });
        
        timeline.addEventListener('touchcancel', function(e) {
            if (isDraggingTouch) {
                // Stop auto-scrolling
                stopAutoScroll();
                
                removeDragGhost();
                taskRow.classList.remove('dragging');
                document.querySelectorAll('.task-row.drag-over').forEach(row => {
                    row.classList.remove('drag-over');
                });
                
                draggedElement = null;
                isDraggingTouch = false;
                touchDragElement = null;
            }
        });
    }
    
    // Create a ghost element for drag visualization
    function createDragGhost(taskRow) {
        removeDragGhost(); // Remove any existing ghost
        
        dragGhost = taskRow.cloneNode(true);
        dragGhost.classList.add('drag-ghost');
        dragGhost.style.position = 'fixed';
        dragGhost.style.pointerEvents = 'none';
        dragGhost.style.zIndex = '9999';
        dragGhost.style.width = taskRow.offsetWidth + 'px';
        dragGhost.style.opacity = '0.8';
        dragGhost.style.transform = 'rotate(3deg) scale(1.05)';
        dragGhost.style.transition = 'transform 0.2s ease';
        
        const rect = taskRow.getBoundingClientRect();
        dragGhost.style.left = rect.left + 'px';
        dragGhost.style.top = rect.top + 'px';
        
        document.body.appendChild(dragGhost);
    }
    
    // Remove drag ghost element
    function removeDragGhost() {
        if (dragGhost && dragGhost.parentNode) {
            dragGhost.parentNode.removeChild(dragGhost);
            dragGhost = null;
        }
    }
    
    // Auto-scroll when dragging near edges
    function handleAutoScroll(clientY) {
        const SCROLL_THRESHOLD = 100; // pixels from edge to start scrolling
        const SCROLL_SPEED = 10; // pixels per frame
        
        const windowHeight = window.innerHeight;
        
        // Clear existing interval
        if (autoScrollInterval) {
            clearInterval(autoScrollInterval);
            autoScrollInterval = null;
        }
        
        // Scroll up if near top
        if (clientY < SCROLL_THRESHOLD) {
            console.log('Auto-scrolling UP', clientY); // Debug
            autoScrollInterval = setInterval(() => {
                window.scrollBy({
                    top: -SCROLL_SPEED,
                    behavior: 'auto'
                });
                // Update ghost position while scrolling
                if (dragGhost) {
                    const currentTop = parseInt(dragGhost.style.top);
                    dragGhost.style.top = (currentTop - SCROLL_SPEED) + 'px';
                }
            }, 16); // ~60fps
        }
        // Scroll down if near bottom
        else if (clientY > windowHeight - SCROLL_THRESHOLD) {
            console.log('Auto-scrolling DOWN', clientY, windowHeight); // Debug
            autoScrollInterval = setInterval(() => {
                window.scrollBy({
                    top: SCROLL_SPEED,
                    behavior: 'auto'
                });
                // Update ghost position while scrolling
                if (dragGhost) {
                    const currentTop = parseInt(dragGhost.style.top);
                    dragGhost.style.top = (currentTop + SCROLL_SPEED) + 'px';
                }
            }, 16);
        }
    }
    
    // Stop auto-scroll
    function stopAutoScroll() {
        if (autoScrollInterval) {
            clearInterval(autoScrollInterval);
            autoScrollInterval = null;
        }
    }
    
    // Get all incomplete task rows in order
    function getIncompleteTaskRows() {
        return Array.from(tasksContainer.querySelectorAll('.task-row')).filter(row => {
            const task = row.querySelector('.task');
            const status = task.className.match(/status-(\w+)/)[1];
            return status !== 'done';
        });
    }
    
    // Save task order to server
    async function saveTaskOrder() {
        const incompleteTasks = getIncompleteTaskRows();
        const taskIds = incompleteTasks.map(row => row.dataset.taskId);
        
        try {
            const response = await fetch(`/api/project/${projectId}/tasks/reorder`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task_ids: taskIds })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Ошибка при изменении порядка задач');
            }

            const data = await response.json();
            
            if (!data.success) {
                throw new Error('Не удалось сохранить порядок задач');
            }
        } catch (error) {
            console.error('Error saving task order:', error);
            // Don't show alert for order changes, just log
        }
    }

    // Setup long press on task element
    function setupLongPress(taskElement) {
        let touchMoved = false;
        
        // Mouse events
        taskElement.addEventListener('mousedown', function(e) {
            // Don't prevent default here - it blocks dragging
            // Only start long press timer
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

    // Function to reorder tasks: completed tasks at top (sorted by completion time - oldest first, newest last), then incomplete at bottom
    function reorderTasks() {
        const taskRows = Array.from(tasksContainer.querySelectorAll('.task-row'));
        
        // FLIP Animation: First - record initial positions
        const initialPositions = new Map();
        taskRows.forEach(taskRow => {
            const rect = taskRow.getBoundingClientRect();
            initialPositions.set(taskRow, {
                top: rect.top,
                left: rect.left
            });
        });
        
        // Separate completed and incomplete tasks
        const completedTasks = [];
        const incompleteTasks = [];
        
        taskRows.forEach(taskRow => {
            const task = taskRow.querySelector('.task');
            const status = task.className.match(/status-(\w+)/)[1];
            
            if (status === 'done') {
                const completedAt = task.dataset.completedAt;
                completedTasks.push({ taskRow, completedAt });
            } else {
                incompleteTasks.push(taskRow);
            }
        });
        
        // Sort completed tasks by completion time (oldest first, newest last)
        completedTasks.sort((a, b) => {
            const timeA = a.completedAt ? new Date(a.completedAt).getTime() : 0;
            const timeB = b.completedAt ? new Date(b.completedAt).getTime() : 0;
            return timeA - timeB; // Ascending order (oldest first)
        });
        
        // Re-append in correct order: completed first (oldest to newest), then incomplete
        completedTasks.forEach(({ taskRow }) => {
            tasksContainer.appendChild(taskRow);
        });
        incompleteTasks.forEach(taskRow => {
            tasksContainer.appendChild(taskRow);
        });
        
        // FLIP Animation: Last - record final positions and animate
        taskRows.forEach(taskRow => {
            const initial = initialPositions.get(taskRow);
            const final = taskRow.getBoundingClientRect();
            
            const deltaY = initial.top - final.top;
            const deltaX = initial.left - final.left;
            
            // Skip animation if element didn't move
            if (deltaY === 0 && deltaX === 0) return;
            
            // Invert - apply transform to make it appear at initial position
            taskRow.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
            taskRow.style.transition = 'none';
            
            // Force reflow
            taskRow.offsetHeight;
            
            // Play - animate to final position
            requestAnimationFrame(() => {
                taskRow.style.transition = 'transform 0.3s ease-out';
                taskRow.style.transform = '';
                
                // Clean up after animation
                setTimeout(() => {
                    taskRow.style.transition = '';
                }, 300);
            });
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
        
        // Update draggable state and timeline classes
        if (newStatus === 'done') {
            // Task is now completed - remove draggable
            taskRow.removeAttribute('draggable');
            timeline.classList.remove('draggable-handle');
            
            timelineDot.classList.add('completed');
            // Add time placeholder
            const now = new Date();
            const timelineTime = document.createElement('div');
            timelineTime.className = 'timeline-time';
            // Format current time in user's timezone
            timelineTime.textContent = formatTimeInUserTimezone(now.toISOString());
            timeline.appendChild(timelineTime);
            // Set temporary completed_at for proper sorting
            taskElement.dataset.completedAt = now.toISOString();
        } else {
            // Task is now incomplete - make it draggable
            taskRow.setAttribute('draggable', 'true');
            timeline.classList.add('draggable-handle');
            setupDragAndDrop(taskRow);
            
            timelineDot.classList.remove('completed');
            // Remove time if exists
            const timelineTime = timeline.querySelector('.timeline-time');
            if (timelineTime) {
                timelineTime.remove();
            }
            // Clear completed_at
            taskElement.dataset.completedAt = '';
        }
        
        // Reorder tasks after status change
        reorderTasks();
        
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
                // Update completed_at data attribute with server value
                taskElement.dataset.completedAt = data.task.completed_at || '';
                
                // If server returned different status, update to match
                if (data.task.status !== newStatus) {
                    taskElement.classList.remove(`status-${newStatus}`);
                    taskElement.classList.add(`status-${data.task.status}`);
                }
                
                // Update time with actual server time if completed
                if (data.task.status === 'done' && data.task.completed_at) {
                    const timelineTime = timeline.querySelector('.timeline-time');
                    if (timelineTime) {
                        // Use the helper function to format time in user's timezone
                        timelineTime.textContent = formatTimeInUserTimezone(data.task.completed_at);
                    }
                }
                
                // Reorder again with accurate server time
                reorderTasks();
            }
        } catch (error) {
            console.error('Error toggling task status:', error);
            
            // Rollback to old status on error
            taskElement.classList.remove(`status-${newStatus}`);
            taskElement.classList.add(`status-${oldStatus}`);
            
            // Rollback draggable state
            if (oldStatus === 'done') {
                // Was completed, should not be draggable
                taskRow.removeAttribute('draggable');
                timeline.classList.remove('draggable-handle');
                timelineDot.classList.add('completed');
                // Restore previous completed_at value if it existed
                // (We don't have the old value saved, but server should have it)
            } else {
                // Was incomplete, should be draggable
                taskRow.setAttribute('draggable', 'true');
                timeline.classList.add('draggable-handle');
                timelineDot.classList.remove('completed');
                const timelineTime = timeline.querySelector('.timeline-time');
                if (timelineTime) {
                    timelineTime.remove();
                }
                taskElement.dataset.completedAt = '';
            }
            
            // Reorder tasks back to correct state
            reorderTasks();
            
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
    
    // Setup drag and drop for existing incomplete task rows
    document.querySelectorAll('.task-row[draggable="true"]').forEach(function(taskRow) {
        setupDragAndDrop(taskRow);
    });
    
    // Convert all existing timeline times to user's timezone
    document.querySelectorAll('.timeline-time[data-time]').forEach(function(timeElement) {
        const isoTime = timeElement.getAttribute('data-time');
        if (isoTime) {
            timeElement.textContent = formatTimeInUserTimezone(isoTime);
        }
    });
});
