(function () {
  // Mobile sections menu
  var btn = document.querySelector("[data-menu]"), nav = document.getElementById("sections");
  if (btn && nav) btn.addEventListener("click", function () {
    var open = nav.classList.toggle("open");
    btn.setAttribute("aria-expanded", open);
  });

  // Dates computed in the reader's browser so cached pages stay current
  var n = new Date(); n.setHours(0, 0, 0, 0);
  var t = document.querySelector("[data-today]");
  if (t) t.textContent = n.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
  document.querySelectorAll("[data-countdown]").forEach(function (c) {
    var p = c.dataset.date.split("-"), e = new Date(+p[0], +p[1] - 1, +p[2]);
    var d = Math.round((e - n) / 86400000);
    c.textContent = d > 1 ? d + " days to Election Day" : d === 1 ? "Election Day is tomorrow"
      : d === 0 ? "Election Day is today" : "";
  });

  // State picker → vote.gov
  var f = document.getElementById("picker");
  if (f) f.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var v = f.querySelector("select").value;
    if (v) window.location.href = "https://vote.gov/register/" + v;
  });

  // State filter on results list
  document.querySelectorAll("[data-filter]").forEach(function (inp) {
    var items = document.querySelectorAll(inp.dataset.filter);
    inp.addEventListener("input", function () {
      var q = inp.value.trim().toLowerCase();
      items.forEach(function (a) { a.hidden = !!q && a.dataset.name.indexOf(q) === -1; });
    });
  });
})();
