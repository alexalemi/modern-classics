// Reading aids for the book pages. Both are conveniences: without
// JavaScript, or with storage blocked, the page reads exactly the same.
//
// 1. A "Contents" button that appears once the reader has scrolled past the
//    table of contents, so a 3 MB book is never more than a tap from it.
// 2. The last section read is remembered in this browser (localStorage,
//    this device only, nothing sent anywhere). Coming back to the page
//    offers a "Continue reading" link; it never jumps on its own.
(function () {
  var toc = document.getElementById("contents");
  var button = document.querySelector(".to-contents");
  var sections = Array.prototype.slice.call(
    document.querySelectorAll("article section[aria-labelledby]:not(.part)"));
  var key = "emend:last:" + location.pathname;

  function store(id) {
    try { localStorage.setItem(key, id); } catch (e) { /* private mode etc. */ }
  }
  function recall() {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  // ---- continue reading ----
  var resume = document.querySelector(".resume");
  var last = recall();
  if (resume && last && !location.hash && sections.length > 1 &&
      sections[0].getAttribute("aria-labelledby") !== last) {
    var h = document.getElementById(last);
    if (h) {
      var a = resume.querySelector("a");
      a.href = "#" + last;
      a.textContent = h.textContent;
      resume.hidden = false;
    }
  }

  // ---- track position, show the button ----
  var ticking = false;
  function onScroll() {
    ticking = false;
    if (button && toc) {
      var past = toc.parentNode.getBoundingClientRect().bottom < 0;
      button.classList.toggle("show", past);
    }
    // the last section whose heading has scrolled above a third of the screen
    var line = window.innerHeight / 3, current = null;
    for (var i = 0; i < sections.length; i++) {
      if (sections[i].getBoundingClientRect().top > line) break;
      current = sections[i];
    }
    if (current) store(current.getAttribute("aria-labelledby"));
  }
  window.addEventListener("scroll", function () {
    if (!ticking) { ticking = true; window.requestAnimationFrame(onScroll); }
  }, { passive: true });
})();
