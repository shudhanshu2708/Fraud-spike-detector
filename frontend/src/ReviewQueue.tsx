import { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";
import { apiRequest } from "./api";

type ReviewTransaction = {
  id: number;
  amount: number;
  currency: string;
  merchant_id: string;
  device_id: string;
  ip_address: string;
  status: string;
  created_at: string;
  risk_score: number;
  risk_decision: string;
  risk_reasons: string[];
  reviewed_by: number | null;
  reviewed_at: string | null;
};

export default function ReviewQueue() {
  const [transactions, setTransactions] = useState<
    ReviewTransaction[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadReviewQueue() {
    try {
      const data = await apiRequest<{
        items: ReviewTransaction[];
        total: number;
        page: number;
        page_size: number;
        has_next: boolean;
      }>("/admin/transactions?status=REVIEW");

      setTransactions(data.items);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load review queue",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReviewQueue();
  }, []);

  async function handleDecision(
    transactionId: number,
    decision: "approve" | "reject",
  ) {
    try {
      await apiRequest(
        `/admin/transactions/${transactionId}/${decision}`,
        {
          method: "POST",
        },
      );

      setTransactions((current) =>
        current.filter(
          (transaction) => transaction.id !== transactionId,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update transaction",
      );
    }
  }

  return (
    <main className="main">
      <header className="topbar">
        <div>
          <div className="page-label">
            RISK MONITORING
          </div>

          <h1>Review Queue</h1>
        </div>
      </header>

      <section className="content">
        <section className="panel transactions-panel">
          <div className="panel-header">
            <div>
              <span className="panel-label">
                MANUAL REVIEW
              </span>

              <h3>Transactions awaiting decision</h3>
            </div>
          </div>

          {loading && (
            <div className="empty-state">
              <p>Loading review queue...</p>
            </div>
          )}

          {error && (
            <div className="empty-state">
              <p>{error}</p>
            </div>
          )}

          {!loading &&
            !error &&
            transactions.length === 0 && (
              <div className="empty-state">
                <ShieldAlert size={28} />

                <p>No transactions awaiting review.</p>

                <span>
                  Transactions requiring manual review
                  will appear here.
                </span>
              </div>
            )}

          {!loading &&
            !error &&
            transactions.length > 0 && (
              <div className="transactions-list">
                {transactions.map((transaction) => (
                  <div
                    className="transaction-row"
                    key={transaction.id}
                  >
                    <div>
                      <strong>
                        #{transaction.id}
                      </strong>

                      <span>
                        {transaction.merchant_id}
                      </span>

                      <span>
                        {new Date(
                          transaction.created_at,
                        ).toLocaleString()}
                      </span>
                    </div>

                    <div>
                      <strong>
                        {transaction.currency}{" "}
                        {transaction.amount.toFixed(2)}
                      </strong>

                      <span>
                        Risk:{" "}
                        {transaction.risk_score.toFixed(2)}
                      </span>
                    </div>

                    <div>
                      <button
                        className="text-button"
                        onClick={() =>
                          handleDecision(
                            transaction.id,
                            "approve",
                          )
                        }
                      >
                        Approve
                      </button>

                      <button
                        className="text-button"
                        onClick={() =>
                          handleDecision(
                            transaction.id,
                            "reject",
                          )
                        }
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
        </section>
      </section>
    </main>
  );
}