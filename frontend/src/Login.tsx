import { type FormEvent, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { apiRequest } from "./api";

type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const data = await apiRequest<TokenResponse>(
        "/auth/login",
        {
          method: "POST",
          body: JSON.stringify({
            email,
            password,
          }),
        },
      );

      localStorage.setItem(
        "access_token",
        data.access_token,
      );

      localStorage.setItem(
        "refresh_token",
        data.refresh_token,
      );

      window.location.href = "/";
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Login failed",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-icon">
            <ShieldCheck size={25} />
          </div>

          <div>
            <div className="auth-brand-name">
              Fraud-Spike
            </div>
            <div className="auth-brand-subtitle">
              DETECTOR
            </div>
          </div>
        </div>

        <div className="auth-heading">
          <span>SECURE ACCESS</span>
          <h1>Welcome back</h1>
          <p>
            Sign in to access the fraud monitoring
            dashboard.
          </p>
        </div>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="you@example.com"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="••••••••"
              required
            />
          </label>

          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          <button
            className="auth-button"
            type="submit"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="auth-footer">
          <span>Protected by JWT authentication</span>
          <p>
            Don't have an account?{" "}
            <button
              type="button"
              onClick={() => {
                window.location.href = "/signup";
              }}
            >
              Sign up
            </button>
          </p>
        </div>
      </div>
    </main>
  );
}

export default Login;