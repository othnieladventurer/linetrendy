document.addEventListener('click', function(e) {
    console.log('You clicked on:', e.target);
});


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

// Newsletter Subscription
// Newsletter Subscription
document.getElementById("newsletterForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const emailInput = document.getElementById("emailInput");
  const btn = document.getElementById("subscribeBtn");
  const email = emailInput.value.trim();

  if (!email) {
    alert("Please enter a valid email.");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Subscribing...";

  try {
    const response = await fetch("/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();

    if (data.success) {
      btn.textContent = "Subscribed ✓";
      btn.classList.remove("bg-blue-500", "hover:bg-blue-600");
      btn.classList.add("bg-green-500");
    } else {
      btn.textContent = data.message;
      btn.disabled = false;
    }
  } catch (error) {
    btn.textContent = "Error! Try again.";
    btn.disabled = false;
  }
});

// Helper to get CSRF token from cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Helper for CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}


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








// Add to Cart AJAX Functionality
document.addEventListener("DOMContentLoaded", function() {
    // Select all Add to Cart buttons
    const buttons = document.querySelectorAll(".add-to-cart-btn");

    buttons.forEach(button => {
        button.addEventListener("click", function() {
            const productId = this.dataset.id;

            fetch("{% url 'shop:add_to_cart' %}", {
                method: "POST",
                headers: {
                    "X-CSRFToken": "{{ csrf_token }}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: new URLSearchParams({
                    product_id: productId,
                    quantity: 1
                })
            })
            .then(response => {
                // Handle redirect to login
                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }
                return response.json();
            })
            .then(data => {
                if (!data) return; // redirected
                if (data.success) {
                    // Update cart count badge
                    const cartCount = document.querySelector("#cart-count");
                    cartCount.textContent = data.cart_count;
                } else {
                    alert("Could not add product to cart.");
                }
            })
            .catch(error => {
                console.error("Error adding to cart:", error);
            });
        });
    });
});









document.addEventListener('htmx:afterRequest', function(evt) {
    const form = evt.target.closest('.add-to-cart-form');
    if (!form) return;

    const button = form.querySelector('button[type="submit"]');
    if (!button) return;

    // Temporarily change text to "Added to Cart"
    const originalText = button.textContent;
    button.textContent = "Added to Cart";
    button.disabled = true;

    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
    }, 5000); // 5 seconds
});





//owl-carousel 
$(document).ready(function(){
    $(".owl-carousel").owlCarousel({
        loop: true,
        margin: 20,
        nav: false,
        dots: true,
        autoplay: true,
        autoplayTimeout: 4000,
        responsive: {
            0: { items: 1 },
            768: { items: 2 },
            1024: { items: 3 }
        }
    });
});



// Account page Js
function showTab(tab) {
    const tabs = ['orders', 'address', 'profile'];
    tabs.forEach(t => {
      document.getElementById(`${t}-tab`).classList.add('hidden');
      document.getElementById(`tab-${t}-btn`).classList.remove('text-red-600', 'font-bold');
    });
    document.getElementById(`${tab}-tab`).classList.remove('hidden');
    document.getElementById(`tab-${tab}-btn`).classList.add('text-red-600', 'font-bold');
  }
  showTab('orders'); // default tab

  function toggleOrder(orderId) {
    document.getElementById(`order-${orderId}`).classList.toggle('hidden');
  }

  // Cancel modal
  function openCancelModal(orderNumber) {
    const modal = document.getElementById('cancelModal');
    document.getElementById('cancelOrderForm').action = `/cancel-order/${orderNumber}/`;
    modal.classList.remove('hidden'); modal.classList.add('flex');
  }
  function closeCancelModal() {
    const modal = document.getElementById('cancelModal');
    modal.classList.add('hidden'); modal.classList.remove('flex');
  }

  // Address modal
  function openAddressModal() {
    const modal = document.getElementById('addressModal');
    modal.classList.remove('hidden'); modal.classList.add('flex');
  }
  function closeAddressModal() {
    const modal = document.getElementById('addressModal');
    modal.classList.add('hidden'); modal.classList.remove('flex');
  }




// Faw expand collapse page 

