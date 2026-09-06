document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const toggleRegister = document.getElementById("toggle-register");
  const logoutButton = document.getElementById("logout-button");
  const currentUserDiv = document.getElementById("current-user");
  const authMessage = document.getElementById("auth-message");
  let accessToken = localStorage.getItem("accessToken");
  let currentUser = null;

  function authHeaders() {
    return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
  }

  function showAuthMessage(text, type = "error") {
    authMessage.textContent = text;
    authMessage.className = type;
  }

  function renderAuthState() {
    const authenticated = Boolean(accessToken && currentUser);
    loginForm.classList.toggle("hidden", authenticated);
    registerForm.classList.toggle("hidden", authenticated || !registerForm.classList.contains("show"));
    toggleRegister.classList.toggle("hidden", authenticated);
    logoutButton.classList.toggle("hidden", !authenticated);
    currentUserDiv.classList.toggle("hidden", !authenticated);
    if (authenticated) {
      currentUserDiv.textContent = `${currentUser.name} (${currentUser.role})`;
    }
    signupForm.querySelector("button").disabled = !authenticated;
  }

  async function loadCurrentUser() {
    if (!accessToken) {
      renderAuthState();
      return;
    }
    const response = await fetch("/auth/me", { headers: authHeaders() });
    if (response.ok) {
      currentUser = await response.json();
    } else {
      accessToken = null;
      localStorage.removeItem("accessToken");
    }
    renderAuthState();
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: authHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
          headers: authHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.getElementById("login-email").value,
        password: document.getElementById("login-password").value,
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      showAuthMessage(result.detail || "Unable to log in");
      return;
    }
    accessToken = result.access_token;
    currentUser = result.user;
    localStorage.setItem("accessToken", accessToken);
    showAuthMessage("Logged in", "success");
    renderAuthState();
  });

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: document.getElementById("register-name").value,
        email: document.getElementById("register-email").value,
        password: document.getElementById("register-password").value,
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      showAuthMessage(result.detail || "Unable to create account");
      return;
    }
    registerForm.classList.remove("show");
    registerForm.classList.add("hidden");
    loginForm.classList.remove("hidden");
    showAuthMessage("Account created. Please log in.", "success");
  });

  toggleRegister.addEventListener("click", () => {
    registerForm.classList.toggle("show");
    registerForm.classList.toggle("hidden");
    toggleRegister.textContent = registerForm.classList.contains("show")
      ? "Use existing account"
      : "Create an account";
  });

  logoutButton.addEventListener("click", async () => {
    await fetch("/auth/logout", { method: "POST", headers: authHeaders() });
    accessToken = null;
    currentUser = null;
    localStorage.removeItem("accessToken");
    showAuthMessage("Logged out", "success");
    renderAuthState();
  });

  // Initialize app
  loadCurrentUser();
  fetchActivities();
});
