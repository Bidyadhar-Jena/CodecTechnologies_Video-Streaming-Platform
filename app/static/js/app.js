document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener("change", () => {
            const file = fileInput.files[0];
            if (file && file.size > 500 * 1024 * 1024) {
                alert("The selected file is larger than 500 MB.");
                fileInput.value = "";
            }
        });
    }

    document.querySelectorAll(".flash").forEach((item) => {
        setTimeout(() => {
            item.style.opacity = "0";
            item.style.transition = "opacity .4s";
            setTimeout(() => item.remove(), 400);
        }, 4500);
    });
});
