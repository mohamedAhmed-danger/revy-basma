/**
 * Revy Basma — app.js
 * Client-side interactivity, responsive mobile drawer, auto-dismiss toasts, and live search.
 */

(function () {
  "use strict";

  function initFlashDismiss() {
    var AUTO_DISMISS_MS = 5000;

    document.querySelectorAll(".flash").forEach(function (flash) {
      var timer = window.setTimeout(function () {
        fadeAndRemove(flash);
      }, AUTO_DISMISS_MS);

      flash.addEventListener("mouseenter", function () {
        window.clearTimeout(timer);
      });

      var dismissBtn = flash.querySelector(".flash__dismiss");
      if (dismissBtn) {
        dismissBtn.addEventListener("click", function () {
          window.clearTimeout(timer);
          fadeAndRemove(flash);
        });
      }
    });
  }

  function fadeAndRemove(el) {
    el.style.transition = "opacity 0.25s ease, transform 0.25s ease";
    el.style.opacity = "0";
    el.style.transform = "translateY(-4px)";
    window.setTimeout(function () {
      el.remove();
    }, 250);
  }

  function initAdminMobileNav() {
    var toggle = document.getElementById("admin-nav-toggle");
    var sidebar = document.getElementById("admin-sidebar");
    var backdrop = document.getElementById("admin-sidebar-backdrop");

    if (!toggle || !sidebar || !backdrop) {
      return;
    }

    function openNav() {
      sidebar.classList.add("is-open");
      backdrop.style.display = "block";
      toggle.setAttribute("aria-expanded", "true");
    }

    function closeNav() {
      sidebar.classList.remove("is-open");
      backdrop.style.display = "none";
      toggle.setAttribute("aria-expanded", "false");
    }

    toggle.addEventListener("click", function () {
      if (sidebar.classList.contains("is-open")) {
        closeNav();
      } else {
        openNav();
      }
    });

    backdrop.addEventListener("click", closeNav);

    sidebar.querySelectorAll(".admin-nav__link, .admin-sidebar__logout").forEach(function (link) {
      link.addEventListener("click", closeNav);
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 992) {
        closeNav();
      }
    });
  }

  function initAdminLiveSearch() {
    var searchInput = document.getElementById("global-admin-search") || document.querySelector(".admin-search__input");
    if (!searchInput) return;

    searchInput.addEventListener("input", function () {
      var query = this.value.toLowerCase().trim();
      var rows = document.querySelectorAll("table.table tbody tr");
      rows.forEach(function (row) {
        var text = row.textContent.toLowerCase();
        if (query === "" || text.indexOf(query) !== -1) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initFlashDismiss();
    initAdminMobileNav();
    initAdminLiveSearch();
  });
})();
