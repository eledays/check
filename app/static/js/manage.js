const createBlock = document.getElementById('create-block'); 
const createBlockText = createBlock.querySelector('.block-text');
const openBlock = document.getElementById('open-block');

function createHabit() {
    createBlock.classList.add('open');
    setTimeout(() => {
        createBlockText.style.display = 'none';
        openBlock.style.display = 'block';
        setTimeout(() => {
            openBlock.style.opacity = '1';
            createBlock.classList.add('top-left-align');
        }, 50);
    }, 200);
}

createBlock.addEventListener('click', createHabit);