// ===== Salus — Visitor Analytics Tracker =====
// Privacy-respecting: no cookies, no IP storage, localStorage opt-out
// Tables: visitors, page_views, events (see migration 003)

(function() {
  'use strict';

  // ===== 1. Guards =====

  // Skip bots
  if (/bot|crawl|spider|slurp|facebook|twitter|whatsapp|pingdom|lighthouse|gtmetrix|pagespeed/i.test(navigator.userAgent)) return;

  // Permanent opt-out: visit any page with ?salus_notrack
  if (window.location.search.indexOf('salus_notrack') !== -1) {
    localStorage.setItem('salus_notrack', '1');
    return;
  }
  if (localStorage.getItem('salus_notrack')) return;

  // Skip if Supabase not available
  if (!window.salusSupabase) return;

  // Skip admin/owner visits
  window.salusSupabase.auth.getSession().then(function(result) {
    if (result.data && result.data.session) return; // logged-in = admin, skip
    initTracker();
  }).catch(function() {
    initTracker(); // auth check failed, track anyway
  });

  function initTracker() {
    var sb = window.salusSupabase;
    var SB_URL = 'https://egywowuyixfqytaucihf.supabase.co';
    var SB_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVneXdvd3V5aXhmcXl0YXVjaWhmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAyNzE0OTgsImV4cCI6MjA4NTg0NzQ5OH0.XMA7XDaQocuWQKq6kMuPOy6J3qGJ4k8h5T2p2JdEFJI';

    // ===== 2. Visitor Identity =====

    // Persistent visitor ID (survives sessions)
    var visitorId = localStorage.getItem('salus_vid');
    var isNewVisitor = !visitorId;
    if (!visitorId) {
      visitorId = genUUID();
      localStorage.setItem('salus_vid', visitorId);
    }

    // Session ID (one per tab session)
    var sessionId = sessionStorage.getItem('salus_sid');
    var isNewSession = !sessionId;
    if (!sessionId) {
      sessionId = genUUID();
      sessionStorage.setItem('salus_sid', sessionId);
    }

    // ===== 3. Geo Lookup =====

    var geoPromise;
    var cachedGeo = sessionStorage.getItem('salus_geo');
    if (cachedGeo) {
      geoPromise = Promise.resolve(JSON.parse(cachedGeo));
    } else {
      geoPromise = fetch('https://ipapi.co/json/')
        .then(function(res) { return res.json(); })
        .then(function(data) {
          if (data && !data.error) {
            var geo = {
              country: data.country_name || null,
              city: data.city || null,
              region: data.region || null,
              timezone: data.timezone || null,
              latitude: data.latitude || null,
              longitude: data.longitude || null
            };
            sessionStorage.setItem('salus_geo', JSON.stringify(geo));
            return geo;
          }
          return null;
        })
        .catch(function() { return null; });
    }

    // ===== 4. Visitor Upsert + Page View =====

    geoPromise.then(function(geo) {
      geo = geo || {};

      // Ensure visitor record exists before inserting page view (FK constraint)
      var visitorReady;
      if (isNewVisitor) {
        visitorReady = sb.from('visitors').insert({
          id: visitorId,
          total_sessions: 1,
          country: geo.country,
          city: geo.city,
          region: geo.region,
          timezone: geo.timezone,
          user_agent: navigator.userAgent.substring(0, 500)
        }).then(function() {}).catch(function() {});
      } else if (isNewSession) {
        // Returning visitor, new session — update last_seen + increment sessions
        visitorReady = sb.rpc('increment_visitor_session', { vid: visitorId }).then(function(result) {
          if (result.error) {
            return sb.from('visitors')
              .update({ last_seen: new Date().toISOString() })
              .eq('id', visitorId);
          }
        }).catch(function() {
          return sb.from('visitors')
            .update({ last_seen: new Date().toISOString() })
            .eq('id', visitorId);
        });
      } else {
        visitorReady = Promise.resolve();
      }

      // Also write to legacy visitor_logs (first page view per session only)
      if (isNewSession) {
        sb.from('visitor_logs').insert({
          country: geo.country,
          city: geo.city,
          region: geo.region,
          latitude: geo.latitude,
          longitude: geo.longitude,
          landing_page: window.location.pathname,
          user_agent: navigator.userAgent.substring(0, 500),
          session_id: sessionId
        }).then(function() {}).catch(function() {});
      }

      // Parse UTM params
      var params = new URLSearchParams(window.location.search);
      var utmSource = params.get('utm_source');
      var utmMedium = params.get('utm_medium');
      var utmCampaign = params.get('utm_campaign');
      var utmContent = params.get('utm_content');
      var utmTerm = params.get('utm_term');

      // Referrer — only external
      var ref = document.referrer;
      if (ref) {
        try { if (new URL(ref).hostname === window.location.hostname) ref = ''; }
        catch(e) { ref = ''; }
      }

      // Wait for visitor record to exist, then insert page view
      pageViewId = genUUID();
      visitorReady.then(function() {
        sb.from('page_views').insert({
          id: pageViewId,
          visitor_id: visitorId,
          session_id: sessionId,
          page_path: window.location.pathname,
          page_title: document.title,
          referrer: ref || null,
          utm_source: utmSource,
          utm_medium: utmMedium,
          utm_campaign: utmCampaign,
          utm_content: utmContent,
          utm_term: utmTerm,
          country: geo.country,
          city: geo.city,
          region: geo.region,
          latitude: geo.latitude,
          longitude: geo.longitude
        }).then(function() {}).catch(function() {});
      }).catch(function() {});
    });

    // ===== 5. Duration + Scroll Tracking =====

    var pageViewId = null;
    var pageLoadTime = Date.now();
    var maxScrollPct = 0;
    var durationSent = false;
    var MAX_DURATION = 1800; // 30 min cap

    window.addEventListener('scroll', function() {
      var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      var docHeight = Math.max(
        document.body.scrollHeight, document.documentElement.scrollHeight,
        document.body.offsetHeight, document.documentElement.offsetHeight
      );
      var winHeight = window.innerHeight;
      if (docHeight <= winHeight) { maxScrollPct = 100; return; }
      var pct = Math.round((scrollTop + winHeight) / docHeight * 100);
      if (pct > maxScrollPct) maxScrollPct = Math.min(pct, 100);
    }, { passive: true });

    function sendDuration() {
      if (!pageViewId || durationSent) return;
      durationSent = true;
      var elapsed = Math.round((Date.now() - pageLoadTime) / 1000);
      if (elapsed > MAX_DURATION) elapsed = MAX_DURATION;
      if (elapsed < 1) return;

      var url = SB_URL + '/rest/v1/page_views?id=eq.' + pageViewId;
      var body = JSON.stringify({
        duration_seconds: elapsed,
        scroll_depth_pct: maxScrollPct
      });

      // Use fetch with keepalive for page unload reliability
      try {
        fetch(url, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'apikey': SB_KEY,
            'Authorization': 'Bearer ' + SB_KEY,
            'Prefer': 'return=minimal'
          },
          body: body,
          keepalive: true
        });
      } catch(e) { /* silent */ }
    }

    // Send on tab hidden or page unload
    document.addEventListener('visibilitychange', function() {
      if (document.visibilityState === 'hidden') {
        sendDuration();
        // Allow re-sending if user comes back and leaves again
        setTimeout(function() { durationSent = false; }, 1000);
      }
    });
    window.addEventListener('pagehide', sendDuration);

    // ===== 6. Event Tracking =====

    function trackEvent(type, target, value) {
      sb.from('events').insert({
        visitor_id: visitorId,
        session_id: sessionId,
        page_path: window.location.pathname,
        event_type: type,
        event_target: target ? String(target).substring(0, 500) : null,
        event_value: value != null ? String(value) : null
      }).then(function() {}).catch(function() {});
    }

    // Expose for custom event tracking
    window.salusTrack = trackEvent;

    // --- Audio play/pause/ended ---
    function getTrackName(mediaEl) {
      var card = mediaEl.closest('.sound-card');
      if (card) { var h3 = card.querySelector('h3'); if (h3) return h3.textContent; }
      card = mediaEl.closest('.session-card');
      if (card) { var h3 = card.querySelector('h3'); if (h3) return h3.textContent; }
      var src = mediaEl.querySelector('source') ? mediaEl.querySelector('source').src : mediaEl.src;
      if (src) {
        var parts = src.split('/');
        return decodeURIComponent(parts[parts.length - 1]).replace(/\.[^.]+$/, '').replace(/[-_]/g, ' ');
      }
      return 'Unknown Track';
    }

    function hookMediaTracking() {
      document.querySelectorAll('audio, video').forEach(function(el) {
        if (el._salusTrackHooked) return;
        el._salusTrackHooked = true;

        el.addEventListener('play', function() {
          trackEvent('audio_play', getTrackName(el), Math.round(el.currentTime));
        });
        el.addEventListener('pause', function() {
          if (!el.ended) {
            trackEvent('audio_pause', getTrackName(el), Math.round(el.currentTime));
          }
        });
        el.addEventListener('ended', function() {
          trackEvent('audio_complete', getTrackName(el), Math.round(el.duration || 0));
        });
      });
    }

    // Hook now and re-hook on DOM changes (for dynamically added players)
    hookMediaTracking();
    var observer = new MutationObserver(function() { hookMediaTracking(); });
    observer.observe(document.body, { childList: true, subtree: true });

    // --- CTA clicks ---
    document.addEventListener('click', function(e) {
      var link = e.target.closest('a');
      if (!link) return;

      var href = link.getAttribute('href') || '';
      // Track clicks to subscribe/apps page and external CTAs
      if (href.indexOf('apps.html') !== -1 || link.classList.contains('nav-cta--subscribe')) {
        trackEvent('cta_click', href, (link.textContent || '').trim().substring(0, 100));
      }
    });

    // --- Scroll milestones ---
    var scrollMilestones = { 25: false, 50: false, 75: false, 100: false };
    window.addEventListener('scroll', function() {
      var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      var docHeight = Math.max(
        document.body.scrollHeight, document.documentElement.scrollHeight,
        document.body.offsetHeight, document.documentElement.offsetHeight
      );
      var winHeight = window.innerHeight;
      if (docHeight <= winHeight) return; // short page, skip
      var pct = Math.round((scrollTop + winHeight) / docHeight * 100);

      [25, 50, 75, 100].forEach(function(milestone) {
        if (pct >= milestone && !scrollMilestones[milestone]) {
          scrollMilestones[milestone] = true;
          trackEvent('scroll_milestone', milestone + '%', null);
        }
      });
    }, { passive: true });
  }

  // ===== Helpers =====

  function genUUID() {
    if (crypto.randomUUID) return crypto.randomUUID();
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

})();
