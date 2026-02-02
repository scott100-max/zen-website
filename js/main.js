// ===== Salus — Main JS =====

// Mobile nav toggle
const navToggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('.nav-links');
if (navToggle) {
  navToggle.addEventListener('click', () => {
    navLinks.classList.toggle('open');
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

// ===== Persistent Audio Player =====
(function() {
  var STORAGE_KEY = 'salus_player';

  // Inject player bar HTML
  var playerBar = document.createElement('div');
  playerBar.id = 'salus-persistent-player';
  playerBar.innerHTML =
    '<div class="sp-inner">' +
      '<span class="sp-track-name"></span>' +
      '<button class="sp-play-btn" aria-label="Play/Pause">&#9654;</button>' +
      '<div class="sp-progress-wrap"><div class="sp-progress-bar"></div></div>' +
      '<span class="sp-time">0:00</span>' +
      '<button class="sp-close-btn" aria-label="Close">&times;</button>' +
    '</div>';
  document.body.appendChild(playerBar);

  // Inject styles
  var style = document.createElement('style');
  style.textContent =
    '#salus-persistent-player{' +
      'position:fixed;bottom:0;left:0;right:0;z-index:9999;' +
      'background:var(--forest,#0f1a12);color:#fff;' +
      'padding:0;transform:translateY(100%);transition:transform .3s ease;' +
      'box-shadow:0 -2px 20px rgba(0,0,0,.3);' +
    '}' +
    '#salus-persistent-player.sp-visible{transform:translateY(0);}' +
    '.sp-inner{' +
      'max-width:1140px;margin:0 auto;padding:10px 24px;' +
      'display:flex;align-items:center;gap:14px;' +
    '}' +
    '.sp-track-name{' +
      'font-size:.85rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:0 1 auto;max-width:220px;' +
    '}' +
    '.sp-play-btn,.sp-close-btn{' +
      'background:none;border:none;color:#fff;cursor:pointer;font-size:1.1rem;padding:4px 8px;flex-shrink:0;' +
    '}' +
    '.sp-play-btn:hover,.sp-close-btn:hover{color:var(--accent-light,#b5cdb8);}' +
    '.sp-progress-wrap{' +
      'flex:1;height:6px;background:rgba(255,255,255,.15);border-radius:3px;cursor:pointer;position:relative;min-width:60px;' +
    '}' +
    '.sp-progress-bar{' +
      'height:100%;background:var(--accent,#7a9e7e);border-radius:3px;width:0%;transition:width .2s linear;' +
    '}' +
    '.sp-time{font-size:.75rem;opacity:.7;flex-shrink:0;min-width:36px;text-align:right;}' +
    '.sp-close-btn{font-size:1.4rem;line-height:1;}' +
    '@media(max-width:768px){' +
      '.sp-track-name{max-width:100px;}' +
      '.sp-inner{padding:8px 16px;gap:10px;}' +
    '}' +
    /* push footer up when player is visible */
    'body.sp-active{padding-bottom:52px;}';
  document.head.appendChild(style);

  var trackNameEl = playerBar.querySelector('.sp-track-name');
  var playBtn = playerBar.querySelector('.sp-play-btn');
  var progressWrap = playerBar.querySelector('.sp-progress-wrap');
  var progressBar = playerBar.querySelector('.sp-progress-bar');
  var timeEl = playerBar.querySelector('.sp-time');
  var closeBtn = playerBar.querySelector('.sp-close-btn');

  // The hidden audio element used for persistent playback
  var persistentAudio = new Audio();
  persistentAudio.preload = 'auto';

  var currentTrackName = '';
  var currentTrackSrc = '';
  var saveInterval = null;

  function formatTime(s) {
    s = Math.floor(s || 0);
    var m = Math.floor(s / 60);
    var sec = s % 60;
    return m + ':' + (sec < 10 ? '0' : '') + sec;
  }

  function showPlayer() {
    playerBar.classList.add('sp-visible');
    document.body.classList.add('sp-active');
  }

  function hidePlayer() {
    playerBar.classList.remove('sp-visible');
    document.body.classList.remove('sp-active');
  }

  function saveState() {
    if (!currentTrackSrc) return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      src: currentTrackSrc,
      name: currentTrackName,
      time: persistentAudio.currentTime || 0,
      playing: !persistentAudio.paused
    }));
  }

  function clearState() {
    localStorage.removeItem(STORAGE_KEY);
  }

  function updateProgress() {
    if (persistentAudio.duration && isFinite(persistentAudio.duration)) {
      var pct = (persistentAudio.currentTime / persistentAudio.duration) * 100;
      progressBar.style.width = pct + '%';
      timeEl.textContent = formatTime(persistentAudio.currentTime);
    }
  }

  function updatePlayBtn() {
    playBtn.innerHTML = persistentAudio.paused ? '&#9654;' : '&#9646;&#9646;';
  }

  // Start playing a track in the persistent player
  function playTrack(src, name, startTime) {
    currentTrackSrc = src;
    currentTrackName = name;
    trackNameEl.textContent = name;

    if (persistentAudio.getAttribute('data-src') !== src) {
      persistentAudio.src = src;
      persistentAudio.setAttribute('data-src', src);
    }

    if (startTime && startTime > 0) {
      persistentAudio.currentTime = startTime;
    }

    persistentAudio.play().catch(function() {
      // Autoplay may be blocked; show player paused
      updatePlayBtn();
    });

    showPlayer();
    saveState();

    // Start periodic save
    clearInterval(saveInterval);
    saveInterval = setInterval(saveState, 2000);
  }

  function stopPlayer() {
    persistentAudio.pause();
    persistentAudio.src = '';
    persistentAudio.removeAttribute('data-src');
    currentTrackSrc = '';
    currentTrackName = '';
    clearState();
    clearInterval(saveInterval);
    hidePlayer();
    updatePlayBtn();
  }

  // Audio events
  persistentAudio.addEventListener('timeupdate', updateProgress);
  persistentAudio.addEventListener('play', updatePlayBtn);
  persistentAudio.addEventListener('pause', function() {
    updatePlayBtn();
    saveState();
  });
  persistentAudio.addEventListener('ended', function() {
    updatePlayBtn();
    clearState();
    hidePlayer();
  });

  // Controls
  playBtn.addEventListener('click', function() {
    if (!currentTrackSrc) return;
    if (persistentAudio.paused) {
      persistentAudio.play();
    } else {
      persistentAudio.pause();
    }
  });

  progressWrap.addEventListener('click', function(e) {
    var rect = progressWrap.getBoundingClientRect();
    var pct = (e.clientX - rect.left) / rect.width;

    // Try seeking on-page video with matching source first
    var seeked = false;
    document.querySelectorAll('video').forEach(function(v) {
      if (getMediaSrc(v) === currentTrackSrc && v.duration && isFinite(v.duration)) {
        v.currentTime = pct * v.duration;
        seeked = true;
      }
    });

    // Always seek persistent audio if it has a valid duration
    if (persistentAudio.duration && isFinite(persistentAudio.duration)) {
      persistentAudio.currentTime = pct * persistentAudio.duration;
    }

    saveState();
  });

  closeBtn.addEventListener('click', function() {
    stopPlayer();
    // Also pause any on-page media that matches
    document.querySelectorAll('audio, video').forEach(function(el) {
      el.pause();
    });
  });

  // Helper: get a friendly track name from a media element
  function getTrackName(mediaEl) {
    // For soundscape cards
    var card = mediaEl.closest('.sound-card');
    if (card) {
      var h3 = card.querySelector('h3');
      if (h3) return h3.textContent;
    }
    // For session cards
    card = mediaEl.closest('.session-card');
    if (card) {
      var h3 = card.querySelector('h3');
      if (h3) return h3.textContent;
    }
    // Fallback: filename
    var src = mediaEl.querySelector('source') ? mediaEl.querySelector('source').src : mediaEl.src;
    if (src) {
      var parts = src.split('/');
      return decodeURIComponent(parts[parts.length - 1]).replace(/\.[^.]+$/, '').replace(/[-_]/g, ' ');
    }
    return 'Unknown Track';
  }

  // Helper: get the actual src URL for a media element
  function getMediaSrc(mediaEl) {
    var sourceEl = mediaEl.querySelector('source');
    if (sourceEl && sourceEl.src) return sourceEl.src;
    return mediaEl.src || '';
  }

  // Hook into all audio and video elements on the page
  function hookMediaElements() {
    document.querySelectorAll('audio, video').forEach(function(mediaEl) {
      if (mediaEl._salusHooked) return;
      mediaEl._salusHooked = true;

      mediaEl.addEventListener('play', function() {
        // Skip the home page hero video — it's ambient, not a session
        if (mediaEl.id === 'heroVideo') return;

        var src = getMediaSrc(mediaEl);
        var name = getTrackName(mediaEl);

        // For video elements, we extract audio by playing through persistent player
        // but also keep video playing on its own page
        if (mediaEl.tagName === 'VIDEO') {
          // Save state so if user navigates away, audio resumes
          currentTrackSrc = src;
          currentTrackName = name;
          trackNameEl.textContent = name;

          // For video, we mirror position to persistent audio but keep it hidden
          // The persistent audio will take over only on other pages
          // Don't load into persistent audio if we're on the same page with the video
          persistentAudio.setAttribute('data-src', src);
          showPlayer();

          // Sync from video to persistent player display
          function syncFromVideo() {
            if (persistentAudio.duration && isFinite(persistentAudio.duration)) {
              updateProgress();
            } else if (mediaEl.duration && isFinite(mediaEl.duration)) {
              var pct = (mediaEl.currentTime / mediaEl.duration) * 100;
              progressBar.style.width = pct + '%';
              timeEl.textContent = formatTime(mediaEl.currentTime);
            }
          }
          mediaEl.addEventListener('timeupdate', syncFromVideo);
          mediaEl.addEventListener('pause', function() {
            saveState();
            updatePlayBtn();
          });

          // Save state periodically
          clearInterval(saveInterval);
          saveInterval = setInterval(function() {
            if (!mediaEl.paused) {
              localStorage.setItem(STORAGE_KEY, JSON.stringify({
                src: src,
                name: name,
                time: mediaEl.currentTime || 0,
                playing: true
              }));
            }
          }, 2000);

          updatePlayBtn();
          return;
        }

        // For audio elements: pause native controls, use persistent player
        // Pause all other on-page audio/video
        document.querySelectorAll('audio, video').forEach(function(other) {
          if (other !== mediaEl) other.pause();
        });

        // Pause native element and play through persistent player
        mediaEl.pause();
        playTrack(src, name, mediaEl.currentTime);
      });
    });
  }

  hookMediaElements();

  // Also hook elements that may be added later (unlikely in static site, but safe)
  if (typeof MutationObserver !== 'undefined') {
    new MutationObserver(function() { hookMediaElements(); })
      .observe(document.body, { childList: true, subtree: true });
  }

  // Sync persistent player play/pause with on-page video (if present)
  playBtn.addEventListener('click', function() {
    // If there's an on-page video with the same source, control it too
    document.querySelectorAll('video').forEach(function(v) {
      var vSrc = getMediaSrc(v);
      if (vSrc === currentTrackSrc) {
        if (persistentAudio.paused && v.paused) {
          // We just toggled - the play handler above will handle it
        }
        // Sync video with persistent audio action
        if (!v.paused && persistentAudio.paused) {
          v.pause();
        }
      }
    });
  });

  // Resume from localStorage on page load
  var saved = null;
  try { saved = JSON.parse(localStorage.getItem(STORAGE_KEY)); } catch(e) {}

  if (saved && saved.src && saved.src.indexOf('salus-video') === -1) {
    // Check if there's an on-page video with this source
    var onPageVideo = null;
    document.querySelectorAll('video').forEach(function(v) {
      if (getMediaSrc(v) === saved.src) onPageVideo = v;
    });

    if (onPageVideo) {
      // We're on the same page as the video — restore its position but do NOT auto-play
      trackNameEl.textContent = saved.name;
      currentTrackSrc = saved.src;
      currentTrackName = saved.name;
      showPlayer();
      onPageVideo.currentTime = saved.time || 0;
      updatePlayBtn();
    } else {
      // Different page or audio — restore state but do NOT auto-play
      currentTrackSrc = saved.src;
      currentTrackName = saved.name;
      trackNameEl.textContent = saved.name;

      persistentAudio.src = saved.src;
      persistentAudio.setAttribute('data-src', saved.src);
      persistentAudio.preload = 'auto';

      // Set the start time once metadata is loaded
      var startTime = saved.time || 0;
      if (startTime > 0) {
        persistentAudio.addEventListener('loadedmetadata', function onMeta() {
          persistentAudio.currentTime = startTime;
          updateProgress();
          persistentAudio.removeEventListener('loadedmetadata', onMeta);
        });
      }

      showPlayer();
      updatePlayBtn();

      // Start periodic save (will only save if playing)
      clearInterval(saveInterval);
      saveInterval = setInterval(saveState, 2000);
    }
  }

  // Save state before navigating away
  window.addEventListener('beforeunload', function() {
    // For on-page videos, save their current time
    document.querySelectorAll('video').forEach(function(v) {
      if (!v.paused && getMediaSrc(v) === currentTrackSrc) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
          src: currentTrackSrc,
          name: currentTrackName,
          time: v.currentTime || 0,
          playing: true
        }));
      }
    });
    if (currentTrackSrc && !persistentAudio.paused) {
      saveState();
    }
  });

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
    seekBar.value = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0;
    timeEl.textContent = fmt(audio.currentTime) + ' / ' + fmt(audio.duration || 0);
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
        playBtn.innerHTML = '&#9646;&#9646;';
      });
      audio.addEventListener('error', () => {
        playBtn.innerHTML = '&#9654;';
        loaded = false;
      });
      return;
    }
    if (audio.paused) {
      audio.play();
      playBtn.innerHTML = '&#9646;&#9646;';
    } else {
      audio.pause();
      playBtn.innerHTML = '&#9654;';
    }
  });

  seekBar.addEventListener('input', () => {
    if (audio.duration) {
      audio.currentTime = (seekBar.value / 100) * audio.duration;
    }
  });

  audio.addEventListener('timeupdate', updateTime);
  audio.addEventListener('loadedmetadata', updateTime);
  audio.addEventListener('ended', () => {
    playBtn.innerHTML = '&#9654;';
    seekBar.value = 0;
  });
});
