/* Landlord-Tenant Direct Connect - shared frontend behaviour.
 *
 * Kept dependency-free (vanilla JS). Provides:
 * - auto-dismissal of Django message alerts after a short delay
 * - a confirmation guard on any form marked with data-confirm
 */
(function () {
  "use strict";

  // Auto-dismiss flash messages (e.g. success notices) after 5 seconds so they
  // do not permanently occupy the page top.
  document.querySelectorAll(".messages .alert").forEach(function (alert) {
    setTimeout(function () {
      var close = alert.querySelector(".btn-close");
      if (close) close.click();
    }, 5000);
  });

  // Confirmation guard for destructive actions (search forms tag buttons with
  // data-confirm and a message via data-confirm-text).
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var text = form.getAttribute("data-confirm-text") || "Are you sure?";
      if (!window.confirm(text)) {
        event.preventDefault();
      }
    });
  });
})();