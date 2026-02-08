#!/bin/bash
# Validation script for Supabase Auth System
# Run from /Users/scottripley/salus-website

PASS=0
FAIL=0

check() {
    if [ "$2" = "true" ]; then
        echo "✓ $1"
        ((PASS++))
    else
        echo "✗ $1"
        ((FAIL++))
    fi
}

echo "=========================================="
echo "SUPABASE AUTH SYSTEM VALIDATION"
echo "=========================================="
echo ""

# 1. New Files Exist
echo "--- New Files ---"
if [ -f "js/supabase-config.js" ]; then check "js/supabase-config.js exists" "true"; else check "js/supabase-config.js exists" "false"; fi
if [ -f "js/auth.js" ]; then check "js/auth.js exists" "true"; else check "js/auth.js exists" "false"; fi
if [ -f "login.html" ]; then check "login.html exists" "true"; else check "login.html exists" "false"; fi
if [ -f "signup.html" ]; then check "signup.html exists" "true"; else check "signup.html exists" "false"; fi
if [ -f "dashboard.html" ]; then check "dashboard.html exists" "true"; else check "dashboard.html exists" "false"; fi
if [ -f "reset-password.html" ]; then check "reset-password.html exists" "true"; else check "reset-password.html exists" "false"; fi
if [ -f "supabase/functions/stripe-webhook/index.ts" ]; then check "stripe-webhook/index.ts exists" "true"; else check "stripe-webhook/index.ts exists" "false"; fi
if [ -f "supabase/migrations/001_create_auth_tables.sql" ]; then check "SQL migration exists" "true"; else check "SQL migration exists" "false"; fi

echo ""
echo "--- Supabase Config ---"
grep -q "egywowuyixfqytaucihf.supabase.co" js/supabase-config.js && check "Project URL configured" "true" || check "Project URL configured" "false"
grep -q "eyJ" js/supabase-config.js && check "Legacy JWT anon key (not sb_publishable_)" "true" || check "Legacy JWT anon key (not sb_publishable_)" "false"

echo ""
echo "--- Auth Module (js/auth.js) ---"
grep -q "async function signUp" js/auth.js && check "signUp function exists" "true" || check "signUp function exists" "false"
grep -q "async function signIn" js/auth.js && check "signIn function exists" "true" || check "signIn function exists" "false"
grep -q "async function signOut" js/auth.js && check "signOut function exists" "true" || check "signOut function exists" "false"
grep -q "function isPremium" js/auth.js && check "isPremium function exists" "true" || check "isPremium function exists" "false"
grep -q "function updateNavUI" js/auth.js && check "updateNavUI function exists" "true" || check "updateNavUI function exists" "false"
grep -q "salus_premium" js/auth.js && check "localStorage fallback for legacy premium" "true" || check "localStorage fallback for legacy premium" "false"

echo ""
echo "--- HTML Pages Updated ---"
# Check a sample of pages for Supabase scripts
grep -q "supabase-config.js" index.html && check "index.html has supabase-config.js" "true" || check "index.html has supabase-config.js" "false"
grep -q "nav-auth-btn" index.html && check "index.html has nav-auth-btn" "true" || check "index.html has nav-auth-btn" "false"
grep -q "supabase-config.js" sessions.html && check "sessions.html has supabase-config.js" "true" || check "sessions.html has supabase-config.js" "false"
grep -q "nav-auth-btn" sessions.html && check "sessions.html has nav-auth-btn" "true" || check "sessions.html has nav-auth-btn" "false"
grep -q "supabase-config.js" soundscapes.html && check "soundscapes.html has supabase-config.js" "true" || check "soundscapes.html has supabase-config.js" "false"
grep -q "nav-auth-btn" soundscapes.html && check "soundscapes.html has nav-auth-btn" "true" || check "soundscapes.html has nav-auth-btn" "false"

# Count total pages with auth
AUTH_PAGES=$(grep -l "nav-auth-btn" *.html sessions/*.html 2>/dev/null | wc -l | tr -d ' ')
echo "   (Total pages with nav-auth-btn: $AUTH_PAGES)"

echo ""
echo "--- apps.html (Subscribe Flow) ---"
grep -q "stripe-subscribe-btn" apps.html && check "Subscribe buttons have class for JS targeting" "true" || check "Subscribe buttons have class for JS targeting" "false"
grep -q "Create Account to Subscribe" apps.html && check "Non-logged-in text present" "true" || check "Non-logged-in text present" "false"
grep -q "SalusAuth.isLoggedIn" apps.html && check "Login state check in JS" "true" || check "Login state check in JS" "false"

echo ""
echo "--- thank-you.html (Failsafe) ---"
grep -q "createAccountPrompt" thank-you.html && check "Account creation prompt element exists" "true" || check "Account creation prompt element exists" "false"
grep -q "same email you just paid with" thank-you.html && check "Prompt text for email matching" "true" || check "Prompt text for email matching" "false"

echo ""
echo "--- signup.html ---"
grep -q "Start your Salus journey" signup.html && check "Subtitle updated" "true" || check "Subtitle updated" "false"
grep -q "redirect" signup.html && check "Redirect parameter handling" "true" || check "Redirect parameter handling" "false"

echo ""
echo "--- login.html ---"
grep -q "redirect" login.html && check "Redirect parameter handling" "true" || check "Redirect parameter handling" "false"

echo ""
echo "--- main.js (Premium Logic) ---"
grep -q "SalusAuth" js/main.js && check "Defers to SalusAuth when available" "true" || check "Defers to SalusAuth when available" "false"

echo ""
echo "--- Stripe Webhook ---"
grep -q "checkout.session.completed" supabase/functions/stripe-webhook/index.ts && check "Handles checkout.session.completed" "true" || check "Handles checkout.session.completed" "false"
grep -q "customer.subscription.updated" supabase/functions/stripe-webhook/index.ts && check "Handles subscription.updated" "true" || check "Handles subscription.updated" "false"
grep -q "customer.subscription.deleted" supabase/functions/stripe-webhook/index.ts && check "Handles subscription.deleted" "true" || check "Handles subscription.deleted" "false"
grep -q "invoice.payment_succeeded" supabase/functions/stripe-webhook/index.ts && check "Handles invoice.payment_succeeded" "true" || check "Handles invoice.payment_succeeded" "false"
grep -q "invoice.payment_failed" supabase/functions/stripe-webhook/index.ts && check "Handles invoice.payment_failed" "true" || check "Handles invoice.payment_failed" "false"

echo ""
echo "--- SQL Migration ---"
grep -q "CREATE TABLE.*profiles" supabase/migrations/001_create_auth_tables.sql && check "profiles table defined" "true" || check "profiles table defined" "false"
grep -q "CREATE TABLE.*subscriptions" supabase/migrations/001_create_auth_tables.sql && check "subscriptions table defined" "true" || check "subscriptions table defined" "false"
grep -q "ENABLE ROW LEVEL SECURITY" supabase/migrations/001_create_auth_tables.sql && check "RLS enabled" "true" || check "RLS enabled" "false"
grep -q "handle_new_user" supabase/migrations/001_create_auth_tables.sql && check "Auto-create profile trigger" "true" || check "Auto-create profile trigger" "false"

echo ""
echo "=========================================="
echo "RESULTS: $PASS passed, $FAIL failed"
echo "=========================================="

if [ $FAIL -eq 0 ]; then
    echo "All checks passed!"
    exit 0
else
    echo "Some checks failed. Review above."
    exit 1
fi
