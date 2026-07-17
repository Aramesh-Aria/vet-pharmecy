/* Appointment request: show only services that belong to the chosen subject's
   Animal Category. Subject options and service options each carry
   `data-category` (core.widgets.CategoryDataSelect). Server-side validation
   still enforces the match. */
(function () {
  "use strict";
  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }
  ready(function () {
    var subject = document.getElementById("id_subject");
    var service = document.getElementById("id_service");
    if (!subject || !service) return;

    function filter() {
      var opt = subject.options[subject.selectedIndex];
      var cat = opt ? opt.getAttribute("data-category") : null;
      var reset = false;
      Array.prototype.forEach.call(service.options, function (o) {
        if (!o.value) { o.hidden = false; return; } // keep the empty option
        var show = cat == null || o.getAttribute("data-category") === cat;
        o.hidden = !show;
        o.disabled = !show;
        if (!show && o.selected) reset = true;
      });
      if (reset) service.value = "";
    }

    subject.addEventListener("change", filter);
    filter(); // apply on load
  });
})();
