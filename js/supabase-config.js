// ===== Salus — Supabase Configuration =====
// Initialize Supabase client with public keys

(function() {
  'use strict';

  // Supabase project credentials (safe to expose - anon key only)
  var SUPABASE_URL = 'https://egywowuyixfqytaucihf.supabase.co';
  var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVneXdvd3V5aXhmcXl0YXVjaWhmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAyNzE0OTgsImV4cCI6MjA4NTg0NzQ5OH0.XMA7XDaQocuWQKq6kMuPOy6J3qGJ4k8h5T2p2JdEFJI';

  // Initialize Supabase client
  if (typeof window.supabase !== 'undefined' && window.supabase.createClient) {
    window.salusSupabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  } else {
    console.warn('Supabase JS library not loaded. Auth features will be unavailable.');
    window.salusSupabase = null;
  }
})();
