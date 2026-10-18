/* Reading progress bar, TOC highlighting, code copy buttons. No dependencies. */
(function () {
  "use strict";

  /* progress bar */
  var bar = document.getElementById("progress");
  function update() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
  }
  document.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  update();

  /* active TOC entry */
  var heads = [].slice.call(document.querySelectorAll("main h2[id], main h3[id]"));
  var links = {};
  [].forEach.call(document.querySelectorAll("aside.toc a"), function (a) {
    links[a.getAttribute("href").slice(1)] = a;
  });
  if (heads.length && Object.keys(links).length) {
    var seen = new WeakMap();
    var obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          seen.set(e.target, e.isIntersecting);
        });
        for (var i = 0; i < heads.length; i++) {
          var id = heads[i].id;
          if (seen.get(heads[i]) && links[id]) {
            [].forEach.call(document.querySelectorAll("aside.toc a.active"), function (a) {
              a.classList.remove("active");
            });
            links[id].classList.add("active");
            break;
          }
        }
      },
      { rootMargin: "-80px 0px -70% 0px" }
    );
    heads.forEach(function (h) {
      obs.observe(h);
    });
  }

  /* copy buttons */
  [].forEach.call(document.querySelectorAll("pre"), function (pre) {
    var btn = document.createElement("button");
    btn.className = "copy";
    btn.type = "button";
    btn.textContent = "copy";
    btn.addEventListener("click", function () {
      var text = pre.querySelector("code").innerText;
      function done() {
        btn.classList.add("done");
        btn.textContent = "copied";
        setTimeout(function () {
          btn.classList.remove("done");
          btn.textContent = "copy";
        }, 1400);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      } else {
        var ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); done(); } catch (e) {}
        document.body.removeChild(ta);
      }
    });
    pre.appendChild(btn);
  });
})();
