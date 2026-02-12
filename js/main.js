// ===== Salus — Main JS =====

// Mobile nav toggle
const navToggle = document.querySelector('.nav-toggle');
if (navToggle) {
  navToggle.addEventListener('click', () => {
    const nav = navToggle.closest('.nav');
    if (nav) nav.classList.toggle('nav-open');
  });
}

// Scroll fade-in animation
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

// Active nav link highlight
const currentPage = window.location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.nav-links a').forEach(link => {
  if (link.getAttribute('href') === currentPage) {
    link.classList.add('active');
  }
});

// Contact form handling
const contactForm = document.getElementById('contact-form');
if (contactForm) {
  contactForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = contactForm.querySelector('.btn');
    btn.textContent = 'Message Sent!';
    btn.style.background = '#7a9e7e';
    setTimeout(() => {
      btn.textContent = 'Send Message';
      btn.style.background = '';
      contactForm.reset();
    }, 3000);
  });
}

// ===== Premium Access Check =====
// Note: Primary premium check is now handled by auth.js (SalusAuth.isPremium())
// This provides a fallback for pages where auth.js may not be loaded
(function() {
  // Check if SalusAuth is available - if so, let it handle everything
  if (typeof SalusAuth !== 'undefined') {
    // SalusAuth will handle premium UI updates via updateNavUI()
    return;
  }

  // Fallback: Use localStorage check for backwards compatibility
  var isPremium = localStorage.getItem('salus_premium') === 'true';

  // Handle premium unlock on session pages
  var unlockCta = document.querySelector('.unlock-cta');
  if (unlockCta && isPremium) {
    // Replace lock CTA with premium player
    unlockCta.innerHTML = '<div style="text-align:center;padding:24px;">' +
      '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" style="margin-bottom:12px;"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>' +
      '<h3 style="margin-bottom:8px;color:var(--forest);">Premium Unlocked</h3>' +
      '<p style="color:var(--mid-gray);margin-bottom:16px;">Audio player coming soon. Thank you for subscribing!</p>' +
      '</div>';
    unlockCta.style.background = 'linear-gradient(135deg, #f0f7f4 0%, #e8f4ec 100%)';
    unlockCta.style.border = '2px solid var(--accent)';
  }

  // Update nav subscribe button for premium users
  if (isPremium) {
    var subBtn = document.querySelector('.nav a[href="apps.html"], .nav a[href="../apps.html"]');
    if (subBtn && subBtn.textContent.trim() === 'Subscribe') {
      subBtn.textContent = 'Premium';
      subBtn.style.background = 'linear-gradient(135deg, var(--accent), var(--accent-dark))';
    }
  }
})();

// ===== Custom Audio Player (full-buffer for GitHub Pages seek support) =====
document.querySelectorAll('.custom-player').forEach(player => {
  const src = player.dataset.src;
  const playBtn = player.querySelector('.cp-play');
  const seekBar = player.querySelector('.cp-seek');
  const timeEl = player.querySelector('.cp-time');
  const audio = new Audio();
  let loaded = false;

  function fmt(s) {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return m + ':' + (sec < 10 ? '0' : '') + sec;
  }

  function updateTime() {
    if (seekBar) seekBar.value = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0;
    if (timeEl) timeEl.textContent = fmt(audio.currentTime) + ' / ' + fmt(audio.duration || 0);
  }

  playBtn.addEventListener('click', () => {
    if (!loaded) {
      audio.src = src + '?v=' + Date.now();
      audio.preload = 'auto';
      audio.load();
      loaded = true;
      playBtn.innerHTML = '...';
      audio.addEventListener('canplay', function onReady() {
        audio.removeEventListener('canplay', onReady);
        audio.play();
        playBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>';
      });
      audio.addEventListener('error', () => {
        playBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>';
        loaded = false;
      });
      return;
    }
    if (audio.paused) {
      audio.play();
      playBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>';
    } else {
      audio.pause();
      playBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>';
    }
  });

  if (seekBar) {
    seekBar.addEventListener('input', () => {
      if (audio.duration) {
        audio.currentTime = (seekBar.value / 100) * audio.duration;
      }
    });
  }

  audio.addEventListener('timeupdate', updateTime);
  audio.addEventListener('loadedmetadata', updateTime);
  audio.addEventListener('ended', () => {
    playBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>';
    if (seekBar) seekBar.value = 0;
  });
});
