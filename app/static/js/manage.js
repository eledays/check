const createBlock = document.getElementById('create-block'); 
const createBlockText = createBlock.querySelector('.block-text');
const openBlock = document.getElementById('open-block');
const nameInput = document.querySelector('input#name');
const cancelButton = document.querySelector('button.cancel');

function createHabit() {
    createBlock.classList.add('open');
    setTimeout(() => {
        createBlockText.style.display = 'none';
        openBlock.style.display = 'block';
        setTimeout(() => {
            openBlock.style.opacity = '1';
            createBlock.classList.add('top-left-align');
            nameInput.focus();
        }, 50);
    }, 200);
}

function closeCreatingHabit() {
    createBlock.classList.remove('open');
    setTimeout(() => {
        createBlockText.style.display = 'block';
        openBlock.style.opacity = '0';
    }, 200);
}

cancelButton.addEventListener('click', closeCreatingHabit);
createBlock.addEventListener('click', createHabit);