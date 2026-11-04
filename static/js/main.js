/* XYZ Technologies Limited - site scripts */
(function () {
  "use strict";

  /* ---------- Mobile menu ---------- */
  var navToggle = document.getElementById("nav-toggle");
  var menu = document.getElementById("menu");
  if (navToggle && menu) {
    navToggle.addEventListener("click", function () {
      var open = menu.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* ---------- Light / dark toggle ---------- */
  var themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var root = document.documentElement;
      var current = root.getAttribute("data-theme") ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      var next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) { /* ignore */ }
    });
  }

  /* ---------- Contact form ---------- */
  var form = document.getElementById("contact-form");
  if (!form) return;

  var API_URL = form.dataset.url;
  var note = document.getElementById("form-note");
  var button = form.querySelector("button[type='submit']");

  function show(type, text) {
    note.className = "msg show " + type;
    note.textContent = text;
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();

    var data = {
      name: form.elements.name.value.trim(),
      email: form.elements.email.value.trim(),
      phone: form.elements.phone.value.trim(),
      topic: form.elements.topic.value,
      message: form.elements.message.value.trim(),
      nickname: form.elements.nickname.value
    };

    if (!data.name || !/^\S+@\S+\.\S+$/.test(data.email)) {
      show("err", "Please enter your name and a valid email address.");
      return;
    }
    if (data.message.length < 10) {
      show("err", "Please write a message of at least 10 characters.");
      return;
    }

    button.disabled = true;
    button.textContent = "Sending...";

    fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": form.elements.csrfmiddlewaretoken.value
      },
      body: JSON.stringify(data)
    })
      .then(function (res) {
        return res.json().then(function (body) {
          return { ok: res.ok && body.ok, body: body };
        });
      })
      .then(function (result) {
        if (result.ok) {
          show("ok", result.body.message);
          form.reset();
        } else {
          show("err", result.body.error || "Something went wrong. Please try again.");
        }
      })
      .catch(function () {
        show("err", "We could not reach the server. Please check your connection and try again.");
      })
      .finally(function () {
        button.disabled = false;
        button.textContent = "Send message";
      });
  });
})();
