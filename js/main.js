// ===== Salus — Main JS =====

// Scroll fade-in animation
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

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

// ===== Persistent Narrator Player (cross-page) =====
(function(){
  // Skip if homepage already handles its own player
  if(window.__narratorHome) return;
  var saved=sessionStorage.getItem('narrator');
  if(!saved) return;
  var st=JSON.parse(saved);
  if(!st.playing||!st.time) return;
  sessionStorage.removeItem('narrator');

  // Create floating mini-player
  var wrap=document.createElement('div');
  wrap.className='narrator-float';
  wrap.innerHTML=
    '<button class="narrator-float__play" aria-label="Play narrator">' +
      '<svg class="narrator-float__icon-play" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>' +
      '<svg class="narrator-float__icon-pause" viewBox="0 0 24 24" style="display:none"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>' +
    '</button>' +
    '<div class="narrator-float__info">' +
      '<span class="narrator-float__label">Marco, your narrator</span>' +
      '<div class="narrator-float__track"><div class="narrator-float__bar"></div></div>' +
    '</div>' +
    '<span class="narrator-float__time">0:00</span>' +
    '<button class="narrator-float__close" aria-label="Close">&times;</button>';

  // Inject styles
  var css=document.createElement('style');
  css.textContent=
    '.narrator-float{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:10px;'+
    'background:rgba(10,13,24,0.92);border:1px solid rgba(255,255,255,0.08);border-radius:40px;padding:8px 14px 8px 8px;'+
    'z-index:9999;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);box-shadow:0 8px 32px rgba(0,0,0,0.4);max-width:340px;width:90%}'+
    '.narrator-float__play{width:34px;height:34px;border-radius:50%;background:rgba(78,205,196,0.12);border:1px solid rgba(78,205,196,0.25);'+
    'display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;transition:all .3s}'+
    '.narrator-float__play:hover{background:rgba(78,205,196,0.2)}'+
    '.narrator-float__play svg{width:14px;height:14px;fill:#4ecdc4}'+
    '.narrator-float__info{flex:1;min-width:0}'+
    '.narrator-float__label{display:block;font-size:.65rem;font-weight:300;color:rgba(242,240,250,0.45);margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:"Outfit",sans-serif}'+
    '.narrator-float__track{height:3px;background:rgba(255,255,255,0.06);border-radius:2px;overflow:hidden;cursor:pointer}'+
    '.narrator-float__bar{height:100%;width:0%;background:linear-gradient(90deg,#4ecdc4,#6dd5c8);border-radius:2px;transition:width .1s linear}'+
    '.narrator-float__time{font-size:.65rem;color:rgba(242,240,250,0.45);min-width:26px;text-align:right;font-variant-numeric:tabular-nums;font-family:"Outfit",sans-serif;flex-shrink:0}'+
    '.narrator-float__close{background:none;border:none;color:rgba(242,240,250,0.3);font-size:1.1rem;cursor:pointer;padding:0 0 0 4px;line-height:1;flex-shrink:0}'+
    '.narrator-float__close:hover{color:rgba(242,240,250,0.6)}';
  document.head.appendChild(css);
  document.body.appendChild(wrap);

  var audio=new Audio('https://media.salus-mind.com/content/audio-free/narrator-welcome.mp3');
  var playBtn=wrap.querySelector('.narrator-float__play');
  var iconPlay=wrap.querySelector('.narrator-float__icon-play');
  var iconPause=wrap.querySelector('.narrator-float__icon-pause');
  var bar=wrap.querySelector('.narrator-float__bar');
  var track=wrap.querySelector('.narrator-float__track');
  var timeEl=wrap.querySelector('.narrator-float__time');
  var closeBtn=wrap.querySelector('.narrator-float__close');

  function fmt(s){var m=Math.floor(s/60);return m+':'+(('0'+Math.floor(s%60)).slice(-2));}

  audio.currentTime=st.time;
  audio.play().then(function(){
    iconPlay.style.display='none';iconPause.style.display='block';
  }).catch(function(){
    // Autoplay blocked — show play button, user can tap to resume
    iconPlay.style.display='block';iconPause.style.display='none';
  });

  playBtn.addEventListener('click',function(){
    if(audio.paused){
      audio.play();iconPlay.style.display='none';iconPause.style.display='block';
    }else{
      audio.pause();iconPlay.style.display='block';iconPause.style.display='none';
    }
  });
  audio.addEventListener('timeupdate',function(){
    if(audio.duration){bar.style.width=(audio.currentTime/audio.duration*100)+'%';timeEl.textContent=fmt(audio.currentTime);}
  });
  audio.addEventListener('ended',function(){
    sessionStorage.removeItem('narrator');wrap.remove();
  });
  track.addEventListener('click',function(e){
    if(audio.duration){var rect=track.getBoundingClientRect();audio.currentTime=(e.clientX-rect.left)/rect.width*audio.duration;}
  });
  closeBtn.addEventListener('click',function(){
    audio.pause();sessionStorage.removeItem('narrator');wrap.remove();
  });

  // Save state if navigating again
  window.addEventListener('beforeunload',function(){
    if(!audio.paused&&audio.currentTime>0){
      sessionStorage.setItem('narrator',JSON.stringify({playing:true,time:audio.currentTime}));
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
