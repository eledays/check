const projectsElement = document.querySelector('.projects');

projectsElement.addEventListener('click', (e) => {
    const task = e.target.closest('.task');
    if (task) {
        const taskId = task.id.replace('task-', '');
        handleTaskClick(taskId);
    } 
});

function handleTaskClick(taskId) {
    const taskElement = document.getElementById(`task-${taskId}`);
    const isCompleted = taskElement.classList.contains('status-done');

    if (isCompleted) {
        taskElement.classList.replace('status-done', 'status-todo');
    } else {
        taskElement.classList.add('status-done');
    }

    // TODO: Server update logic can be added here
}