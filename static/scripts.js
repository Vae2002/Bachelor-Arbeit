// Toggle purchased status (AJAX)
function togglePurchased(itemId) {
    fetch(`/toggle_purchased/${itemId}`, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        let itemElement = document.getElementById('name-' + itemId);
        let quantityElement = document.getElementById('quantity-' + itemId);

        if (data.purchased) {
            itemElement.classList.add('purchased');
            quantityElement.classList.add('purchased');
        } else {
            itemElement.classList.remove('purchased');
            quantityElement.classList.remove('purchased');
        }

        let radioButton = document.querySelector(`input[name="purchased-${itemId}"]`);
        radioButton.checked = data.purchased;
    })
    .catch(error => console.error('Error:', error));
}

// Save changes to name or quantity (AJAX)
function saveChanges(itemId, field) {
    let newValue = document.getElementById(field + '-' + itemId).value.trim();
    
    if (newValue === "") {
        alert("Value cannot be empty!");
        return;
    }

    let formData = new FormData();
    formData.append('new_' + field, newValue);

    fetch(`/rename/${itemId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            alert('Failed to save changes');
        }
    })
    .catch(error => console.error('Error:', error));
}

// Function to handle clearing all purchased items
function clearAllPurchased() {
    fetch('/clear_all', {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        
        let listItems = document.querySelectorAll('.list-group-item');
        listItems.forEach(item => {
            if (item.querySelector('input[type="radio"]:checked')) {
                item.remove();
            }
        });
    })
    .catch(error => console.error('Error:', error));
}
