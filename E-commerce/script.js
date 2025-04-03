const menuBtn = document.getElementById("menuBtn");
const navList = document.querySelector(".nav_list");
const minusButton = document.querySelector("#minusBtn");
const plusButton = document.querySelector("#plusBtn");
const itemAmount = document.querySelector(".quantity_form input");
const button = document.createElement("button");

menuBtn.addEventListener("click", () => {
  navList.classList.toggle("active");
  menuBtn.classList.toggle("active");
});

minusButton.addEventListener("click", () => {
  itemValue = parseInt(itemAmount.value);
  itemAmount.textContent = itemValue - 1;
  itemAmount.value = itemValue - 1;
});

plusButton.addEventListener("click", () => {
  itemValue = parseInt(itemAmount.value);
  itemAmount.textContent = itemValue + 1;
  itemAmount.value = itemValue + 1;
});

const tBody = document.querySelector('.tBody')

tBody.querySelectorAll('tr').forEach(tr => {
  const tdatas = tr.querySelectorAll('td')
  const price = Number(tdatas[1].textContent)
  tdatas[2].querySelectorAll('form button').forEach(button => {
    button.addEventListener("click", () => {
      let itemCount = tdatas[2].querySelector('input').value
      tdatas[3].textContent = parseInt(itemCount) * price
    })
  })
})

document.addEventListener("DOMContentLoaded", function () {
  const buyButtons = document.querySelectorAll(".buy_button");
  const modal = document.getElementById("errorModal");
  const closeBtn = document.querySelector(".close-btn");

  buyButtons.forEach((button) => {
      button.addEventListener("click", function (event) {
          event.preventDefault(); // Prevent default action

          // Check if there are products (dummy check for now)
          const productExists = document.querySelector(".product_card");
          
          if (!productExists) {
              modal.style.display = "flex"; // Show modal
          } else {
              window.location.href = "/cart"; // Redirect to cart if products exist
          }
      });
  });

  // Close modal when clicking "X" button
  closeBtn.addEventListener("click", function () {
      modal.style.display = "none";
  });

  // Close modal when clicking outside of it
  window.addEventListener("click", function (event) {
      if (event.target === modal) {
          modal.style.display = "none";
      }
  });
});
