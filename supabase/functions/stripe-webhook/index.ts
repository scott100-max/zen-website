// Supabase Edge Function: Stripe Webhook Handler
// Handles Stripe payment events and updates subscriptions table

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import Stripe from "https://esm.sh/stripe@12.0.0?target=deno";

const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY") as string, {
  apiVersion: "2023-10-16",
  httpClient: Stripe.createFetchHttpClient(),
});

const supabaseUrl = Deno.env.get("SUPABASE_URL") as string;
const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") as string;

const supabase = createClient(supabaseUrl, supabaseServiceKey);

const webhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET") as string;

serve(async (req: Request) => {
  const signature = req.headers.get("stripe-signature");

  if (!signature) {
    return new Response("No signature", { status: 400 });
  }

  try {
    const body = await req.text();
    const cryptoProvider = Stripe.createSubtleCryptoProvider();
    const event = await stripe.webhooks.constructEventAsync(
      body,
      signature,
      webhookSecret,
      undefined,
      cryptoProvider
    );

    console.log(`Received event: ${event.type}`);

    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session;
        await handleCheckoutComplete(session);
        break;
      }

      case "customer.subscription.updated": {
        const subscription = event.data.object as Stripe.Subscription;
        await handleSubscriptionUpdated(subscription);
        break;
      }

      case "customer.subscription.deleted": {
        const subscription = event.data.object as Stripe.Subscription;
        await handleSubscriptionDeleted(subscription);
        break;
      }

      case "invoice.payment_succeeded": {
        const invoice = event.data.object as Stripe.Invoice;
        await handleInvoicePaid(invoice);
        break;
      }

      case "invoice.payment_failed": {
        const invoice = event.data.object as Stripe.Invoice;
        await handleInvoiceFailed(invoice);
        break;
      }

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: { "Content-Type": "application/json" },
      status: 200,
    });
  } catch (err) {
    console.error("Webhook error:", err);
    return new Response(`Webhook Error: ${err.message}`, { status: 400 });
  }
});

async function handleCheckoutComplete(session: Stripe.Checkout.Session) {
  // Get user ID from client_reference_id (set during checkout)
  const userId = session.client_reference_id;

  if (!userId) {
    console.error("No client_reference_id in checkout session");
    return;
  }

  // Get subscription details from Stripe
  const subscriptionId = session.subscription as string;
  if (!subscriptionId) {
    console.error("No subscription in checkout session");
    return;
  }

  const stripeSubscription = await stripe.subscriptions.retrieve(subscriptionId);

  // Determine plan type based on interval
  const priceId = stripeSubscription.items.data[0]?.price.id;
  const interval = stripeSubscription.items.data[0]?.price.recurring?.interval;
  const planType = interval === "year" ? "yearly" : "monthly";

  // Upsert subscription in database
  const { error } = await supabase.from("subscriptions").upsert(
    {
      user_id: userId,
      stripe_customer_id: session.customer as string,
      stripe_subscription_id: subscriptionId,
      plan_type: planType,
      status: "active",
      current_period_end: new Date(
        stripeSubscription.current_period_end * 1000
      ).toISOString(),
    },
    {
      onConflict: "user_id",
    }
  );

  if (error) {
    console.error("Error upserting subscription:", error);
  } else {
    console.log(`Subscription created for user ${userId}`);
  }
}

async function handleSubscriptionUpdated(subscription: Stripe.Subscription) {
  const customerId = subscription.customer as string;

  // Find subscription by Stripe customer ID
  const { data: existingSubscription, error: fetchError } = await supabase
    .from("subscriptions")
    .select("*")
    .eq("stripe_customer_id", customerId)
    .single();

  if (fetchError || !existingSubscription) {
    console.error("Subscription not found for customer:", customerId);
    return;
  }

  // Determine new status
  let status = "active";
  if (subscription.status === "canceled" || subscription.status === "unpaid") {
    status = "expired";
  } else if (subscription.status === "past_due") {
    status = "past_due";
  } else if (subscription.status === "trialing") {
    status = "trialing";
  }

  // Update subscription
  const { error } = await supabase
    .from("subscriptions")
    .update({
      status: status,
      current_period_end: new Date(
        subscription.current_period_end * 1000
      ).toISOString(),
    })
    .eq("stripe_customer_id", customerId);

  if (error) {
    console.error("Error updating subscription:", error);
  } else {
    console.log(`Subscription updated for customer ${customerId}`);
  }
}

async function handleSubscriptionDeleted(subscription: Stripe.Subscription) {
  const customerId = subscription.customer as string;

  // Mark subscription as expired
  const { error } = await supabase
    .from("subscriptions")
    .update({
      status: "expired",
    })
    .eq("stripe_customer_id", customerId);

  if (error) {
    console.error("Error marking subscription as expired:", error);
  } else {
    console.log(`Subscription marked as expired for customer ${customerId}`);
  }
}

async function handleInvoicePaid(invoice: Stripe.Invoice) {
  const customerId = invoice.customer as string;
  const subscriptionId = invoice.subscription as string;

  if (!subscriptionId) return;

  // Fetch the subscription to get the new period end
  const subscription = await stripe.subscriptions.retrieve(subscriptionId);

  // Update the subscription period end
  const { error } = await supabase
    .from("subscriptions")
    .update({
      status: "active",
      current_period_end: new Date(
        subscription.current_period_end * 1000
      ).toISOString(),
    })
    .eq("stripe_customer_id", customerId);

  if (error) {
    console.error("Error updating subscription after payment:", error);
  } else {
    console.log(`Subscription renewed for customer ${customerId}`);
  }
}

async function handleInvoiceFailed(invoice: Stripe.Invoice) {
  const customerId = invoice.customer as string;

  // Mark subscription as past_due
  const { error } = await supabase
    .from("subscriptions")
    .update({
      status: "past_due",
    })
    .eq("stripe_customer_id", customerId);

  if (error) {
    console.error("Error marking subscription as past_due:", error);
  } else {
    console.log(`Subscription marked as past_due for customer ${customerId}`);
  }
}
