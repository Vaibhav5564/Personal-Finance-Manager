// simple console message to check JS working
console.log("Finance Manager JS Loaded");


// confirmation before deleting transaction
document.addEventListener("DOMContentLoaded", function () {

    const deleteButtons = document.querySelectorAll(".btn-danger");

    deleteButtons.forEach(button => {
        button.addEventListener("click", function (e) {

            const confirmDelete = confirm("Are you sure you want to delete this transaction?");

            if (!confirmDelete) {
                e.preventDefault(); // stop deletion
            }
        });
    });

});