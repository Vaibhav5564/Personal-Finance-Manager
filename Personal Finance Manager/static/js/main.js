// Check JS is loaded
console.log("Finance Manager JS Loaded");

// Confirmation before deleting transaction
document.addEventListener("DOMContentLoaded", function () {

    const deleteButtons = document.querySelectorAll(".delete-btn");

    deleteButtons.forEach(button => {
        button.addEventListener("click", function (e) {

            const confirmDelete = confirm("Are you sure you want to delete this transaction?");

            if (!confirmDelete) {
                e.preventDefault();
            }

        });
    });

});