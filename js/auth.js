// ===== Salus — Authentication Module =====
// Handles user authentication, premium status, and UI updates

var SalusAuth = (function() {
  'use strict';

  var supabase = null;
  var currentUser = null;
  var subscription = null;
  var initPromise = null;

  // Initialize auth module
  async function init() {
    // If already initializing or initialized, return the existing promise
    if (initPromise) return initPromise;

    initPromise = (async function() {
      supabase = window.salusSupabase;
      if (!supabase) {
        console.warn('Supabase not available. Using localStorage fallback.');
        updateNavUI();
        return;
      }

      // Get current session
      try {
        var { data: { session } } = await supabase.auth.getSession();
        if (session) {
          currentUser = session.user;
          await loadSubscription();
        } else {
          // Check localStorage backup (fallback if Supabase session lost)
          var backupUserId = localStorage.getItem('salus_user_id');
          var backupEmail = localStorage.getItem('salus_user_email');
          if (backupUserId && backupEmail) {
            currentUser = { id: backupUserId, email: backupEmail };
          }
        }
      } catch (err) {
        console.error('Error getting session:', err);
        // Check localStorage backup on error too
        var backupUserId = localStorage.getItem('salus_user_id');
        var backupEmail = localStorage.getItem('salus_user_email');
        if (backupUserId && backupEmail) {
          currentUser = { id: backupUserId, email: backupEmail };
        }
      }

      // Listen for auth state changes (for future updates)
      supabase.auth.onAuthStateChange(function(event, session) {
        if (session) {
          currentUser = session.user;
          loadSubscription().then(function() {
            updateNavUI();
          });
        } else {
          currentUser = null;
          subscription = null;
          updateNavUI();
        }
      });

      updateNavUI();
    })();

    return initPromise;
  }

  // Load user's subscription from database
  async function loadSubscription() {
    // Skip if no supabase, no user, or using localStorage fallback (no real session)
    if (!supabase || !currentUser || !currentUser.aud) {
      subscription = null;
      return;
    }

    try {
      var { data, error } = await supabase
        .from('subscriptions')
        .select('*')
        .eq('user_id', currentUser.id)
        .eq('status', 'active')
        .single();

      if (error && error.code !== 'PGRST116') {
        // PGRST116 = no rows returned (not an error for us)
        console.error('Error loading subscription:', error);
      }
      subscription = data || null;
    } catch (err) {
      console.error('Error loading subscription:', err);
      subscription = null;
    }
  }

  // Sign up with email and password
  async function signUp(email, password, fullName) {
    if (!supabase) {
      return { error: { message: 'Authentication service unavailable' } };
    }

    try {
      var { data, error } = await supabase.auth.signUp({
        email: email,
        password: password,
        options: {
          data: {
            full_name: fullName
          }
        }
      });

      if (error) {
        return { error: error };
      }

      return { data: data };
    } catch (err) {
      return { error: { message: err.message } };
    }
  }

  // Sign in with email and password
  async function signIn(email, password) {
    if (!supabase) {
      return { error: { message: 'Authentication service unavailable' } };
    }

    try {
      var { data, error } = await supabase.auth.signInWithPassword({
        email: email,
        password: password
      });

      if (error) {
        return { error: error };
      }

      currentUser = data.user;
      // Store login state as backup
      localStorage.setItem('salus_user_id', data.user.id);
      localStorage.setItem('salus_user_email', data.user.email);
      // Load subscription in background - don't block login
      loadSubscription().then(function() {
        updateNavUI();
      }).catch(function(err) {
        console.error('Failed to load subscription:', err);
      });
      updateNavUI();

      return { data: data };
    } catch (err) {
      return { error: { message: err.message } };
    }
  }

  // Sign out
  async function signOut() {
    if (!supabase) {
      return { error: { message: 'Authentication service unavailable' } };
    }

    try {
      var { error } = await supabase.auth.signOut();
      if (error) {
        return { error: error };
      }

      currentUser = null;
      subscription = null;
      // Clear localStorage backup
      localStorage.removeItem('salus_user_id');
      localStorage.removeItem('salus_user_email');
      updateNavUI();

      return { data: true };
    } catch (err) {
      return { error: { message: err.message } };
    }
  }

  // Reset password request
  async function resetPassword(email) {
    if (!supabase) {
      return { error: { message: 'Authentication service unavailable' } };
    }

    try {
      var { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/reset-password.html'
      });

      if (error) {
        return { error: error };
      }

      return { data: true };
    } catch (err) {
      return { error: { message: err.message } };
    }
  }

  // Update password (for reset flow)
  async function updatePassword(newPassword) {
    if (!supabase) {
      return { error: { message: 'Authentication service unavailable' } };
    }

    try {
      var { error } = await supabase.auth.updateUser({
        password: newPassword
      });

      if (error) {
        return { error: error };
      }

      return { data: true };
    } catch (err) {
      return { error: { message: err.message } };
    }
  }

  // Check if user has premium access
  function isPremium() {
    // Check Supabase subscription first
    if (subscription && subscription.status === 'active') {
      // Verify subscription hasn't expired
      if (subscription.current_period_end) {
        var endDate = new Date(subscription.current_period_end);
        if (endDate > new Date()) {
          return true;
        }
      } else {
        // No end date means lifetime or indefinite access
        return true;
      }
    }

    // Fallback: Check localStorage for legacy premium users (migration period)
    if (localStorage.getItem('salus_premium') === 'true') {
      return true;
    }

    return false;
  }

  // Check if user should see migration banner
  function shouldShowMigrationBanner() {
    // Show banner if they have localStorage premium but no account
    var hasLocalPremium = localStorage.getItem('salus_premium') === 'true';
    var hasAccount = currentUser !== null;
    var hasSupabaseSubscription = subscription !== null;
    var bannerDismissed = localStorage.getItem('salus_migration_dismissed') === 'true';

    return hasLocalPremium && !hasSupabaseSubscription && !bannerDismissed;
  }

  // Dismiss migration banner
  function dismissMigrationBanner() {
    localStorage.setItem('salus_migration_dismissed', 'true');
  }

  // Get current user
  function getUser() {
    return currentUser;
  }

  // Get subscription details
  function getSubscription() {
    return subscription;
  }

  // Check if user is logged in
  function isLoggedIn() {
    return currentUser !== null;
  }

  // Update navigation UI based on auth state
  function updateNavUI() {
    // Find login button — old nav uses .nav-auth-btn, new 2-row nav uses .nav-cta--login
    var authBtn = document.querySelector('.nav-auth-btn') || document.querySelector('.nav-cta--login');

    // Detect if we're in a subdirectory by checking existing href pattern
    var pathPrefix = '';
    if (authBtn && (authBtn.getAttribute('href') || '').includes('../')) {
      pathPrefix = '../';
    }

    // Update body classes for CSS-driven visibility
    document.body.classList.toggle('is-logged-in', !!currentUser);
    document.body.classList.toggle('is-premium', isPremium());

    if (authBtn) {
      if (currentUser) {
        authBtn.textContent = 'My Account';
        authBtn.href = pathPrefix + 'dashboard.html';
      } else {
        authBtn.textContent = 'Log In';
        authBtn.href = pathPrefix + 'login.html';
      }
    }

    // Also update login button in mobile drawer (new nav)
    var drawerLogin = document.querySelector('.nav-drawer .nav-cta--login');
    if (drawerLogin) {
      if (currentUser) {
        drawerLogin.textContent = 'My Account';
        drawerLogin.href = pathPrefix + 'dashboard.html';
      } else {
        drawerLogin.textContent = 'Log In';
        drawerLogin.href = pathPrefix + 'login.html';
      }
    }

    // Update premium CTAs for premium users
    if (isPremium()) {
      document.querySelectorAll('a[href="apps.html"], a[href="../apps.html"]').forEach(function(link) {
        var text = link.textContent.trim();
        // Nav subscribe buttons → show "Account" for premium users
        if (text === 'Subscribe' && link.classList.contains('nav-cta--subscribe')) {
          link.textContent = 'Account';
          link.href = pathPrefix + 'dashboard.html';
          return;
        }
        // Footer/page subscribe CTAs → redirect to dashboard
        if (text === 'Subscribe' || text === 'Upgrade to Premium' || text === 'Get Salus Premium' || text === 'Go Premium') {
          link.textContent = 'My Account';
          link.href = pathPrefix + 'dashboard.html';
        }
        // Course unlock buttons → show "You have access"
        if (text === 'Unlock Full Course') {
          link.textContent = 'You Have Access';
          link.href = pathPrefix + 'dashboard.html';
          link.style.background = 'rgba(78,205,196,0.15)';
          link.style.borderColor = 'rgba(78,205,196,0.3)';
        }
      });

      // Hide full-page CTA banner sections for premium users
      document.querySelectorAll('.cta-banner').forEach(function(banner) {
        var hasAppsLink = banner.querySelector('a[href="apps.html"], a[href="../apps.html"]');
        if (hasAppsLink) {
          banner.style.display = 'none';
        }
      });

      // Unlock locked day cards on course pages
      document.querySelectorAll('.day-card.locked').forEach(function(card) {
        card.classList.remove('locked');
        var lockIcon = card.querySelector('svg');
        if (lockIcon) lockIcon.remove();
      });
    }

    // Handle premium content unlock
    handlePremiumContent();

    // Show migration banner if needed
    if (shouldShowMigrationBanner()) {
      showMigrationBanner();
    }
  }

  // Handle premium content display
  function handlePremiumContent() {
    var unlockCta = document.querySelector('.unlock-cta');
    if (unlockCta && isPremium()) {
      unlockCta.innerHTML = '<div style="text-align:center;padding:24px;">' +
        '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#4ecdc4" stroke-width="2" style="margin-bottom:12px;"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>' +
        '<h3 style="margin-bottom:8px;color:#f0eefc;">Premium Unlocked</h3>' +
        '<p style="color:rgba(240,238,252,0.55);margin-bottom:16px;">Audio player coming soon. Thank you for subscribing!</p>' +
        '</div>';
      unlockCta.style.background = 'rgba(78,205,196,0.06)';
      unlockCta.style.border = '1px solid rgba(78,205,196,0.2)';
    }
  }

  // Show migration banner for localStorage premium users
  function showMigrationBanner() {
    // Don't show on auth pages
    var path = window.location.pathname;
    if (path.includes('login') || path.includes('signup') || path.includes('dashboard') || path.includes('reset-password')) {
      return;
    }

    // Check if banner already exists
    if (document.getElementById('salus-migration-banner')) {
      return;
    }

    var banner = document.createElement('div');
    banner.id = 'salus-migration-banner';
    banner.style.cssText = 'position:fixed;bottom:60px;left:24px;right:24px;max-width:480px;z-index:9998;' +
      'background:linear-gradient(135deg,#1e293b,#0f172a);color:#fff;padding:20px 24px;border-radius:12px;' +
      'box-shadow:0 8px 32px rgba(0,0,0,0.3);';
    banner.innerHTML =
      '<div style="display:flex;align-items:flex-start;gap:16px;">' +
        '<div style="flex:1;">' +
          '<h4 style="margin:0 0 8px;font-size:1rem;">Sync Your Premium Access</h4>' +
          '<p style="margin:0;font-size:0.85rem;opacity:0.85;line-height:1.5;">' +
            'Create an account to access your premium content on any device.' +
          '</p>' +
          '<div style="margin-top:16px;display:flex;gap:12px;">' +
            '<a href="signup.html" class="btn btn-primary" style="padding:10px 20px;font-size:0.85rem;">Create Account</a>' +
            '<button onclick="SalusAuth.dismissMigrationBanner();this.closest(\'#salus-migration-banner\').remove();" ' +
              'style="background:none;border:1px solid rgba(255,255,255,0.3);color:#fff;padding:10px 16px;border-radius:50px;' +
              'font-size:0.85rem;cursor:pointer;">Maybe Later</button>' +
          '</div>' +
        '</div>' +
        '<button onclick="SalusAuth.dismissMigrationBanner();this.closest(\'#salus-migration-banner\').remove();" ' +
          'style="background:none;border:none;color:rgba(255,255,255,0.5);font-size:1.5rem;cursor:pointer;padding:0;line-height:1;">&times;</button>' +
      '</div>';

    document.body.appendChild(banner);
  }

  // Refresh subscription (call after successful payment)
  async function refreshSubscription() {
    if (!supabase || !currentUser) return;
    await loadSubscription();
    updateNavUI();
  }

  // Get Stripe checkout URL with user info
  function getStripeCheckoutUrl(baseUrl) {
    if (!currentUser) {
      return baseUrl;
    }

    var separator = baseUrl.includes('?') ? '&' : '?';
    return baseUrl +
      separator + 'client_reference_id=' + encodeURIComponent(currentUser.id) +
      '&prefilled_email=' + encodeURIComponent(currentUser.email);
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Public API
  return {
    init: init,
    signUp: signUp,
    signIn: signIn,
    signOut: signOut,
    resetPassword: resetPassword,
    updatePassword: updatePassword,
    isPremium: isPremium,
    isLoggedIn: isLoggedIn,
    getUser: getUser,
    getSubscription: getSubscription,
    refreshSubscription: refreshSubscription,
    getStripeCheckoutUrl: getStripeCheckoutUrl,
    shouldShowMigrationBanner: shouldShowMigrationBanner,
    dismissMigrationBanner: dismissMigrationBanner,
    updateNavUI: updateNavUI
  };
})();
