// Handle dropdown menus
document.addEventListener("DOMContentLoaded", () => {
  const dropdownToggles = document.querySelectorAll(".dropdown-toggle")

  dropdownToggles.forEach((toggle) => {
    toggle.addEventListener("click", function (e) {
      e.preventDefault()
      e.stopPropagation() // Prevent event bubbling

      const dropdown = this.nextElementSibling

      // Close all other dropdowns first
      document.querySelectorAll(".dropdown-menu.show").forEach((menu) => {
        if (menu !== dropdown) {
          menu.classList.remove("show")
          menu.previousElementSibling.setAttribute("aria-expanded", "false")
        }
      })

      // Toggle current dropdown
      dropdown.classList.toggle("show")
      this.setAttribute("aria-expanded", dropdown.classList.contains("show"))
    })
  })

  // Close dropdowns when clicking outside
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".dropdown")) {
      document.querySelectorAll(".dropdown-menu.show").forEach((menu) => {
        menu.classList.remove("show")
        menu.previousElementSibling.setAttribute("aria-expanded", "false")
      })
    }
  })

  // Prevent dropdown from closing when clicking inside dropdown menu
  document.querySelectorAll(".dropdown-menu").forEach((menu) => {
    menu.addEventListener("click", (e) => {
      e.stopPropagation()
    })
  })

  // Global notification handlers for messages
  // Check for unread messages count
  function checkUnreadMessages() {
    fetch("/api/messages/unread/count")
      .then((response) => response.json())
      .then((data) => {
        const messagesBadge = document.getElementById("messages-badge")
        if (messagesBadge) {
          if (data.count > 0) {
            messagesBadge.textContent = data.count
            messagesBadge.style.display = "inline-flex"
          } else {
            messagesBadge.style.display = "none"
          }
        }
      })
      .catch((error) => console.error("Error checking unread messages:", error))
  }

  // Check for unread messages every 30 seconds
  if (document.body.dataset.loggedIn === "true") {
    checkUnreadMessages()
    setInterval(checkUnreadMessages, 30000)
  }

  // Handle message notifications via Socket.IO if available
  const io = window.io // Declare the io variable
  if (typeof io !== "undefined") {
    const socket = io()

    // Join user's room if logged in
    const userId = document.body.dataset.userId
    if (userId) {
      socket.emit("join", { user_id: userId })

      // Listen for new messages
      socket.on("new_message", (data) => {
        // Only show notification if we're not already in the conversation
        const currentPath = window.location.pathname
        const conversationPath = `/conversation/${data.sender_id}`

        if (currentPath !== conversationPath && data.sender_id !== userId) {
          // Update unread count
          checkUnreadMessages()

          // Show browser notification if supported
          if ("Notification" in window && Notification.permission === "granted") {
            const notification = new Notification("New message on SkillSwap", {
              body: "You have received a new message",
              icon: "/static/images/logo.png",
            })

            notification.onclick = () => {
              window.open(conversationPath, "_blank")
            }
          }
        }
      })
    }
  }

  // Request notification permission
  if ("Notification" in window && Notification.permission !== "denied") {
    Notification.requestPermission()
  }

  // Add active class to current navigation item
  const currentPath = window.location.pathname
  const navLinks = document.querySelectorAll(".nav-link")

  navLinks.forEach((link) => {
    const href = link.getAttribute("href")
    if (href === currentPath || (href !== "/" && currentPath.startsWith(href))) {
      link.classList.add("active")
    }
  })

  // Handle mobile navigation toggle
  const mobileMenuToggle = document.getElementById("mobile-menu-toggle")
  const mobileMenu = document.getElementById("mobile-menu")

  if (mobileMenuToggle && mobileMenu) {
    mobileMenuToggle.addEventListener("click", () => {
      mobileMenu.classList.toggle("show")
      mobileMenuToggle.setAttribute("aria-expanded", mobileMenu.classList.contains("show"))
    })
  }

  // Handle form validation
  const forms = document.querySelectorAll(".needs-validation")

  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!form.checkValidity()) {
        e.preventDefault()
        e.stopPropagation()
      }

      form.classList.add("was-validated")
    })
  })

  // Handle alerts auto-dismiss
  const alerts = document.querySelectorAll(".alert")

  alerts.forEach((alert) => {
    // Auto-dismiss success alerts after 5 seconds
    if (alert.classList.contains("alert-success")) {
      setTimeout(() => {
        alert.style.opacity = "0"
        setTimeout(() => {
          alert.remove()
        }, 300)
      }, 5000)
    }

    // Add close button functionality if it exists
    const closeBtn = alert.querySelector(".alert-close")
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        alert.style.opacity = "0"
        setTimeout(() => {
          alert.remove()
        }, 300)
      })
    }
  })

  // Handle smooth scrolling for anchor links
  const anchorLinks = document.querySelectorAll('a[href^="#"]')

  anchorLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      const href = link.getAttribute("href")
      if (href === "#") return

      const target = document.querySelector(href)
      if (target) {
        e.preventDefault()
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        })
      }
    })
  })

  // Handle loading states for buttons
  const loadingButtons = document.querySelectorAll(".btn-loading")

  loadingButtons.forEach((button) => {
    button.addEventListener("click", function () {
      if (!this.disabled) {
        this.disabled = true
        const originalText = this.innerHTML
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...'

        // Re-enable after 3 seconds (adjust as needed)
        setTimeout(() => {
          this.disabled = false
          this.innerHTML = originalText
        }, 3000)
      }
    })
  })

  // Handle tooltips (if you're using any)
  const tooltipElements = document.querySelectorAll("[data-tooltip]")

  tooltipElements.forEach((element) => {
    element.addEventListener("mouseenter", function () {
      const tooltipText = this.getAttribute("data-tooltip")
      const tooltip = document.createElement("div")
      tooltip.className = "tooltip"
      tooltip.textContent = tooltipText
      document.body.appendChild(tooltip)

      const rect = this.getBoundingClientRect()
      tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + "px"
      tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + "px"
    })

    element.addEventListener("mouseleave", () => {
      const tooltip = document.querySelector(".tooltip")
      if (tooltip) {
        tooltip.remove()
      }
    })
  })

  // Handle escape key to close dropdowns and modals
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      // Close all open dropdowns
      document.querySelectorAll(".dropdown-menu.show").forEach((menu) => {
        menu.classList.remove("show")
        if (menu.previousElementSibling) {
          menu.previousElementSibling.setAttribute("aria-expanded", "false")
        }
      })

      // Close mobile menu
      const mobileMenu = document.getElementById("mobile-menu")
      const mobileMenuToggle = document.getElementById("mobile-menu-toggle")
      if (mobileMenu && mobileMenu.classList.contains("show")) {
        mobileMenu.classList.remove("show")
        if (mobileMenuToggle) {
          mobileMenuToggle.setAttribute("aria-expanded", "false")
        }
      }
    }
  })
})

// Console log for debugging
console.log("SkillSwap main.js loaded successfully")
