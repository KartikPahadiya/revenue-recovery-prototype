"""
SendGrid email client for real recovery outreach.
Sends personalized emails for cart reminders, discount codes, and payment notifications.
All cart recovery emails now include the Razorpay payment link for one-click checkout.
Gracefully falls back to simulation if SendGrid is not configured or fails.
"""
import os
import html

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_SENDER = os.getenv("SENDGRID_SENDER", "noreply@revenue-recovery-demo.com")


def _get_client():
    """Lazy import to avoid startup crash if sendgrid is not installed."""
    from sendgrid import SendGridAPIClient
    return SendGridAPIClient(SENDGRID_API_KEY)

def send_personalized_email(
    customer_name: str,
    customer_email: str,
    subject: str,
    body_text: str,
    payment_url: str | None = None,
    discount_code: str | None = None,
) -> dict:
    """Send an LLM-drafted email. body_text is plain text drafted by the
    LLM; discount_code/payment_url are inserted by code, never by the LLM."""
    safe_name = html.escape(customer_name)
    safe_body = html.escape(body_text).replace("\n", "<br>")
    link_html = _payment_link_html(payment_url)

    discount_html = ""
    if discount_code:
        discount_html = f"""
        <div style="background: #1a3a1a; border: 2px dashed #4ade80; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; color: #4ade80; font-size: 14px; font-weight: 600;">YOUR EXCLUSIVE CODE</p>
            <p style="margin: 10px 0; color: #4ade80; font-size: 32px; font-weight: 700; letter-spacing: 2px;">{html.escape(discount_code)}</p>
        </div>
        """

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #d97706;">Hi {safe_name},</h2>
        <p>{safe_body}</p>
        {discount_html}
        {link_html}
        <a href="https://revenue-recovery-prototype.onrender.com/"
           style="display: inline-block; background: #d97706; color: white; padding: 12px 24px;
                  text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 10px;">
            Browse Store →
        </a>
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            This is a demo from the AI Revenue Recovery Agent. No actual purchase will be charged.
        </p>
    </div>
    """
    return _send_email(customer_email, html.unescape(subject), html_content)

def _send_email(to_email: str, subject: str, html_content: str) -> dict:
    """Send email via SendGrid. Returns result dict."""
    if not SENDGRID_API_KEY:
        return {"sent": False, "error": "SENDGRID_API_KEY not configured"}

    try:
        sg = _get_client()
        from sendgrid.helpers.mail import Mail
        message = Mail(
            from_email=SENDGRID_SENDER,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
        response = sg.send(message)
        return {
            "sent": True,
            "status_code": response.status_code,
        }
    except Exception as e:
        return {"sent": False, "error": str(e)}


def _payment_link_html(payment_url: str | None) -> str:
    """Generate HTML for the Razorpay payment link block."""
    if not payment_url:
        return ""
    return f"""
    <div style="background: #1a3a1a; border: 2px solid #4ade80; padding: 18px; text-align: center; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0; color: #4ade80; font-size: 13px; font-weight: 600;">ONE-CLICK CHECKOUT</p>
        <p style="margin: 6px 0; color: #a89f92; font-size: 12px;">Secure payment via Razorpay (Test Mode)</p>
        <a href="{payment_url}" 
           style="display: inline-block; background: #4ade80; color: #14100c; padding: 12px 28px; 
                  text-decoration: none; border-radius: 6px; font-weight: 700; font-size: 15px; margin-top: 8px;">
            Pay Now →
        </a>
    </div>
    """


def send_cart_reminder_email(customer_name: str, customer_email: str, items: str, cart_value: float, payment_url: str | None = None) -> dict:
    """Send a personalized cart reminder email with payment link."""
    subject = f"Hey {customer_name}, you left something behind! 🛒"
    link_html = _payment_link_html(payment_url)
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #d97706;">Hi {customer_name},</h2>
        <p>You were checking out these items but didn't complete your purchase:</p>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <p style="margin: 0; font-weight: 600;">{items}</p>
            <p style="margin: 10px 0 0 0; font-size: 18px; color: #d97706;">Total: ₹{cart_value:,.0f}</p>
        </div>
        <p>Come back and complete your order — your items are waiting!</p>
        {link_html}
        <a href="https://revenue-recovery-prototype.onrender.com/" 
           style="display: inline-block; background: #d97706; color: white; padding: 12px 24px; 
                  text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 10px;">
            Browse Store →
        </a>
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            This is a demo from the AI Revenue Recovery Agent. No actual purchase will be charged.
        </p>
    </div>
    """
    return _send_email(customer_email, subject, html)


