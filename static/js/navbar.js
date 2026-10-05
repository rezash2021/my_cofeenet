const mobileMenuButton = document.getElementById("mobile-menu-button");
const mobileMenu = document.getElementById("mobile-menu");
const mobileMenuIcon = document.getElementById("mobile-menu-icon");

mobileMenuButton.addEventListener("click",function(){

    mobileMenu.classList.toggle("hidden");

    const isOpen = !mobileMenu.classList.contains("hidden");

    mobileMenuButton.setAttribute("aria-expanded",isOpen);

    mobileMenuButton.setAttribute("aria-label",isOpen ? "باز کردن منو" : "بستن منو");

    mobileMenuIcon.textContent = isOpen ? "✕" : "☰";
});