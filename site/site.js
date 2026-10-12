// The filter box on the index and restored pages: type part of a title,
// author, year or blurb and the cards that do not match are hidden, along
// with any shelf left empty. Plain DOM, no dependencies. Without JavaScript
// the box stays hidden and the page is the full list.
(function () {
  var box = document.querySelector(".finder");
  if (!box) return;
  var input = box.querySelector("input");
  var count = box.querySelector(".count");
  var cards = Array.prototype.slice.call(document.querySelectorAll(".card"));
  var text = cards.map(function (c) { return norm(c.textContent); });
  box.hidden = false;

  // fold case and accents, so "godel" finds Gödel and "dogen" finds Dōgen
  function norm(s) {
    return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  function apply() {
    var words = norm(input.value).split(/\s+/).filter(Boolean);
    var shown = 0;
    cards.forEach(function (card, i) {
      var hit = words.every(function (w) { return text[i].indexOf(w) !== -1; });
      card.hidden = !hit;
      if (hit) shown++;
    });
    // a shelf (heading + ul.deck) with nothing showing disappears entirely,
    // and so does a whole collection (section.strand) with no shelves left
    document.querySelectorAll("ul.deck").forEach(function (deck) {
      var any = deck.querySelector(".card:not([hidden])") !== null;
      deck.hidden = !any;
      var h = deck.previousElementSibling;
      if (h && /^H[2-6]$/.test(h.tagName)) h.hidden = !any;
    });
    document.querySelectorAll("section.strand").forEach(function (strand) {
      strand.hidden = strand.querySelector(".card:not([hidden])") === null;
    });
    count.textContent = words.length
      ? (shown === 0 ? "No matches" : shown + (shown === 1 ? " book" : " books"))
      : "";
  }

  input.addEventListener("input", apply);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { input.value = ""; apply(); }
  });
})();
