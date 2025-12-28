const habitForms = document.querySelectorAll('.habit-form');

habitForms.forEach(form => {
    const id = Number(form.querySelector('.id').value);

    const deleteButton = form.querySelector('.delete-button');
    const submitButton = form.querySelector('.submit-button');

    const nameElement = form.querySelector('.name');

    // deleteButton.addEventListener('click', () => deleteHabit(id));
    // submitButton.addEventListener('click', () => submitHabit(id));

    nameElement.addEventListener('click', (event) => extendForm(event, id));
});

function extendForm(event, id) {
    console.log(`extendForm: ${id}`)

    const habitForms = document.querySelectorAll('.habit-form');
    const form = document.getElementById(`habit-form-${id}`);
    const hiddenBlock = form.querySelector('.hidden-block');

    habitForms.forEach(form => {
        const formId = form.getAttribute('id');
        if (form.classList.contains('expanded') && formId !== `habit-form-${id}`) {
            reduceForm(formId);
        }
    });

    form.classList.add('expanded');
    hiddenBlock.classList.add('expanded');
}

function reduceForm(id) {
    console.log(`reduceForm: ${id}`)
    const form = document.getElementById(id);
    const hiddenBlock = form.querySelector('.hidden-block');
    
    form.classList.remove('expanded');
    hiddenBlock.classList.remove('expanded');
    hiddenBlock.style.marginTop = '0';

    setTimeout(() => {
        hiddenBlock.style.marginTop = null;
    }, 250);
}

function deleteHabit(id) {
    console.log(`deleteHabit: ${id}`)
}

function submitHabit(id) {
    console.log(`submitHabit: ${id}`)
}