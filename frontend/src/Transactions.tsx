import { useEffect, useState } from "react";
import { CreditCard } from "lucide-react";
import { apiRequest } from "./api";

type Transaction = {
  id: number;
  amount: number;
  currency: string;
  merchant_id: string;
  device_id: string;
  ip_address: string;
  status: string;
  created_at: string;
};

export default function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadTransactions() {
      try {
        const data = await apiRequest<{
           items: Transaction[];
           total: number;
           page: number;
           page_size: number;
           has_next: boolean;
        }>("/transactions/");

        setTransactions(data.items);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load transactions",
        );
      } finally {
        setLoading(false);
      }
    }

    loadTransactions();
  }, []);

  return (
    <main className="main">
      <header className="topbar">
        <div>
          <div className="page-label">
            RISK MONITORING
          </div>

          <h1>Transactions</h1>
        </div>
      </header>

      <section className="content">
        <section className="panel transactions-panel">
          <div className="panel-header">
            <div>
              <span className="panel-label">
                TRANSACTION HISTORY
              </span>

              <h3>Recent Transactions</h3>
            </div>
          </div>

          {loading && (
            <div className="empty-state">
              <p>Loading transactions...</p>
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
                <CreditCard size={28} />

                <p>No transactions yet.</p>

                <span>
                  Transactions analyzed through the risk
                  engine will appear here.
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
                    </div>

                    <div>
                      <strong>
                        {transaction.currency}{" "}
                        {transaction.amount.toFixed(2)}
                      </strong>

                      <span>
                        {new Date(
                          transaction.created_at,
                        ).toLocaleString()}
                      </span>
                    </div>

                    <span
                      className={`badge ${
                        transaction.status ===
                        "APPROVED"
                          ? "success"
                          : transaction.status ===
                              "REVIEW"
                            ? "review"
                            : "rejected"
                      }`}
                    >
                      {transaction.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
        </section>
      </section>
    </main>
  );
}