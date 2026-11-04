/* Runs in <head> before the page paints, so there is no light/dark flash. */
(function () {
  try {
    var saved = localStorage.getItem("theme");
    if (saved === "dark" || saved === "light") {
      document.documentElement.setAttribute("data-theme", saved);
    }
  } catch (e) { /* storage blocked: follow the system setting */ }
})();
