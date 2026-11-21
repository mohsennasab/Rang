(function () {
  "use strict";

  var THEME_KEY = "rang-theme";
  var PAINT_KEY = "rang-paint";
  var root = document.documentElement;

  /* ---------------- Theme Toggle ---------------- */
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

  var initialTheme = "light";
  try {
    if (localStorage.getItem(THEME_KEY) === "dark") {
      initialTheme = "dark";
    }
  } catch (e) {
    /* ignore storage errors */
  }
  applyTheme(initialTheme);

  var themeToggle = document.querySelector("[data-theme-toggle]");
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var next = root.dataset.theme === "dark" ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem(THEME_KEY, next);
      } catch (e) {
        /* ignore storage errors */
      }
    });
  }

  /* ---------------- Mobile Menu Toggle ---------------- */
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

  /* ---------------- Clipboard Copy Helpers ---------------- */
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

  /* ---------------- Lightbox Dialog ---------------- */
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

  /* ---------------- Paint Drop & Bottom Splash Canvas ---------------- */
  var canvas = document.getElementById("paint-canvas");
  var paintToggle = document.querySelector("[data-paint-toggle]");
  var ctx = canvas && canvas.getContext ? canvas.getContext("2d") : null;
  var prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var paintEnabled = !prefersReduced;
  try {
    var savedPaint = localStorage.getItem(PAINT_KEY);
    if (savedPaint === "off") paintEnabled = false;
    else if (savedPaint === "on") paintEnabled = true;
  } catch (e) {
    /* ignore storage errors */
  }

  var viewW = window.innerWidth;
  var viewH = window.innerHeight;
  var dpr = 1;
  var drops = [];
  var droplets = [];
  var pools = [];
  var rafId = null;
  var ambientTimer = null;
  var colorCursor = 0;

  var baseColors = (document.body.getAttribute("data-palette-colors") || "")
    .split(",")
    .map(function (c) { return c.trim(); })
    .filter(Boolean);
  if (!baseColors.length) {
    baseColors = ["#7f3020", "#c07049", "#c59b46", "#6d866a", "#5d95a8", "#3263ac", "#1a3b45"];
  }
  var plates = Array.prototype.slice.call(document.querySelectorAll(".palette-plate[data-colors]"));

  function resizeCanvas() {
    if (!canvas || !ctx) return;
    viewW = window.innerWidth;
    viewH = window.innerHeight;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(viewW * dpr);
    canvas.height = Math.round(viewH * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function updatePaintButton() {
    if (!paintToggle) return;
    paintToggle.setAttribute("aria-pressed", String(paintEnabled));
    var label = paintToggle.querySelector(".paint-label");
    if (label) {
      label.textContent = paintEnabled ? "Paint" : "Paused";
    }
  }

  function activeViewportColors() {
    if (!plates.length) return baseColors;
    var midY = viewH * 0.48;
    var best = null;
    var bestDist = Infinity;
    for (var i = 0; i < plates.length; i++) {
      var rect = plates[i].getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > viewH) continue;
      var center = (rect.top + rect.bottom) * 0.5;
      var dist = Math.abs(center - midY);
      if (dist < bestDist) {
        bestDist = dist;
        best = plates[i];
      }
    }
    if (!best) return baseColors;
    var cols = (best.getAttribute("data-colors") || "").split(",").filter(Boolean);
    return cols.length ? cols : baseColors;
  }

  function nextColor() {
    var cols = activeViewportColors();
    var c = cols[colorCursor % cols.length];
    colorCursor += 1;
    return c;
  }

  function pickMarginX() {
    var leftSide = Math.random() < 0.5;
    if (viewW > 1120) {
      var pad = Math.min((viewW - 1080) * 0.5, 160);
      var edge = Math.max(pad - 14, 34);
      return leftSide
        ? 16 + Math.random() * edge
        : viewW - 16 - Math.random() * edge;
    }
    return leftSide
      ? 14 + Math.random() * Math.min(54, viewW * 0.14)
      : viewW - 14 - Math.random() * Math.min(54, viewW * 0.14);
  }

  function spawnDrop(x, y, color, radius) {
    if (!ctx || !paintEnabled) return;
    drops.push({
      x: Math.max(10, Math.min(viewW - 10, x)),
      y: y,
      vx: (Math.random() - 0.5) * 0.55,
      vy: 1.8 + Math.random() * 1.8,
      r: radius || (4.4 + Math.random() * 2.4),
      color: color
    });
    ensureRunning();
  }

  function createSplash(x, color, r) {
    var count = 9 + Math.floor(Math.random() * 5);
    for (var i = 0; i < count; i++) {
      var spread = (Math.random() - 0.5) * 7.6;
      var lift = -(2.4 + Math.random() * 5.8);
      droplets.push({
        x: x + (Math.random() - 0.5) * 6,
        y: viewH - 2,
        vx: spread,
        vy: lift,
        r: 1.5 + Math.random() * 3.4,
        color: color,
        alpha: 0.96,
        decay: 0.018 + Math.random() * 0.012
      });
    }

    var lobeCount = 5 + Math.floor(Math.random() * 3);
    var lobes = [];
    var baseWidth = 24 + r * 3.6;
    for (var j = 0; j < lobeCount; j++) {
      var t = lobeCount > 1 ? (j / (lobeCount - 1)) * 2 - 1 : 0;
      lobes.push({
        dx: t * baseWidth * 0.62 + (Math.random() - 0.5) * 6,
        rx: 7 + Math.random() * 11,
        ry: (1 - Math.abs(t) * 0.45) * (9 + Math.random() * 13)
      });
    }
    pools.push({
      x: x,
      color: color,
      lobes: lobes,
      age: 0,
      life: 9.5,
      growDur: 0.28
    });
    if (pools.length > 20) {
      pools.shift();
    }
  }

  function easeOutBack(t) {
    var c1 = 1.70158;
    var c3 = c1 + 1;
    var u = t - 1;
    return 1 + c3 * u * u * u + c1 * u * u;
  }

  function drawTeardrop(drop) {
    var stretch = Math.min(2.35, 1.18 + drop.vy * 0.07);
    var r = drop.r;
    var tipY = -r * stretch * 1.65;
    ctx.save();
    ctx.translate(drop.x, drop.y);
    ctx.fillStyle = drop.color;
    ctx.beginPath();
    ctx.moveTo(0, tipY);
    ctx.bezierCurveTo(r * 0.55, -r * 0.5, r, -r * 0.05, r, r * 0.35);
    ctx.arc(0, r * 0.35, r, 0, Math.PI, false);
    ctx.bezierCurveTo(-r, -r * 0.05, -r * 0.55, -r * 0.5, 0, tipY);
    ctx.closePath();
    ctx.fill();

    /* Specular glaze glint */
    ctx.fillStyle = "rgba(255, 255, 255, 0.42)";
    ctx.beginPath();
    ctx.ellipse(-r * 0.28, r * 0.2, r * 0.22, r * 0.42, -0.22, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawPool(pool) {
    var progress = Math.min(1, pool.age / pool.growDur);
    var scale = progress < 1 ? Math.max(0.1, easeOutBack(progress)) : 1;
    var fadeStart = pool.life - 2.6;
    var alpha = pool.age > fadeStart
      ? Math.max(0, 1 - (pool.age - fadeStart) / 2.6)
      : 1;

    ctx.save();
    ctx.globalAlpha = alpha * 0.9;
    ctx.fillStyle = pool.color;
    for (var i = 0; i < pool.lobes.length; i++) {
      var lobe = pool.lobes[i];
      ctx.beginPath();
      ctx.ellipse(
        pool.x + lobe.dx * scale,
        viewH,
        lobe.rx * scale,
        lobe.ry * scale,
        0,
        Math.PI,
        Math.PI * 2
      );
      ctx.closePath();
      ctx.fill();
    }
    ctx.restore();
  }

  var lastTime = 0;
  function tick(now) {
    if (!ctx) return;
    var dt = lastTime ? Math.min(0.05, (now - lastTime) / 1000) : 0.016;
    lastTime = now;
    var step = dt * 60;

    ctx.clearRect(0, 0, viewW, viewH);

    for (var p = pools.length - 1; p >= 0; p--) {
      var pool = pools[p];
      pool.age += dt;
      if (pool.age >= pool.life) {
        pools.splice(p, 1);
      } else {
        drawPool(pool);
      }
    }

    for (var i = drops.length - 1; i >= 0; i--) {
      var d = drops[i];
      d.vy += 0.34 * step;
      d.x += d.vx * step;
      d.y += d.vy * step;
      if (d.y >= viewH - 2) {
        createSplash(d.x, d.color, d.r);
        drops.splice(i, 1);
      } else {
        drawTeardrop(d);
      }
    }

    for (var k = droplets.length - 1; k >= 0; k--) {
      var s = droplets[k];
      s.vy += 0.28 * step;
      s.x += s.vx * step;
      s.y += s.vy * step;
      s.alpha -= s.decay * step;
      if (s.alpha <= 0.02 || s.y > viewH + 8) {
        droplets.splice(k, 1);
      } else {
        ctx.save();
        ctx.globalAlpha = s.alpha;
        ctx.fillStyle = s.color;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    if (drops.length > 0 || droplets.length > 0 || pools.length > 0) {
      rafId = window.requestAnimationFrame(tick);
    } else {
      rafId = null;
      lastTime = 0;
    }
  }

  function ensureRunning() {
    if (rafId === null && ctx) {
      lastTime = 0;
      rafId = window.requestAnimationFrame(tick);
    }
  }

  function splashPalette(colors, originEl) {
    if (!ctx) return;
    if (!paintEnabled) {
      paintEnabled = true;
      updatePaintButton();
    }
    var rect = originEl ? originEl.getBoundingClientRect() : null;
    var cols = colors.slice(0, 12);
    for (var i = 0; i < cols.length; i++) {
      (function (idx, col) {
        setTimeout(function () {
          var startX;
          var startY;
          if (rect) {
            var span = Math.max(40, Math.min(rect.width, 460));
            var frac = cols.length > 1 ? idx / (cols.length - 1) : 0.5;
            startX = rect.left + frac * span + (Math.random() - 0.5) * 14;
            startY = Math.max(10, rect.top + rect.height * 0.5);
          } else {
            startX = pickMarginX();
            startY = 8;
          }
          spawnDrop(startX, startY, col, 4.8 + Math.random() * 1.8);
        }, idx * 55);
      })(i, cols[i]);
    }
  }

  function scheduleAmbient() {
    if (ambientTimer) clearTimeout(ambientTimer);
    if (!paintEnabled || !ctx) return;
    var delay = 2200 + Math.random() * 1800;
    ambientTimer = setTimeout(function () {
      if (paintEnabled && !document.hidden) {
        spawnDrop(pickMarginX(), 6, nextColor());
      }
      scheduleAmbient();
    }, delay);
  }

  function runOpeningCascade() {
    if (!paintEnabled || !ctx) return;
    for (var i = 0; i < 6; i++) {
      (function (idx) {
        setTimeout(function () {
          if (paintEnabled && !document.hidden) {
            spawnDrop(pickMarginX(), 6, nextColor(), 4.8 + Math.random() * 2);
          }
        }, 180 + idx * 170);
      })(i);
    }
  }

  if (canvas && ctx) {
    resizeCanvas();
    updatePaintButton();
    window.addEventListener("resize", resizeCanvas, { passive: true });
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden && paintEnabled) {
        scheduleAmbient();
      }
    });
    if (paintEnabled) {
      runOpeningCascade();
      scheduleAmbient();
    }
  }

  if (paintToggle) {
    paintToggle.addEventListener("click", function () {
      paintEnabled = !paintEnabled;
      updatePaintButton();
      try {
        localStorage.setItem(PAINT_KEY, paintEnabled ? "on" : "off");
      } catch (e) {
        /* ignore storage errors */
      }
      if (paintEnabled) {
        spawnDrop(pickMarginX(), 6, nextColor(), 5.5);
        scheduleAmbient();
      } else {
        if (ambientTimer) clearTimeout(ambientTimer);
        drops = [];
        droplets = [];
        pools = [];
        if (rafId !== null) {
          window.cancelAnimationFrame(rafId);
          rafId = null;
        }
        if (ctx) ctx.clearRect(0, 0, viewW, viewH);
      }
    });
  }

  /* Unified click handler for copy buttons, hex drops, ribbon drops, and splash buttons */
  document.addEventListener("click", function (event) {
    var ribbonBtn = event.target.closest("[data-splash-color]");
    if (ribbonBtn) {
      var rCol = ribbonBtn.getAttribute("data-splash-color");
      if (rCol) {
        if (!paintEnabled) {
          paintEnabled = true;
          updatePaintButton();
          scheduleAmbient();
        }
        var rRect = ribbonBtn.getBoundingClientRect();
        spawnDrop(rRect.left + rRect.width * 0.5, 6, rCol, 6.2);
      }
      return;
    }

    var splashBtn = event.target.closest("[data-splash-palette]");
    if (splashBtn) {
      var list = (splashBtn.getAttribute("data-splash-palette") || "")
        .split(",")
        .filter(Boolean);
      if (list.length) {
        splashPalette(list, splashBtn.closest(".hex-bar") || splashBtn);
      }
      return;
    }

    var copyBtn = event.target.closest("[data-copy]");
    if (copyBtn) {
      var val = copyBtn.getAttribute("data-copy");
      if (!val) return;
      copyText(val).then(function () {
        flashCopied(copyBtn, val);
      }).catch(function () {
        /* ignore clipboard rejection */
      });
      if (paintEnabled) {
        if (copyBtn.classList.contains("hex-chip")) {
          var cRect = copyBtn.getBoundingClientRect();
          spawnDrop(cRect.left + cRect.width * 0.5, cRect.top + cRect.height * 0.5, val, 5.4);
        } else if (copyBtn.classList.contains("copy-all-btn")) {
          splashPalette(val.split(/\s+/).filter(Boolean), copyBtn.closest(".hex-bar") || copyBtn);
        }
      }
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

  /* ---------------- Desktop Scrollspy (Strictly One Active Link) ---------------- */
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
      var offset = 115;
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
