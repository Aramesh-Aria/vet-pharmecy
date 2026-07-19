/* Prescription admin: limit the medication dropdown to the chosen pet's
   Animal Category. The animal autocomplete result carries `category_id`
   (core.admin_site.VetAutocompleteJsonView); each product option carries
   `data-category` (core.widgets.CategoryDataSelect). Server-side validation
   still enforces the rule — this is just to guide the staff member. */
(function () {
  "use strict";
  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }
  ready(function () {
    var $ = window.django && window.django.jQuery;
    var animal = document.getElementById("id_animal");
    var product = document.getElementById("id_product");
    if (!animal || !product) return;

    function filter(catId) {
      catId = catId == null ? null : String(catId);
      var reset = false;
      Array.prototype.forEach.call(product.options, function (o) {
        if (!o.value) { o.hidden = false; return; } // keep the empty option
        var oc = o.getAttribute("data-category");
        var show = catId === null || oc === catId;
        o.hidden = !show;
        o.disabled = !show;
        if (!show && o.selected) reset = true;
      });
      if (reset) {
        product.value = "";
        if ($) $(product).trigger("change");
      }
    }

    // Change form: a medication is already chosen — filter to its category.
    var sel = product.options[product.selectedIndex];
    if (sel && sel.value && sel.getAttribute("data-category")) {
      filter(sel.getAttribute("data-category"));
    }

    if ($) {
      $(animal).on("select2:select", function (e) {
        var d = e.params && e.params.data;
        filter(d ? d.category_id : null);
      });
      $(animal).on("select2:clear", function () { filter(null); });
    }
  });
})();
