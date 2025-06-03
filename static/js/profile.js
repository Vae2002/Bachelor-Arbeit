function changeMember(select) {
    const memberId = select.value;
    window.location.href = `{{ url_for('profile') }}?member_id=${memberId}`;
}

document.addEventListener('DOMContentLoaded', function () {
    const dropdownItems = document.querySelectorAll('.dropdown-menu .dropdown-item');
    const dropdownButton = document.getElementById('memberDropdown');

    dropdownItems.forEach(item => {
    item.addEventListener('click', function (e) {
        if (this.classList.contains('text-success')) {
        dropdownButton.textContent = "Select Member";
        }
        else{
        dropdownButton.textContent = this.textContent;
        }
    });
    });
});

document.getElementById('diet-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);

    fetch('/member_diet_calculator', {
        method: 'POST',
        body: formData
    }).then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }

        document.getElementById('calcBMR').innerText = data.bmr;
        document.getElementById('calcCalories').innerText = data.tdee;
        document.getElementById('calcProtein').innerText = data.protein;
        document.getElementById('calcFat').innerText = data.fat;
        document.getElementById('calcCarbs').innerText = data.carbs;
    });
});

function applyDietValues() {
    const calories = document.getElementById('calcCalories').innerText;
    const protein = document.getElementById('calcProtein').innerText;
    const fat = document.getElementById('calcFat').innerText;
    const carbs = document.getElementById('calcCarbs').innerText;

    document.getElementById('dailyCalories').value = calories;
    document.getElementById('proteinGrams').value = protein;
    document.getElementById('fatGrams').value = fat;
    document.getElementById('carbsGrams').value = carbs;

    // Close calculator modal
    const dietModal = bootstrap.Modal.getInstance(document.getElementById('dietCalculatorModal'));
    dietModal.hide();

    // Only show memberModal if it's not already open
    const memberModalEl = document.getElementById('memberModal');
    const isMemberModalVisible = memberModalEl.classList.contains('show');

    if (!isMemberModalVisible) {
        setTimeout(() => {
            const memberModal = new bootstrap.Modal(memberModalEl);
            memberModal.show();
        }, 300);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const editButtons = document.querySelectorAll('.edit-member-btn');
    const addButton = document.querySelector('.add-member-btn');
    const form = document.getElementById('memberForm');
    const modalTitle = document.getElementById('memberModalLabel');

    function resetForm() {
        form.reset(); 

        document.querySelectorAll('.form-check-input').forEach(input => input.checked = false);
    }

    function checkBoxesFromArray(className, values) {
        document.querySelectorAll(`.${className}`).forEach(input => {
            input.checked = values.includes(input.value);
        });
    }

    // Open Edit
    editButtons.forEach(button => {
        button.addEventListener('click', function () {
            const member = JSON.parse(this.getAttribute('data-member'));
            resetForm();

            modalTitle.textContent = `Edit Member`;
            form.action = `/edit_member/${member.id}`;

            document.getElementById('memberName').value = member.name || "";
            document.getElementById('dailyCalories').value = member.daily_calories || "";
            document.getElementById('proteinGrams').value = member.protein_grams || "";
            document.getElementById('fatGrams').value = member.fat_grams || "";
            document.getElementById('carbsGrams').value = member.carbs_grams || "";

            checkBoxesFromArray('cuisine-checkbox', member.cuisines || []);
            checkBoxesFromArray('allergy-checkbox', member.allergies || []);
            checkBoxesFromArray('restriction-checkbox', member.dietary_restrictions || []);

            const modal = new bootstrap.Modal(document.getElementById('memberModal'));
            modal.show();
        });
    });

    // Open Add
    addButton.addEventListener('click', function () {
        resetForm();
        modalTitle.textContent = `Add New Member`;
        form.action = `/add_member`;

        const modal = new bootstrap.Modal(document.getElementById('memberModal'));
        modal.show();
    });
});