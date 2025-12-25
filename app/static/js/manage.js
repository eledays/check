const createBlock = document.getElementById('create-block'); 

function createHabit() {
    createBlock.classList.add('open');

}

createBlock.addEventListener('click', createHabit);