def send_discount_code_email(customer_name: str, customer_email: str, items: str, cart_value: float, payment_url: str | None = None) -> dict:
    """Send a discount code email for high-value abandoned carts with payment link."""
    discount_code = f"SAVE{cart_value:.0f}"
    subject = f"{customer_name}, here's 10% off your ₹{cart_value:,.0f} cart! 🎉"
    link_html = _payment_link_html(payment_url)
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #d97706;">Hi {customer_name},</h2>
        <p>We noticed you left these items in your cart:</p>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <p style="margin: 0; font-weight: 600;">{items}</p>
            <p style="margin: 10px 0 0 0; font-size: 18px; color: #d97706;">Cart Value: ₹{cart_value:,.0f}</p>
        </div>
        <p>Here's a special discount to help you complete your order:</p>
        <div style="background: #1a3a1a; border: 2px dashed #4ade80; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; color: #4ade80; font-size: 14px; font-weight: 600;">YOUR EXCLUSIVE CODE</p>
            <p style="margin: 10px 0; color: #4ade80; font-size: 32px; font-weight: 700; letter-spacing: 2px;">
                {discount_code}
            </p>
            <p style="margin: 0; color: #a89f92; font-size: 13px;">10% off your entire cart</p>
        </div>
        {link_html}
        <a href="https://revenue-recovery-prototype.onrender.com/" 
           style="display: inline-block; background: #d97706; color: white; padding: 12px 24px; 
                  text-decoration: none; border-radius: 6px; font-weight: 600;">
            Browse Store →
        </a>
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            This is a demo from the AI Revenue Recovery Agent. No actual purchase will be charged.
        </p>
    </div>
    """
    result = _send_email(customer_email, subject, html)
    if result["sent"]:
        result["discount_code"] = discount_code
    return result


def send_product_recommendation_email(customer_name: str, customer_email: str, items: str, payment_url: str | None = None) -> dict:
    """Send a product recommendation email with payment link."""
    suggestions = "🍯 Honey, 🥜 Peanut Butter, 🍌 Bananas"
    if "bread" in items.lower():
        suggestions = "🍯 Honey, 🥜 Peanut Butter, 🧈 Extra Butter"
    elif "milk" in items.lower():
        suggestions = "🍫 Chocolate Powder, 🍪 Cookies, 🥣 Cornflakes"
    elif "noodles" in items.lower():
        suggestions = "🥚 Eggs, 🧈 Butter, 🌶️ Schezwan Sauce"

    subject = f"{customer_name}, people also bought these with your items 🛍️"
    link_html = _payment_link_html(payment_url)
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #d97706;">Hi {customer_name},</h2>
        <p>You were looking at: <strong>{items}</strong></p>
        <p>Customers who bought these also loved:</p>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <p style="margin: 0; font-size: 24px; text-align: center;">{suggestions}</p>
        </div>
        <p>Add them to your cart and complete your order!</p>
        {link_html}
        <a href="https://revenue-recovery-prototype.onrender.com/" 
           style="display: inline-block; background: #d97706; color: white; padding: 12px 24px; 
                  text-decoration: none; border-radius: 6px; font-weight: 600;">
            Continue Shopping →
        </a>
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            This is a demo from the AI Revenue Recovery Agent. No actual purchase will be charged.
        </p>
    </div>
    """
    return _send_email(customer_email, subject, html)


def send_payment_notification_email(customer_name: str, customer_email: str, failure_reason: str, amount: float, payment_url: str | None = None) -> dict:
    """Send a payment failure notification with retry payment link."""
    subject = f"{customer_name}, your payment of ₹{amount:,.0f} needs attention 🔧"
    link_html = _payment_link_html(payment_url)
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #d97706;">Hi {customer_name},</h2>
        <p>We noticed an issue with your recent payment attempt:</p>
        <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <p style="margin: 0; color: #856404; font-weight: 600;">
                Issue: {failure_reason}
            </p>
            <p style="margin: 10px 0 0 0; color: #856404;">
                Amount: ₹{amount:,.0f}
            </p>
        </div>
        <p>Don't worry — your order is still saved. You can retry your payment now:</p>
        {link_html}
        <a href="https://revenue-recovery-prototype.onrender.com/" 
           style="display: inline-block; background: #d97706; color: white; padding: 12px 24px; 
                  text-decoration: none; border-radius: 6px; font-weight: 600;">
            Browse Store →
        </a>
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            This is a demo from the AI Revenue Recovery Agent. No actual purchase will be charged.
        </p>
    </div>
    """
    return _send_email(customer_email, subject, html)
