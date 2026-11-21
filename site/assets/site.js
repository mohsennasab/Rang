(function () {
  "use strict";

  var STORAGE_KEY = "rang-theme";
  var root = document.documentElement;

  function applyTheme(theme) {
    if (theme === "dark") {
      root.dataset.theme = "dark";
    } else {
      delete root.dataset.theme;
    }
    var btn = document.querySelector("[data-theme-toggle]");
    if (!btn) return;
    var isDark = theme === "dark";
    btn.setAttribute("aria-pressed", String(isDark));
    var label = btn.querySelector(".theme-label");
    if (label) {
      label.textContent = isDark ? "Light" : "Dark";
    }
    var sun = btn.querySelector("[data-icon-sun]");
    var moon = btn.querySelector("[data-icon-moon]");
    if (sun && moon) {
      sun.style.display = isDark ? "inline" : "none";
      moon.style.display = isDark ? "none" : "inline";
    }
  }

  var initial = "light";
  try {
    if (localStorage.getItem(STORAGE_KEY) === "dark") {
      initial = "dark";
    }
  } catch (e) {
    /* ignore storage errors */
  }
  applyTheme(initial);

  var themeToggle = document.querySelector("[data-theme-toggle]");
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var next = root.dataset.theme === "dark" ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch (e) {
        /* ignore storage errors */
      }
    });
  }

  /* Mobile menu toggle */
  var navToggle = document.querySelector("[data-nav-toggle]");
  var navMenu = document.querySelector("[data-nav-menu]");
  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function () {
      var open = navMenu.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
    navMenu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        navMenu.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && navMenu.classList.contains("is-open")) {
        navMenu.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* Clipboard copy helpers */
  var announcer = document.getElementById("copy-announcer");
  var timers = new WeakMap();

  function copyText(value) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(value);
    }
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = value;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        var ok = document.execCommand("copy");
        document.body.removeChild(ta);
        if (ok) resolve();
        else reject(new Error("Copy failed"));
      } catch (err) {
        document.body.removeChild(ta);
        reject(err);
      }
    });
  }

  function flashCopied(btn, value) {
    var existing = timers.get(btn);
    if (existing) clearTimeout(existing);
    var labelEl = btn.querySelector("[data-copy-label]") || btn;
    if (!btn.dataset.originalLabel) {
      btn.dataset.originalLabel = labelEl.textContent;
    }
    btn.dataset.copied = "true";
    labelEl.textContent = "Copied";
    if (announcer) {
      announcer.textContent = "Copied " + value + " to clipboard";
    }
    var t = setTimeout(function () {
      delete btn.dataset.copied;
      labelEl.textContent = btn.dataset.originalLabel;
    }, 1500);
    timers.set(btn, t);
  }

  document.addEventListener("click", function (event) {
    var copyBtn = event.target.closest("[data-copy]");
    if (copyBtn) {
      var val = copyBtn.getAttribute("data-copy");
      if (!val) return;
      copyText(val).then(function () {
        flashCopied(copyBtn, val);
      }).catch(function () {
        /* ignore clipboard rejection */
      });
      return;
    }

    var codeBtn = event.target.closest("[data-copy-code]");
    if (codeBtn) {
      var block = codeBtn.closest(".code-block");
      var pre = block && block.querySelector("pre code");
      if (!pre) return;
      var text = pre.textContent.replace(/\n$/, "");
      copyText(text).then(function () {
        flashCopied(codeBtn, "code snippet");
      }).catch(function () {
        /* ignore clipboard rejection */
      });
    }
  });

  /* Lightbox dialog for palette plates */
  var dialog = document.getElementById("plate-lightbox");
  if (dialog) {
    var dialogImg = dialog.querySelector("[data-lightbox-img]");
    var dialogCap = dialog.querySelector("[data-lightbox-caption]");
    var closeBtn = dialog.querySelector("[data-lightbox-close]");

    document.addEventListener("click", function (event) {
      var trigger = event.target.closest("[data-zoom-src]");
      if (!trigger) return;
      var src = trigger.getAttribute("data-zoom-src");
      var alt = trigger.getAttribute("data-zoom-alt") || "";
      if (!src || !dialogImg) return;
      dialogImg.src = src;
      dialogImg.alt = alt;
      if (dialogCap) {
        dialogCap.textContent = alt;
      }
      if (typeof dialog.showModal === "function") {
        dialog.showModal();
      }
    });

    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        dialog.close();
      });
    }

    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) {
        dialog.close();
      }
    });
  }

  /* Desktop anchor scroll indicator: strictly one active section at a time */
  var navLinks = Array.prototype.slice.call(
    document.querySelectorAll('.site-nav a[href^="#"]')
  );
  if (navLinks.length > 0) {
    var tracked = navLinks.map(function (link) {
      return {
        link: link,
        el: document.getElementById(link.getAttribute("href").slice(1))
      };
    }).filter(function (item) { return Boolean(item.el); });

    var ticking = false;
    function updateActiveNav() {
      ticking = false;
      var offset = 110;
      var current = null;
      for (var i = 0; i < tracked.length; i++) {
        var top = tracked[i].el.getBoundingClientRect().top;
        if (top <= offset) {
          current = tracked[i].link;
        }
      }
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 24 && tracked.length) {
        current = tracked[tracked.length - 1].link;
      }
      tracked.forEach(function (item) {
        item.link.classList.toggle("is-active", item.link === current);
      });
    }

    window.addEventListener("scroll", function () {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(updateActiveNav);
      }
    }, { passive: true });
    updateActiveNav();
  }
})();
