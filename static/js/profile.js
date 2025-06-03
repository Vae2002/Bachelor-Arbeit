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
    // Get values from calculator modal
    const calories = document.getElementById('calcCalories').innerText;
    const protein = document.getElementById('calcProtein').innerText;
    const fat = document.getElementById('calcFat').innerText;
    const carbs = document.getElementById('calcCarbs').innerText;

    // Set values in addMemberModal form (to <input> elements)
    document.getElementById('dailyCalories').value = calories;
    document.getElementById('proteinGrams').value = protein;
    document.getElementById('fatGrams').value = fat;
    document.getElementById('carbsGrams').value = carbs;

    // Close calculator modal
    const dietModal = bootstrap.Modal.getInstance(document.getElementById('dietCalculatorModal'));
    dietModal.hide();

    // Show Add Member modal after a short delay
    setTimeout(() => {
        const addMemberModalEl = document.getElementById('addMemberModal');
        const addMemberModal = new bootstrap.Modal(addMemberModalEl);
        addMemberModal.show();
    }, 300);
}

document.addEventListener('DOMContentLoaded', function () {
    const editButtons = document.querySelectorAll('.edit-member-btn');
    const editForm = document.getElementById('editMemberForm');

    editButtons.forEach(button => {
        button.addEventListener('click', function () {
            const member = JSON.parse(this.getAttribute('data-member'));
            document.getElementById('editMemberId').value = member.id;
            document.getElementById('editMemberName').value = member.name;
            // set action for form
            editForm.action = `/edit_member/${member.id}`;
        });
    });
});
