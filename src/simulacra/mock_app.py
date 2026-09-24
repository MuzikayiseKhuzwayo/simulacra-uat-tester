"""Self-contained local demo web application for Simulacra UAT testing.

Provides realistic SaaS and e-commerce workflows with intentional UX friction points
(e.g., hidden secondary buttons, validation boundaries, pricing tables, multi-step forms)
for offline deterministic simulation.
"""

import http.server
import threading
import time
from typing import ClassVar


HTML_LANDING = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AcmeCloud — Modern Cloud Billing & Invoicing</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; color: #1e293b; background: #f8fafc; }
    header { background: #0f172a; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
    header a { color: #94a3b8; text-decoration: none; margin-left: 1.5rem; font-weight: 500; }
    header a:hover { color: #38bdf8; }
    .hero { padding: 4rem 2rem; text-align: center; max-width: 800px; margin: 0 auto; }
    .hero h1 { font-size: 2.75rem; margin-bottom: 1rem; color: #0f172a; }
    .hero p { font-size: 1.25rem; color: #64748b; line-height: 1.6; margin-bottom: 2rem; }
    .btn { display: inline-block; background: #2563eb; color: white; padding: 0.85rem 1.75rem; border-radius: 0.5rem; text-decoration: none; font-weight: 600; cursor: pointer; border: none; font-size: 1rem; }
    .btn:hover { background: #1d4ed8; }
    .btn-secondary { background: #e2e8f0; color: #334155; margin-left: 1rem; }
    .btn-secondary:hover { background: #cbd5e1; }
    .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 2rem; max-width: 1000px; margin: 3rem auto; padding: 0 2rem; }
    .card { background: white; padding: 2rem; border-radius: 0.75rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .card h3 { margin-top: 0; color: #1e293b; }
    .card p { color: #64748b; font-size: 0.95rem; }
    .social-proof { text-align: center; padding: 2rem; background: #e0f2fe; margin-top: 4rem; }
    .rage-target { opacity: 0.85; border: 1px dashed #94a3b8; padding: 0.5rem 1rem; border-radius: 4px; display: inline-block; cursor: pointer; color: #64748b; font-size: 0.85rem; margin-top: 1rem; }
    footer { text-align: center; padding: 2rem; color: #94a3b8; font-size: 0.875rem; }
  </style>
</head>
<body>
  <header>
    <div><strong>AcmeCloud</strong></div>
    <nav>
      <a href="/" id="nav-home">Home</a>
      <a href="/pricing" id="nav-pricing">Pricing</a>
      <a href="/signup" id="nav-signup">Sign Up</a>
      <a href="/docs" id="nav-docs">Docs</a>
      <a href="/dashboard" id="nav-dashboard">Dashboard</a>
    </nav>
  </header>
  <div class="hero">
    <h1>Automate Enterprise Billing with Zero Friction</h1>
    <p>Empower your finance and engineering teams with self-service automated invoicing, real-time telemetry, and smart subscription analytics.</p>
    <div>
      <a href="/signup" class="btn" id="hero-cta-signup">Start Free 14-Day Trial</a>
      <a href="/pricing" class="btn btn-secondary" id="hero-cta-pricing">View Pricing Plans</a>
    </div>
    <div style="margin-top: 1.5rem;">
      <!-- Subtle unclickable badge that frustrated users often click -->
      <span class="rage-target" id="unresponsive-live-demo-badge" onclick="console.log('demo clicked');">⚡ Click here for Instant Sandbox Demo</span>
    </div>
  </div>
  <div class="features">
    <div class="card">
      <h3>Instant Invoicing</h3>
      <p>Generate compliant VAT and multi-currency invoices in 15 seconds flat.</p>
    </div>
    <div class="card">
      <h3>Automated Dunning</h3>
      <p>Recover 70% of failed credit card transactions with smart retries.</p>
    </div>
    <div class="card">
      <h3>SOC2 & GDPR Ready</h3>
      <p>Bank-grade encryption, role-based access control, and complete audit logging.</p>
    </div>
  </div>
  <div class="social-proof">
    <p><strong>Trusted by 10,000+ businesses globally</strong></p>
    <a href="/signup" class="btn" style="background:#0284c7;" id="footer-cta">Get Started Free</a>
  </div>
  <footer>&copy; 2026 AcmeCloud Technologies Inc. All rights reserved.</footer>
</body>
</html>
"""

HTML_PRICING = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Pricing Plans — AcmeCloud</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; color: #1e293b; background: #f8fafc; }
    header { background: #0f172a; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
    header a { color: #94a3b8; text-decoration: none; margin-left: 1.5rem; font-weight: 500; }
    .container { max-width: 1000px; margin: 3rem auto; padding: 0 1rem; }
    h1 { text-align: center; color: #0f172a; margin-bottom: 0.5rem; }
    .subtitle { text-align: center; color: #64748b; margin-bottom: 3rem; }
    .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; }
    .plan-card { background: white; border: 1px solid #e2e8f0; border-radius: 0.75rem; padding: 2rem; text-align: center; position: relative; }
    .plan-card.popular { border: 2px solid #2563eb; }
    .badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #2563eb; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; }
    .price { font-size: 2.5rem; font-weight: 700; color: #0f172a; margin: 1rem 0; }
    .price span { font-size: 1rem; color: #64748b; font-weight: normal; }
    ul { list-style: none; padding: 0; margin: 2rem 0; text-align: left; }
    li { padding: 0.5rem 0; color: #475569; border-bottom: 1px solid #f1f5f9; }
    .btn { display: block; width: 100%; box-sizing: border-box; background: #2563eb; color: white; padding: 0.85rem; border-radius: 0.5rem; text-decoration: none; font-weight: 600; cursor: pointer; border: none; }
    .btn:hover { background: #1d4ed8; }
    .btn-outline { background: white; color: #2563eb; border: 1px solid #2563eb; }
    .btn-outline:hover { background: #eff6ff; }
  </style>
</head>
<body>
  <header>
    <div><strong>AcmeCloud</strong></div>
    <nav>
      <a href="/" id="nav-home">Home</a>
      <a href="/pricing" id="nav-pricing">Pricing</a>
      <a href="/signup" id="nav-signup">Sign Up</a>
      <a href="/docs" id="nav-docs">Docs</a>
    </nav>
  </header>
  <div class="container">
    <h1>Predictable, Transparent Pricing</h1>
    <p class="subtitle">Choose the plan that fits your growth. No hidden setup fees or surprise charges.</p>
    <div class="pricing-grid">
      <div class="plan-card">
        <h3>Starter</h3>
        <div class="price">$29<span>/mo</span></div>
        <ul>
          <li>Up to 100 invoices/month</li>
          <li>Basic email support</li>
          <li>1 admin user</li>
        </ul>
        <a href="/signup?plan=starter" class="btn btn-outline" id="plan-starter-btn">Choose Starter</a>
      </div>
      <div class="plan-card popular">
        <span class="badge">MOST POPULAR</span>
        <h3>Growth</h3>
        <div class="price">$99<span>/mo</span></div>
        <ul>
          <li>Unlimited invoices</li>
          <li>Priority 24/7 support</li>
          <li>5 team members</li>
          <li>Automated smart dunning</li>
        </ul>
        <a href="/signup?plan=growth" class="btn" id="plan-growth-btn">Start 14-Day Growth Trial</a>
      </div>
      <div class="plan-card">
        <h3>Enterprise</h3>
        <div class="price">$299<span>/mo</span></div>
        <ul>
          <li>Dedicated account manager</li>
          <li>Custom SLA & security review</li>
          <li>Unlimited team members</li>
          <li>Custom Webhooks & API rate limits</li>
        </ul>
        <a href="/signup?plan=enterprise" class="btn btn-outline" id="plan-enterprise-btn">Contact Enterprise</a>
      </div>
    </div>
  </div>
</body>
</html>
"""

HTML_SIGNUP = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sign Up — AcmeCloud</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; color: #1e293b; background: #f1f5f9; }
    header { background: #0f172a; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; }
    header a { color: #94a3b8; text-decoration: none; }
    .form-box { max-width: 440px; margin: 3rem auto; background: white; padding: 2.5rem; border-radius: 0.75rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }
    h2 { margin-top: 0; color: #0f172a; }
    .field { margin-bottom: 1.25rem; }
    label { display: block; font-weight: 500; margin-bottom: 0.5rem; font-size: 0.9rem; }
    input[type="text"], input[type="email"], input[type="password"], select { width: 100%; box-sizing: border-box; padding: 0.75rem; border: 1px solid #cbd5e1; border-radius: 0.375rem; font-size: 1rem; }
    .btn-submit { width: 100%; background: #2563eb; color: white; padding: 0.85rem; border: none; border-radius: 0.375rem; font-size: 1rem; font-weight: 600; cursor: pointer; margin-top: 1rem; }
    .btn-submit:hover { background: #1d4ed8; }
    .error-banner { display: none; background: #fee2e2; border: 1px solid #ef4444; color: #b91c1c; padding: 0.75rem; border-radius: 0.375rem; margin-bottom: 1rem; font-size: 0.875rem; }
    .success-banner { display: none; background: #dcfce7; border: 1px solid #22c55e; color: #15803d; padding: 1rem; border-radius: 0.375rem; text-align: center; }
  </style>
</head>
<body>
  <header>
    <div><strong>AcmeCloud</strong></div>
    <a href="/">Back to Home</a>
  </header>
  <div class="form-box">
    <div id="error-message" class="error-banner"></div>
    <div id="signup-container">
      <h2>Create Your Account</h2>
      <p style="color:#64748b; font-size:0.9rem; margin-bottom:1.5rem;">Start your 14-day free trial. No credit card required.</p>
      <form id="signup-form" onsubmit="handleSignup(event)">
        <div class="field">
          <label for="name">Full Name</label>
          <input type="text" id="name" name="name" placeholder="Sarah Jenkins" required>
        </div>
        <div class="field">
          <label for="email">Work Email</label>
          <input type="email" id="email" name="email" placeholder="sarah@example.com" required>
        </div>
        <div class="field">
          <label for="password">Password</label>
          <input type="password" id="password" name="password" placeholder="At least 8 characters" required>
        </div>
        <div class="field">
          <label for="company_size">Company Size</label>
          <select id="company_size" name="company_size">
            <option value="1-10">1 - 10 employees</option>
            <option value="11-50">11 - 50 employees</option>
            <option value="51-200">51 - 200 employees</option>
            <option value="200+">200+ employees</option>
          </select>
        </div>
        <button type="submit" class="btn-submit" id="btn-submit-signup">Complete Registration</button>
      </form>
    </div>
    <div id="success-container" class="success-banner">
      <h3>🎉 Welcome to AcmeCloud!</h3>
      <p>Your workspace is ready. You are now logged in.</p>
      <a href="/dashboard" class="btn-submit" style="display:inline-block; text-decoration:none; margin-top:1rem;" id="btn-go-dashboard">Go to Dashboard</a>
    </div>
  </div>
  <script>
    function handleSignup(e) {
      e.preventDefault();
      var name = document.getElementById('name').value.trim();
      var email = document.getElementById('email').value.trim();
      var pass = document.getElementById('password').value;
      var err = document.getElementById('error-message');

      if (!name || !email || !pass) {
        err.innerText = "Please complete all mandatory fields.";
        err.style.display = "block";
        return;
      }
      if (pass.length < 8) {
        err.innerText = "Password must be at least 8 characters.";
        err.style.display = "block";
        return;
      }
      err.style.display = "none";
      document.getElementById('signup-container').style.display = "none";
      document.getElementById('success-container').style.display = "block";
    }
  </script>
</body>
</html>
"""

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Dashboard — AcmeCloud</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; color: #1e293b; background: #f8fafc; }
    header { background: #0f172a; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
    header a { color: #94a3b8; text-decoration: none; margin-left: 1.5rem; }
    .container { max-width: 1100px; margin: 2rem auto; padding: 0 1.5rem; }
    .metric-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    .metric-card { background: white; border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1.5rem; }
    .metric-card h4 { margin: 0; color: #64748b; font-size: 0.85rem; font-weight: 500; text-transform: uppercase; }
    .metric-card .val { font-size: 2rem; font-weight: 700; color: #0f172a; margin-top: 0.5rem; }
    .table-card { background: white; border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1.5rem; }
    .table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }
    table { width: 100%; border-collapse: collapse; text-align: left; }
    th { border-bottom: 2px solid #e2e8f0; padding: 0.75rem 0.5rem; font-size: 0.85rem; color: #64748b; }
    td { border-bottom: 1px solid #f1f5f9; padding: 0.75rem 0.5rem; font-size: 0.95rem; }
    .badge-paid { background: #dcfce7; color: #15803d; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
    .btn-create { background: #2563eb; color: white; padding: 0.6rem 1.2rem; border: none; border-radius: 0.375rem; cursor: pointer; font-weight: 600; }
    .btn-create:hover { background: #1d4ed8; }
    .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; }
    .modal-box { background: white; padding: 2rem; border-radius: 0.5rem; width: 400px; }
  </style>
</head>
<body>
  <header>
    <div><strong>AcmeCloud</strong> Console</div>
    <nav>
      <a href="/" id="nav-home">Home</a>
      <a href="/pricing" id="nav-pricing">Pricing</a>
      <a href="/dashboard" id="nav-dashboard">Dashboard</a>
      <a href="/docs" id="nav-docs">Docs</a>
    </nav>
  </header>
  <div class="container">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
      <h1 style="margin:0; font-size:1.75rem;" id="dashboard-heading">Invoice Management</h1>
      <button class="btn-create" id="btn-new-invoice" onclick="openModal()">+ Create New Invoice</button>
    </div>
    <div class="metric-row">
      <div class="metric-card">
        <h4>Monthly Recurring</h4>
        <div class="val">$48,250</div>
      </div>
      <div class="metric-card">
        <h4>Paid Invoices</h4>
        <div class="val">142</div>
      </div>
      <div class="metric-card">
        <h4>Pending Recovery</h4>
        <div class="val">$3,120</div>
      </div>
    </div>
    <div class="table-card">
      <div class="table-header">
        <h3 style="margin:0;">Recent Invoices</h3>
      </div>
      <table>
        <thead>
          <tr>
            <th>Invoice ID</th>
            <th>Client</th>
            <th>Amount</th>
            <th>Date</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="invoice-tbody">
          <tr>
            <td><strong>INV-2026-001</strong></td>
            <td>Stripe Corp</td>
            <td>$12,400.00</td>
            <td>2026-09-20</td>
            <td><span class="badge-paid">Paid</span></td>
          </tr>
          <tr>
            <td><strong>INV-2026-002</strong></td>
            <td>Nexus Media</td>
            <td>$4,850.00</td>
            <td>2026-09-22</td>
            <td><span class="badge-paid">Paid</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
  <div id="invoice-modal" class="modal">
    <div class="modal-box">
      <h3>Create New Invoice</h3>
      <div style="margin-bottom:1rem;">
        <label style="display:block; margin-bottom:0.5rem; font-size:0.9rem;">Client Name</label>
        <input type="text" id="modal-client" style="width:100%; box-sizing:border-box; padding:0.5rem; border:1px solid #cbd5e1; border-radius:4px;" placeholder="Acme Partner">
      </div>
      <div style="margin-bottom:1.5rem;">
        <label style="display:block; margin-bottom:0.5rem; font-size:0.9rem;">Amount ($)</label>
        <input type="text" id="modal-amount" style="width:100%; box-sizing:border-box; padding:0.5rem; border:1px solid #cbd5e1; border-radius:4px;" placeholder="1500.00">
      </div>
      <div style="display:flex; justify-content:flex-end; gap:0.5rem;">
        <button onclick="closeModal()" style="padding:0.5rem 1rem; border:1px solid #cbd5e1; background:white; border-radius:4px; cursor:pointer;" id="modal-cancel-btn">Cancel</button>
        <button onclick="submitInvoice()" class="btn-create" id="modal-confirm-btn">Confirm & Issue</button>
      </div>
    </div>
  </div>
  <script>
    function openModal() { document.getElementById('invoice-modal').style.display = 'flex'; }
    function closeModal() { document.getElementById('invoice-modal').style.display = 'none'; }
    function submitInvoice() {
      var client = document.getElementById('modal-client').value || 'New Client';
      var amount = document.getElementById('modal-amount').value || '1000.00';
      var tbody = document.getElementById('invoice-tbody');
      var tr = document.createElement('tr');
      tr.innerHTML = '<td><strong>INV-2026-NEW</strong></td><td>' + client + '</td><td>$' + amount + '</td><td>Today</td><td><span class=\"badge-paid\">Issued</span></td>';
      tbody.appendChild(tr);
      closeModal();
      alert('Invoice successfully issued!');
    }
  </script>
</body>
</html>
"""

HTML_DOCS = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>API Documentation — AcmeCloud</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; color: #1e293b; background: #ffffff; }
    header { background: #0f172a; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; }
    header a { color: #94a3b8; text-decoration: none; margin-left: 1rem; }
    .layout { display: flex; max-width: 1200px; margin: 0 auto; }
    aside { width: 240px; border-right: 1px solid #e2e8f0; padding: 2rem 1rem; min-height: 80vh; }
    aside a { display: block; color: #475569; text-decoration: none; padding: 0.5rem; border-radius: 4px; font-size: 0.9rem; }
    aside a:hover { background: #f1f5f9; color: #2563eb; }
    main { flex: 1; padding: 2rem 3rem; }
    pre { background: #0f172a; color: #f8fafc; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; font-family: monospace; font-size: 0.9rem; }
  </style>
</head>
<body>
  <header>
    <div><strong>AcmeCloud</strong> Developer Portal</div>
    <nav>
      <a href="/" id="nav-home">Home</a>
      <a href="/pricing" id="nav-pricing">Pricing</a>
      <a href="/dashboard" id="nav-dashboard">Dashboard</a>
    </nav>
  </header>
  <div class="layout">
    <aside>
      <a href="#quickstart" id="doc-quickstart">Quickstart</a>
      <a href="#authentication" id="doc-auth">Authentication</a>
      <a href="#invoices-api" id="doc-invoices">Invoices API</a>
      <a href="#webhooks" id="doc-webhooks">Webhooks</a>
    </aside>
    <main>
      <h1>Developer REST API Reference</h1>
      <p>Integrate automated recurring billing into any frontend or backend service using JSON webhooks and standard HTTPS REST endpoints.</p>
      <h2 id="authentication">Authentication</h2>
      <p>All API calls must include your Bearer token in the Authorization header:</p>
      <pre><code>Authorization: Bearer sk_live_9812938102938102</code></pre>
      <h2 id="invoices-api">Create Invoice Endpoint</h2>
      <p>POST /v1/invoices</p>
      <pre><code>curl -X POST https://api.acmecloud.com/v1/invoices \\
  -H "Authorization: Bearer sk_live_xxx" \\
  -d '{"client_id": "cli_991", "amount": 2500}'</code></pre>
    </main>
  </div>
</body>
</html>
"""


class MockAppHandler(http.server.BaseHTTPRequestHandler):
    """Serve simulated multi-page application."""

    def log_message(self, format: str, *args: object) -> None:
        # Suppress noisy HTTP stdout logs during automated simulation runs
        pass

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            content = HTML_LANDING
        elif path == "/pricing":
            content = HTML_PRICING
        elif path == "/signup":
            content = HTML_SIGNUP
        elif path == "/dashboard":
            content = HTML_DASHBOARD
        elif path == "/docs":
            content = HTML_DOCS
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))


class MockAppServer:
    """Threaded HTTP server providing local test target."""

    _instance: ClassVar["MockAppServer | None"] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, port: int = 8585, host: str = "127.0.0.1") -> None:
        self.port = port
        self.host = host
        self.server: http.server.ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.is_running = False

    @classmethod
    def get_or_start(cls, port: int = 8585) -> "MockAppServer":
        """Singleton accessor to ensure test server is active."""
        with cls._lock:
            if cls._instance is None or not cls._instance.is_running:
                server = MockAppServer(port=port)
                server.start()
                cls._instance = server
            return cls._instance

    def start(self) -> None:
        if self.is_running:
            return
        self.server = http.server.ThreadingHTTPServer(
            (self.host, self.port), MockAppHandler
        )
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.thread.start()
        self.is_running = True
        time.sleep(0.1)

    def stop(self) -> None:
        if self.server and self.is_running:
            self.server.shutdown()
            self.server.server_close()
            self.is_running = False

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"
