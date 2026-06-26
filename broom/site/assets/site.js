// Shared atmosphere + nav behaviour for the NIMBUS site.
(function () {
  function embers(n) {
    var box = document.querySelector('.embers');
    if (!box) return;
    for (var i = 0; i < n; i++) {
      var e = document.createElement('div');
      e.className = 'ember';
      e.style.left = (Math.random() * 100) + 'vw';
      var dur = 9 + Math.random() * 14;
      e.style.animationDuration = dur + 's';
      e.style.animationDelay = (-Math.random() * dur) + 's';
      var s = 1.5 + Math.random() * 2.5;
      e.style.width = e.style.height = s + 'px';
      e.style.opacity = 0.3 + Math.random() * 0.5;
      box.appendChild(e);
    }
  }
  function activeNav() {
    var page = document.body.getAttribute('data-page');
    document.querySelectorAll('nav.top a.link').forEach(function (a) {
      if (a.getAttribute('href') === page + '.html') a.classList.add('active');
    });
  }
  document.addEventListener('DOMContentLoaded', function () {
    embers(26);
    activeNav();
  });
})();
