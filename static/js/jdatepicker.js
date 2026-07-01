/* هیرکان — self-hosted Jalali (Shamsi) date picker. No CDN, no jQuery.
   Enhances every [data-jdate]: shows a Jalali calendar, writes a Gregorian ISO
   value to the hidden field so Django stores Gregorian unchanged.
   Conversion math: jalaali-js (Behrang Noruzi Niya / Roozbeh Pournader), MIT. */
(function () {
  "use strict";

  /* ---- jalaali-js conversion core ---- */
  function div(a, b) { return ~~(a / b); }
  function mod(a, b) { return a - ~~(a / b) * b; }
  function jalCal(jy, withoutLeap) {
    var breaks = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
      1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178];
    var bl = breaks.length, gy = jy + 621, leapJ = -14, jp = breaks[0];
    var jm, jump, leap, leapG, march, n, i;
    if (jy < jp || jy >= breaks[bl - 1]) throw new Error("bad jy " + jy);
    for (i = 1; i < bl; i += 1) {
      jm = breaks[i]; jump = jm - jp;
      if (jy < jm) break;
      leapJ = leapJ + div(jump, 33) * 8 + div(mod(jump, 33), 4); jp = jm;
    }
    n = jy - jp;
    leapJ = leapJ + div(n, 33) * 8 + div(mod(n, 33) + 3, 4);
    if (mod(jump, 33) === 4 && jump - n === 4) leapJ += 1;
    leapG = div(gy, 4) - div((div(gy, 100) + 1) * 3, 4) - 150;
    march = 20 + leapJ - leapG;
    if (!withoutLeap) {
      if (jump - n < 6) n = n - jump + div(jump + 4, 33) * 33;
      leap = mod(mod(n + 1, 33) - 1, 4);
      if (leap === -1) leap = 4;
    }
    return { leap: leap, gy: gy, march: march };
  }
  function g2d(gy, gm, gd) {
    var d = div((gy + div(gm - 8, 6) + 100100) * 1461, 4)
      + div(153 * mod(gm + 9, 12) + 2, 5) + gd - 34840408;
    d = d - div(div(gy + 100100 + div(gm - 8, 6), 100) * 3, 4) + 752;
    return d;
  }
  function d2g(jdn) {
    var j, i, gd, gm, gy;
    j = 4 * jdn + 139361631;
    j = j + div(div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908;
    i = div(mod(j, 1461), 4) * 5 + 308;
    gd = div(mod(i, 153), 5) + 1;
    gm = mod(div(i, 153), 12) + 1;
    gy = div(j, 1461) - 100100 + div(8 - gm, 6);
    return { gy: gy, gm: gm, gd: gd };
  }
  function j2d(jy, jm, jd) {
    var r = jalCal(jy, true);
    return g2d(r.gy, 3, r.march) + (jm - 1) * 31 - div(jm, 7) * (jm - 7) + jd - 1;
  }
  function d2j(jdn) {
    var gy = d2g(jdn).gy, jy = gy - 621, r = jalCal(jy, false);
    var jdn1f = g2d(gy, 3, r.march), jd, jm, k = jdn - jdn1f;
    if (k >= 0) {
      if (k <= 185) { jm = 1 + div(k, 31); jd = mod(k, 31) + 1; return { jy: jy, jm: jm, jd: jd }; }
      k -= 186;
    } else { jy -= 1; k += 179; if (r.leap === 1) k += 1; }
    jm = 7 + div(k, 30); jd = mod(k, 30) + 1;
    return { jy: jy, jm: jm, jd: jd };
  }
  function toJalaali(gy, gm, gd) { return d2j(g2d(gy, gm, gd)); }
  function toGregorian(jy, jm, jd) { return d2g(j2d(jy, jm, jd)); }
  function isLeapJalaaliYear(jy) { return jalCal(jy, false).leap === 0; }
  function monthLen(jy, jm) {
    if (jm <= 6) return 31; if (jm <= 11) return 30;
    return isLeapJalaaliYear(jy) ? 30 : 29;
  }

  /* ---- helpers ---- */
  var MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];
  var WEEK = ["ش", "ی", "د", "س", "چ", "پ", "ج"];
  function fa(s) { return String(s).replace(/[0-9]/g, function (d) { return "۰۱۲۳۴۵۶۷۸۹"[d]; }); }
  function pad(n) { return n < 10 ? "0" + n : "" + n; }
  // Jalali weekday index, Saturday = 0
  function jWeekday(g) { return (new Date(g.gy, g.gm - 1, g.gd).getDay() + 1) % 7; }

  /* ---- picker ---- */
  function attach(root) {
    var display = root.querySelector(".jdate__display");
    var hidden = root.querySelector(".jdate__value");
    if (!display || !hidden) return;

    var pop = document.createElement("div");
    pop.className = "jdate__pop"; pop.setAttribute("role", "dialog"); pop.hidden = true;
    root.appendChild(pop);

    var today = new Date();
    var view; // {jy, jm}
    var sel = null; // {jy, jm, jd}

    function syncFromHidden() {
      if (hidden.value) {
        var p = hidden.value.split("-");
        var j = toJalaali(+p[0], +p[1], +p[2]);
        sel = j; view = { jy: j.jy, jm: j.jm };
        display.value = fa(j.jy + "/" + pad(j.jm) + "/" + pad(j.jd));
      } else {
        var tj = toJalaali(today.getFullYear(), today.getMonth() + 1, today.getDate());
        view = { jy: tj.jy, jm: tj.jm };
      }
    }
    syncFromHidden();

    function choose(jy, jm, jd) {
      var g = toGregorian(jy, jm, jd);
      hidden.value = g.gy + "-" + pad(g.gm) + "-" + pad(g.gd);
      display.value = fa(jy + "/" + pad(jm) + "/" + pad(jd));
      sel = { jy: jy, jm: jm, jd: jd };
      hidden.dispatchEvent(new Event("change", { bubbles: true }));
      close();
    }

    function render() {
      var tj = toJalaali(today.getFullYear(), today.getMonth() + 1, today.getDate());
      var g1 = toGregorian(view.jy, view.jm, 1);
      var startCol = jWeekday(g1);
      var len = monthLen(view.jy, view.jm);
      var html = '<div class="jdate__bar">'
        + '<button type="button" class="jdate__nav" data-step="-1" aria-label="ماه قبل">›</button>'
        + '<span class="jdate__title">' + MONTHS[view.jm - 1] + " " + fa(view.jy) + "</span>"
        + '<button type="button" class="jdate__nav" data-step="1" aria-label="ماه بعد">‹</button>'
        + "</div><div class=\"jdate__grid\">";
      WEEK.forEach(function (w) { html += '<span class="jdate__wd">' + w + "</span>"; });
      for (var i = 0; i < startCol; i++) html += '<span class="jdate__cell jdate__cell--empty"></span>';
      for (var d = 1; d <= len; d++) {
        var cls = "jdate__cell";
        if (sel && sel.jy === view.jy && sel.jm === view.jm && sel.jd === d) cls += " is-selected";
        if (tj.jy === view.jy && tj.jm === view.jm && tj.jd === d) cls += " is-today";
        html += '<button type="button" class="' + cls + '" data-day="' + d + '">' + fa(d) + "</button>";
      }
      html += '</div><div class="jdate__foot">'
        + '<button type="button" class="jdate__btn" data-today>امروز</button>'
        + '<button type="button" class="jdate__btn jdate__btn--clear" data-clear>پاک کردن</button>'
        + "</div>";
      pop.innerHTML = html;
    }

    function open() { syncFromHidden(); render(); pop.hidden = false; }
    function close() { pop.hidden = true; }
    function toggle() { pop.hidden ? open() : close(); }

    display.addEventListener("focus", open);
    display.addEventListener("click", open);
    var icon = root.querySelector(".jdate__icon");
    if (icon) icon.addEventListener("click", function (e) { e.preventDefault(); toggle(); });

    pop.addEventListener("click", function (e) {
      var nav = e.target.closest("[data-step]");
      if (nav) {
        view.jm += +nav.getAttribute("data-step");
        if (view.jm < 1) { view.jm = 12; view.jy -= 1; }
        if (view.jm > 12) { view.jm = 1; view.jy += 1; }
        render(); return;
      }
      var day = e.target.closest("[data-day]");
      if (day) { choose(view.jy, view.jm, +day.getAttribute("data-day")); return; }
      if (e.target.closest("[data-today]")) {
        var tj = toJalaali(today.getFullYear(), today.getMonth() + 1, today.getDate());
        choose(tj.jy, tj.jm, tj.jd); return;
      }
      if (e.target.closest("[data-clear]")) {
        hidden.value = ""; display.value = ""; sel = null;
        hidden.dispatchEvent(new Event("change", { bubbles: true })); close(); return;
      }
    });

    document.addEventListener("click", function (e) {
      if (!root.contains(e.target)) close();
    });
    display.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
      if (e.key === "Enter") { e.preventDefault(); toggle(); }
    });
  }

  function init() {
    document.querySelectorAll("[data-jdate]").forEach(function (el) {
      if (!el.__jdate) { el.__jdate = true; attach(el); }
    });
  }
  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
