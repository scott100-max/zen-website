// ===== Salus — Visitor Location Tracker =====
// Anonymized geolocation tracking (no IP stored)

(function() {
  'use strict';

  // Skip if already tracked this session
  if (sessionStorage.getItem('salus_tracked')) return;

  // Skip if Supabase not available
  if (!window.salusSupabase) return;

  // Skip bots
  if (/bot|crawl|spider|slurp|facebook|twitter|whatsapp/i.test(navigator.userAgent)) return;

  // Set flag immediately to prevent race-condition duplicates
  sessionStorage.setItem('salus_tracked', '1');

  // Skip admin/owner visits — if logged into Supabase, don't track
  window.salusSupabase.auth.getSession().then(function(result) {
    if (result.data && result.data.session) return; // logged-in user = admin, skip

    doTrack();
  }).catch(function() {
    doTrack(); // auth check failed, track anyway
  });

  function doTrack() {
    // Generate a session ID for dedup
    var sessionId = crypto.randomUUID ? crypto.randomUUID() :
      'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
      });

    // Fetch geolocation — ip-api.com gives neighbourhood-level precision
    fetch('http://ip-api.com/json/?fields=status,country,regionName,city,zip,lat,lon')
      .then(function(res) { return res.json(); })
      .then(function(geo) {
        if (!geo || geo.status !== 'success') return;

        window.salusSupabase
          .from('visitor_logs')
          .insert({
            country: geo.country || null,
            city: geo.city || null,
            region: geo.regionName || null,
            latitude: geo.lat || null,
            longitude: geo.lon || null,
            landing_page: window.location.pathname,
            user_agent: navigator.userAgent.substring(0, 500),
            session_id: sessionId
          })
          .then(function() { /* silent */ })
          .catch(function() { /* silent */ });
      })
      .catch(function() { /* silent — ad blocker or network error */ });
  }
})();
