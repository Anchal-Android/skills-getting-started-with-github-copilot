// Mark that the main client app is active as early as possible so inline scripts can opt-out
window.__serverApp = true;

document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");



  // Helpers
  const slug = (s = "") => s.toLowerCase().trim().replace(/[^\w]+/g, "-").replace(/^-|-$/g, "");
  const getInitials = (email) => {
    const name = email.split("@")[0].replace(/[._-]/g, " ");
    const parts = name.trim().split(/\s+/);
    return ((parts[0] ? parts[0][0] : "") + (parts[1] ? parts[1][0] : "")).slice(0, 2).toUpperCase() || email.slice(0, 2).toUpperCase();
  };

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities", { cache: "no-store" });
      const activities = await response.json();
      console.debug("fetchActivities: received activities", activities);

      // Clear loading message and reset select to avoid duplicates
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const id = details.id || slug(name);
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";
        activityCard.dataset.activityId = id;
        const spotsLeft = details.max_participants - details.participants.length;
        activityCard.dataset.spots = spotsLeft;

        activityCard.innerHTML = `
          <h4 class="activity-title">${name} <span class="count-badge" aria-hidden="true">${details.participants.length}</span></h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p class="availability"><strong>Availability:</strong> <span class="spots-left">${spotsLeft}</span> spots left</p>
          <div class="participants">
            <h4>Participants</h4>
            <ul class="participants-list">
              ${details.participants.length ? details.participants.map(email => `<li><span class="participant-badge">${getInitials(email)}</span><span class="participant-email">${email}</span><button class="remove-participant" data-email="${email}" aria-label="Remove ${email}">✖</button></li>`).join('') : '<li class="empty">No participants yet</li>'}
            </ul>
          </div>
        `;
        activitiesList.appendChild(activityCard);
        console.debug(`renderActivity: ${id} participants=`, details.participants);

        // Add option to select dropdown (use slug/id as value)
        const option = document.createElement("option");
        option.value = id;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
          cache: "no-store"
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "message success";
        signupForm.reset();

        // Update UI: add participant to activity card and update counts/availability
        const card = document.querySelector(`[data-activity-id="${activity}"]`);
        if (card) {
          // update participants list
          const ul = card.querySelector(".participants-list");
          if (ul) {
            const empty = ul.querySelector(".empty");
            if (empty) empty.remove();
            const li = document.createElement("li");
            li.innerHTML = `<span class="participant-badge">${getInitials(email)}</span><span class="participant-email">${email}</span><button class="remove-participant" data-email="${email}" aria-label="Remove ${email}">✖</button>`;
            ul.appendChild(li);
          }
          // update count badge
          const badge = card.querySelector(".count-badge");
          if (badge) badge.textContent = String(Number(badge.textContent || 0) + 1);
          // update availability
          let spots = Number(card.dataset.spots || 0);
          if (spots > 0) spots -= 1;
          card.dataset.spots = spots;
          const spotsEl = card.querySelector(".spots-left");
          if (spotsEl) spotsEl.textContent = String(spots);
        }

        // Refresh activities from the server to ensure UI matches backend and avoid clashes with any inline script
        await fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "message error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "message error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Handle remove participant clicks (event delegation)
  activitiesList.addEventListener("click", async (e) => {
    const btn = e.target.closest(".remove-participant");
    if (!btn) return;
    const email = btn.dataset.email;
    const activityCard = btn.closest(".activity-card");
    const activityId = activityCard && activityCard.dataset.activityId;
    if (!activityId || !email) return;
    if (!confirm(`Unregister ${email} from this activity?`)) return;
    try {
      const response = await fetch(`/activities/${encodeURIComponent(activityId)}/participants?email=${encodeURIComponent(email)}`, { method: "DELETE", cache: "no-store" });
      const result = await response.json();
      if (response.ok) {
        const li = btn.closest("li");
        if (li) li.remove();
        const ul = activityCard.querySelector(".participants-list");
        if (ul && !ul.querySelector("li")) {
          const emptyLi = document.createElement("li");
          emptyLi.className = "empty";
          emptyLi.textContent = "No participants yet";
          ul.appendChild(emptyLi);
        }
        const badge = activityCard.querySelector(".count-badge");
        if (badge) badge.textContent = String(Math.max(0, Number(badge.textContent || 0) - 1));
        let spots = Number(activityCard.dataset.spots || 0);
        spots += 1;
        activityCard.dataset.spots = spots;
        const spotsEl = activityCard.querySelector(".spots-left");
        if (spotsEl) spotsEl.textContent = String(spots);
        messageDiv.textContent = result.message || `Unregistered ${email}`;
        messageDiv.className = "message success";
      } else {
        messageDiv.textContent = result.detail || "Failed to unregister";
        messageDiv.className = "message error";
      }
      messageDiv.classList.remove("hidden");
      setTimeout(() => messageDiv.classList.add("hidden"), 4000);
    } catch (err) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "message error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", err);
    }
  });

  // Initialize app
  fetchActivities();
});
