// Mobile Menu Toggle
const menuBtn = document.getElementById('menu-btn');
const mobileMenu = document.getElementById('mobile-menu');

menuBtn.addEventListener('click', () => {
    menuBtn.classList.toggle('active');
    mobileMenu.classList.toggle('active');
});

// Quick View Modal
const quickViewBtns = document.querySelectorAll('.quick-view-btn');
const quickViewModal = document.getElementById('quick-view-modal');
const closeModalBtn = document.querySelector('.close-modal');

quickViewBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        quickViewModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    });
});

closeModalBtn.addEventListener('click', () => {
    quickViewModal.classList.remove('active');
    document.body.style.overflow = 'auto';
});

quickViewModal.addEventListener('click', (e) => {
    if (e.target === quickViewModal) {
        quickViewModal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
});

// Add to Cart Functionality
const addToCartBtns = document.querySelectorAll('.add-to-cart-btn');
const cartNotification = document.getElementById('cart-notification');

addToCartBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // In a real app, you would add the product to cart here
        // For demo purposes, we'll just show a notification
        cartNotification.classList.remove('hidden');
        
        // Hide notification after 3 seconds
        setTimeout(() => {
            cartNotification.classList.add('hidden');
        }, 3000);
    });
});

// Newsletter Form Submission
const newsletterForm = document.querySelector('form');

newsletterForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const emailInput = newsletterForm.querySelector('input[type="email"]');
    
    // In a real app, you would send this to your backend
    alert(`Thank you for subscribing with ${emailInput.value}! You'll receive our beauty tips soon.`);
    emailInput.value = '';
});

// Search Functionality
const searchBtn = document.querySelector('button[aria-label="Search"]');

searchBtn.addEventListener('click', () => {
    // In a real app, this would open a search bar or modal
    alert('Search functionality would appear here');
});

// Account Button
const accountBtn = document.querySelector('button[aria-label="Account"]');

accountBtn.addEventListener('click', () => {
    // In a real app, this would open account/login modal
    alert('Account/login modal would appear here');
});

// Cart Button
const cartBtn = document.querySelector('button[aria-label="Cart"]');

cartBtn.addEventListener('click', () => {
    // In a real app, this would open cart sidebar
    alert('Cart sidebar would appear here');
});