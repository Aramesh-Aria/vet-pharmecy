/* Auth forms: focus the first field, and let Enter move to the next field
   until the last one, where Enter submits. Marked with `data-enter-nav`. */
(function () {
  "use strict";
  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }
  ready(function () {
    document.querySelectorAll("form[data-enter-nav]").forEach(function (form) {
      var fields = Array.prototype.filter.call(
        form.querySelectorAll("input, select, textarea"),
        function (el) {
          return el.type !== "hidden" && el.type !== "submit" &&
            el.type !== "button" && !el.disabled && el.offsetParent !== null;
        }
      );
      if (!fields.length) return;

      // Cursor starts at the first field (unless one already has autofocus).
      if (!form.querySelector("[autofocus]")) fields[0].focus();

      fields.forEach(function (el, i) {
        el.addEventListener("keydown", function (e) {
          if (e.key !== "Enter" || e.isComposing || el.tagName === "TEXTAREA") return;
          e.preventDefault();
          if (i < fields.length - 1) {
            fields[i + 1].focus();
          } else if (form.requestSubmit) {
            form.requestSubmit();
          } else {
            form.submit();
          }
        });
      });
    });
  });
})();
