import { useEffect, useState } from "react";
import { apiRequest } from "./api";
import Login from "./Login";
import AnalyzeTransaction from "./AnalyzeTransaction";
import Signup from "./Signup";
import ReviewQueue from "./ReviewQueue";
import Transactions from "./Transactions";
import {
  BarChart3,
  CreditCard,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  User,
} from "lucide-react";
import "./App.css";

function App() {

  const token = localStorage.getItem("access_token");
  if (window.location.pathname === "/signup") {
    return <Signup />;
  }
  if (window.location.pathname === "/transactions") {
    return <Transactions />;
  }
  if (window.location.pathname === "/analyze") {
    return <AnalyzeTransaction />;
  }
  if (window.location.pathname === "/review") {
  return <ReviewQueue />;
}
  const [profileOpen, setProfileOpen] = useState(false);
  const [user, setUser] = useState<{
    id: number;
    email: string;
    role: string;
    created_at: string;
  } | null>(null);

  const [stats, setStats] = useState({
    total: 0,
    approved: 0,
    review: 0,
    blocked: 0,
  });
  const [recentTransactions, setRecentTransactions] = useState<
    {
      id: number;
      amount: number;
      currency: string;
      merchant_id: string;
      status: string;
      created_at: string;
    }[]
  >([]);

  useEffect(() => {
    async function loadProfile() {
      try {
        const data = await apiRequest<{
          id: number;
          email: string;
          role: string;
          created_at: string;
        }>("/auth/me");

        setUser(data);
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
    }

    async function loadStats() {
      try {
        const data = await apiRequest<{
          total: number;
          approved: number;
          review: number;
          blocked: number;
        }>("/transactions/stats");

        setStats(data);
      } catch {
        // Keep default zero values if stats cannot be loaded.
      }
    }

    async function loadRecentTransactions() {
      try {
        const data = await apiRequest<{
          items: {
            id: number;
            amount: number;
            currency: string;
            merchant_id: string;
            status: string;
            created_at: string;
          }[];
          total: number;
          page: number;
          page_size: number;
          has_next: boolean;
        }>("/transactions/?page=1&page_size=5");

        setRecentTransactions(data.items);
      } catch (err) {
        console.error("Recent transactions error:", err);
      }
    }

    loadProfile();
    loadStats();
    loadRecentTransactions();
  }, []);

  if (!token) {
    return <Login />;
  }

  return (
    <div className="app">
      {profileOpen && (
        <div
          className="profile-overlay"
          onClick={() => setProfileOpen(false)}
        >
          <div
            className="profile-panel"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="profile-panel-header">
              <div>
                <span className="panel-label">
                  ACCOUNT
                </span>

                <h2>Profile</h2>
              </div>

              <button
                className="profile-close"
                onClick={() => setProfileOpen(false)}
              >
                ×
              </button>
            </div>

            {user ? (
              <div className="profile-details">
                <div>
                  <span>Email</span>
                  <strong>{user.email}</strong>
                </div>

                <div>
                  <span>User ID</span>
                  <strong>{user.id}</strong>
                </div>

                <div>
                  <span>Role</span>
                  <strong>{user.role}</strong>
                </div>

                <div>
                  <span>Account created</span>
                  <strong>
                    {new Date(
                      user.created_at,
                    ).toLocaleDateString()}
                  </strong>
                </div>
              </div>
            ) : (
              <p>Loading profile...</p>
            )}
          </div>
        </div>
      )}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={22} />
          </div>

          <div>
            <div className="brand-name">
              Fraud-Spike
            </div>
            <div className="brand-subtitle">
              DETECTOR
            </div>
          </div>
        </div>

        <nav className="navigation">
          <div className="nav-section">
            <span>MONITORING</span>
          </div>

          <a className="nav-item active">
            <LayoutDashboard size={18} />
            Dashboard
          </a>

          <button
            className="nav-item"
            onClick={() => setProfileOpen(true)}
          >
            <User size={18} />
            Profile
          </button>

          <button
            className="nav-item"
            onClick={() => {
              window.location.href = "/transactions";
            }}
          >
            <CreditCard size={18} />
            Transactions
          </button>

          <div className="nav-section">
            <span>MANAGEMENT</span>
          </div>

          <button
  className="nav-item"
  onClick={() => {
    window.location.href = "/review";
  }}
>
  <BarChart3 size={18} />
  Review Queue
</button>

        </nav>

        <div className="sidebar-bottom">
          <button
            className="logout-button"
            onClick={async () => {
              const refreshToken =
                localStorage.getItem("refresh_token");

              try {
                if (refreshToken) {
                  await apiRequest("/auth/logout", {
                    method: "POST",
                    body: JSON.stringify({
                      refresh_token: refreshToken,
                    }),
                  });
                }
              } catch {
                // Even if the backend request fails,
                // clear local authentication state.
              }

              localStorage.removeItem("access_token");
              localStorage.removeItem("refresh_token");

              window.location.reload();
            }}
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <div className="page-label">
              RISK MONITORING
            </div>

            <h1>Dashboard</h1>
          </div>

          <div className="system-status">
            <span className="status-dot" />
            API ONLINE
          </div>
        </header>

        <section className="content">
          <div className="welcome">
            <div>
              <p className="eyebrow">
                FRAUD INTELLIGENCE
              </p>

              <h2>
                Real-time transaction risk.
              </h2>

              <p className="welcome-text">
                Monitor transaction behavior, analyze
                fraud risk, and review suspicious activity.
              </p>
            </div>

            <button
              className="primary-button"
              onClick={() => {
                window.location.href = "/analyze";
              }}
            >
              Analyze Transaction
            </button>
          </div>

          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">TOTAL TRANSACTIONS</span>
              <strong>{stats.total}</strong>
              <span className="stat-meta">All analyzed transactions</span>
            </div>

            <div className="stat-card">
              <span className="stat-label">APPROVED</span>
              <strong>{stats.approved}</strong>
              <span className="stat-meta">Safe transactions</span>
            </div>

            <div className="stat-card">
              <span className="stat-label">REVIEW</span>
              <strong>{stats.review}</strong>
              <span className="stat-meta">Awaiting decision</span>
            </div>

            <div className="stat-card">
              <span className="stat-label">BLOCKED</span>
              <strong>{stats.blocked}</strong>
              <span className="stat-meta">High-risk attempts</span>
            </div>
          </div>

          <div className="dashboard-grid">
            <section className="panel">
              <div className="panel-header">
                <div>
                  <span className="panel-label">
                    ACTIVITY
                  </span>
                  <h3>Recent Transactions</h3>
                </div>

                <button
                  className="text-button"
                  onClick={() => {
                    window.location.href = "/transactions";
                  }}
                >
                  View all
                </button>
              </div>

              <div className="transaction-list">
                {recentTransactions.map((transaction) => (
                  <div className="transaction-row" key={transaction.id}>
                    <div>
                      <strong>{transaction.merchant_id}</strong>
                      <span>
                        {new Date(transaction.created_at).toLocaleString()}
                      </span>
                    </div>

                    <div>
                      <strong>
                        {transaction.currency} {transaction.amount.toFixed(2)}
                      </strong>
                      <span>{transaction.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="panel risk-panel">
              <div className="panel-header">
                <div>
                  <span className="panel-label">
                    RISK ENGINE
                  </span>
                  <h3>System Status</h3>
                </div>
              </div>

              <div className="system-row">
                <span>Fraud model</span>
                <span className="badge success">
                  READY
                </span>
              </div>

              <div className="system-row">
                <span>PostgreSQL</span>
                <span className="badge success">
                  ONLINE
                </span>
              </div>

              <div className="system-row">
                <span>Redis feature store</span>
                <span className="badge success">
                  ONLINE
                </span>
              </div>

              <div className="system-row">
                <span>Risk decisions</span>
                <span className="badge success">
                  ACTIVE
                </span>
              </div>
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;