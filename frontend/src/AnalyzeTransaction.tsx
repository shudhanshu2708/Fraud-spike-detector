import { type FormEvent, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { apiRequest } from "./api";

type RiskResult = {
  transaction_id: number | null;
  transaction_created: boolean;
  status: string | null;
  risk_score: number;
  decision: string;
  reasons: string[];
  transactions_1m: number;
  transactions_5m: number;
  amount_5m: number;
  created_at: string | null;
};

export default function AnalyzeTransaction() {
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("INR");
  const [merchantId, setMerchantId] = useState("");
  const [deviceId, setDeviceId] = useState("");
  const [ipAddress, setIpAddress] = useState("");

  const [result, setResult] = useState<RiskResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setError("");
    setResult(null);
    setLoading(true);

    try {
      const data = await apiRequest<RiskResult>("/transactions/", {
        method: "POST",
        headers: {
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: JSON.stringify({
          amount: Number(amount),
          currency,
          merchant_id: merchantId,
          device_id: deviceId,
          ip_address: ipAddress,
        }),
      });

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to analyze transaction",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="main">
      <header className="topbar">
        <div>
          <div className="page-label">
            RISK ENGINE
          </div>

          <h1>Analyze Transaction</h1>
        </div>
      </header>

      <section className="content">
        <div className="analyze-grid">
          <section className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-label">
                  TRANSACTION INPUT
                </span>

                <h3>Risk Analysis</h3>
              </div>
            </div>

            <form
              className="analyze-form"
              onSubmit={handleSubmit}
            >
              <label>
                Amount
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={amount}
                  onChange={(e) =>
                    setAmount(e.target.value)
                  }
                  placeholder="5000"
                  required
                />
              </label>

              <label>
                Currency
                <input
                  value={currency}
                  onChange={(e) =>
                    setCurrency(
                      e.target.value.toUpperCase(),
                    )
                  }
                  maxLength={3}
                  required
                />
              </label>

              <label>
                Merchant ID
                <input
                  value={merchantId}
                  onChange={(e) =>
                    setMerchantId(e.target.value)
                  }
                  placeholder="merchant_001"
                  required
                />
              </label>

              <label>
                Device ID
                <input
                  value={deviceId}
                  onChange={(e) =>
                    setDeviceId(e.target.value)
                  }
                  placeholder="device_001"
                  required
                />
              </label>

              <label>
                IP Address
                <input
                  value={ipAddress}
                  onChange={(e) =>
                    setIpAddress(e.target.value)
                  }
                  placeholder="192.168.1.10"
                  required
                />
              </label>

              {error && (
                <div className="auth-error">
                  {error}
                </div>
              )}

              <button
                className="primary-button"
                type="submit"
                disabled={loading}
              >
                {loading
                  ? "Analyzing..."
                  : "Analyze Transaction"}
              </button>
            </form>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-label">
                  MODEL OUTPUT
                </span>

                <h3>Risk Decision</h3>
              </div>
            </div>

            {!result && !loading && (
              <div className="empty-state">
                <ShieldCheck size={28} />

                <p>No analysis yet.</p>

                <span>
                  Submit a transaction to receive a
                  fraud risk decision.
                </span>
              </div>
            )}

            {loading && (
              <div className="empty-state">
                <p>Running fraud analysis...</p>
              </div>
            )}

            {result && (
              <div className="risk-result">
                <div className="risk-score">
                  <span>RISK SCORE</span>
                  <strong>
                    {(result.risk_score * 100).toFixed(1)}%
                  </strong>
                </div>

                <div className="decision-row">
                  <span>Decision</span>
                  <span className="badge success">
                    {result.decision}
                  </span>
                </div>

                <div className="decision-row">
                  <span>Transaction status</span>
                  <strong>
                    {result.status ?? "BLOCKED"}
                  </strong>
                </div>

                <div className="reasons">
                  <span className="panel-label">
                    RISK SIGNALS
                  </span>

                  {result.reasons.length > 0 ? (
                    result.reasons.map((reason) => (
                      <div
                        className="reason"
                        key={reason}
                      >
                        {reason}
                      </div>
                    ))
                  ) : (
                    <div className="reason">
                      No risk signals reported.
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}