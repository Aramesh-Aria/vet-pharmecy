/* هیرکان — progressive enhancement only. No framework; the site works without JS.
   1) mark <html> as js-enabled (gates the CSS load-in animation)
   2) mobile nav drawer
   3) quantity steppers (enhances plain number inputs)
   4) image upload filename + preview                                       */
(function () {
  "use strict";
  document.documentElement.classList.add("js");

  /* ---- mobile nav ---- */
  function initNav() {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("primary-nav");
    var backdrop = document.querySelector(".nav-backdrop");
    if (!toggle || !nav) return;

    function setOpen(open) {
      nav.setAttribute("data-open", open ? "true" : "false");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      if (backdrop) backdrop.setAttribute("data-open", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    }
    toggle.addEventListener("click", function () {
      setOpen(nav.getAttribute("data-open") !== "true");
    });
    if (backdrop) backdrop.addEventListener("click", function () { setOpen(false); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setOpen(false);
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });
  }

  /* Entrance animation is pure CSS (.js .reveal { animation }), triggered on load —
     no scroll dependency, so above-the-fold content is never hidden waiting to scroll. */

  /* ---- quantity steppers ---- */
  function initSteppers() {
    document.querySelectorAll("[data-qty]").forEach(function (input) {
      var wrap = document.createElement("span");
      wrap.className = "qty";
      input.parentNode.insertBefore(wrap, input);

      var minus = document.createElement("button");
      minus.type = "button"; minus.textContent = "−"; minus.setAttribute("aria-label", "کاهش");
      var plus = document.createElement("button");
      plus.type = "button"; plus.textContent = "+"; plus.setAttribute("aria-label", "افزایش");

      wrap.appendChild(plus); wrap.appendChild(input); wrap.appendChild(minus); /* RTL visual order */

      function clamp(v) {
        var min = input.min !== "" ? Number(input.min) : -Infinity;
        var max = input.max !== "" ? Number(input.max) : Infinity;
        return Math.max(min, Math.min(max, v));
      }
      function step(d) {
        input.value = clamp((Number(input.value) || 0) + d);
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }
      plus.addEventListener("click", function () { step(1); });
      minus.addEventListener("click", function () { step(-1); });
    });
  }

  /* ---- pretty image upload (filename + live preview) ---- */
  function initFileFields() {
    document.querySelectorAll("[data-filefield]").forEach(function (wrap) {
      var input = wrap.querySelector(".filefield__input");
      var nameEl = wrap.querySelector("[data-filename]");
      var preview = wrap.querySelector("[data-preview]");
      if (!input) return;
      input.addEventListener("change", function () {
        var file = input.files && input.files[0];
        if (!file) return;
        if (nameEl) nameEl.textContent = file.name;
        wrap.classList.add("has-file");
        if (preview && file.type.indexOf("image/") === 0) {
          var reader = new FileReader();
          reader.onload = function (e) { preview.src = e.target.result; preview.hidden = false; };
          reader.readAsDataURL(file);
        }
      });
    });
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }
  ready(function () { initNav(); initSteppers(); initFileFields(); });
})();
