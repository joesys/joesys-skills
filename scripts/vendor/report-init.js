/* report-init.js — joesys-skills HTML report runtime.
   Eager: applies stored theme preference before paint to avoid flash.
   Deferred: wires the toggle button, initializes Mermaid, and updates
   the sidebar TOC's active item on scroll. */

(function () {
  'use strict';

  var STORAGE_KEY = 'joesys-skills-report-theme';
  var root = document.documentElement;

  // Apply stored theme preference before first paint.
  try {
    var stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') {
      root.setAttribute('data-theme', stored);
    }
  } catch (e) { /* localStorage unavailable — fall back to system pref */ }

  function effectiveTheme() {
    var explicit = root.getAttribute('data-theme');
    if (explicit) return explicit;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function setTheme(next) {
    root.setAttribute('data-theme', next);
    try { localStorage.setItem(STORAGE_KEY, next); } catch (e) { /* ignore */ }
    window.dispatchEvent(new CustomEvent('themechange', { detail: next }));
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.textContent = next === 'dark' ? '☀' : '☾';
      btn.setAttribute('aria-label', 'Switch to ' + (next === 'dark' ? 'light' : 'dark') + ' theme');
    }
  }

  function initMermaid() {
    if (typeof window.mermaid === 'undefined') return;
    var theme = effectiveTheme();
    window.mermaid.initialize({
      startOnLoad: false,
      theme: theme === 'dark' ? 'dark' : 'default',
      themeVariables: {
        primaryColor: getComputedStyle(root).getPropertyValue('--bg-elevated').trim(),
        primaryTextColor: getComputedStyle(root).getPropertyValue('--text').trim(),
        lineColor: getComputedStyle(root).getPropertyValue('--text-muted').trim(),
        primaryBorderColor: getComputedStyle(root).getPropertyValue('--border').trim()
      },
      securityLevel: 'strict'
    });
    window.mermaid.run({ querySelector: 'pre.mermaid' });
  }

  function reInitMermaid() {
    // After theme change, re-render any mermaid blocks with new colors.
    if (typeof window.mermaid === 'undefined') return;
    document.querySelectorAll('pre.mermaid').forEach(function (el) {
      // Mermaid replaces content with rendered SVG; restore source from data attribute.
      var src = el.getAttribute('data-mermaid-source');
      if (src) el.textContent = src;
      el.removeAttribute('data-processed');
    });
    initMermaid();
  }

  function captureMermaidSources() {
    document.querySelectorAll('pre.mermaid').forEach(function (el) {
      el.setAttribute('data-mermaid-source', el.textContent);
    });
  }

  function initTOCActiveTracking() {
    var sidebarLinks = document.querySelectorAll('.sidebar a[href^="#"]');
    if (sidebarLinks.length === 0) return;
    var headings = Array.prototype.map.call(sidebarLinks, function (a) {
      var id = a.getAttribute('href').slice(1);
      return { link: a, target: document.getElementById(id) };
    }).filter(function (entry) { return entry.target; });
    if (headings.length === 0) return;

    function update() {
      var scrollY = window.scrollY + 100;
      var current = headings[0];
      for (var i = 0; i < headings.length; i++) {
        if (headings[i].target.offsetTop <= scrollY) current = headings[i];
      }
      headings.forEach(function (h) { h.link.classList.remove('active'); });
      current.link.classList.add('active');
    }

    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.textContent = effectiveTheme() === 'dark' ? '☀' : '☾';
      btn.setAttribute('aria-label', 'Switch to ' + (effectiveTheme() === 'dark' ? 'light' : 'dark') + ' theme');
      btn.addEventListener('click', function () {
        var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
        setTheme(next);
      });
    }

    captureMermaidSources();
    initMermaid();
    initTOCActiveTracking();

    window.addEventListener('themechange', reInitMermaid);
  });
})();
