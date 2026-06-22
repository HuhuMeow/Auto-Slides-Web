import { FormEvent, useState } from "react";
import { Loader2, LogIn, UserPlus } from "lucide-react";
import { useAuthStore } from "../../store/authStore";

export function LoginForm() {
  const { login, register, loading, error } = useAuthStore();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLocalError(null);
    if (mode === "register") {
      if (password !== confirmPassword) {
        setLocalError("Passwords do not match");
        return;
      }
      await register(username, password);
      return;
    }
    await login(username, password);
  }

  return (
    <form autoComplete="off" onSubmit={onSubmit} className="w-full max-w-sm space-y-5 rounded-lg border bg-white p-6 shadow-subtle">
      <div>
        <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-md border bg-muted">
          {mode === "login" ? <LogIn className="h-5 w-5" /> : <UserPlus className="h-5 w-5" />}
        </div>
        <h1 className="text-xl font-semibold tracking-tight">{mode === "login" ? "Sign in to Auto-Slides" : "Create an account"}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {mode === "login" ? "Use your account to manage conversion tasks." : "No password recovery is available."}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2 rounded-md bg-muted p-1">
        <button
          className={`h-8 rounded text-sm ${mode === "login" ? "bg-white font-medium shadow-sm" : "text-slate-600"}`}
          onClick={() => setMode("login")}
          type="button"
        >
          Sign in
        </button>
        <button
          className={`h-8 rounded text-sm ${mode === "register" ? "bg-white font-medium shadow-sm" : "text-slate-600"}`}
          onClick={() => setMode("register")}
          type="button"
        >
          Register
        </button>
      </div>

      <label className="block space-y-2">
        <span className="text-sm font-medium">Username</span>
        <input
          className="h-10 w-full rounded-md border px-3 text-sm outline-none focus:border-slate-400"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="off"
        />
      </label>

      <label className="block space-y-2">
        <span className="text-sm font-medium">Password</span>
        <input
          className="h-10 w-full rounded-md border px-3 text-sm outline-none focus:border-slate-400"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="new-password"
        />
      </label>

      {mode === "register" ? (
        <label className="block space-y-2">
          <span className="text-sm font-medium">Confirm password</span>
          <input
            className="h-10 w-full rounded-md border px-3 text-sm outline-none focus:border-slate-400"
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            autoComplete="new-password"
          />
        </label>
      ) : null}

      {localError || error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{localError || error}</div> : null}

      <button
        className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
        disabled={loading}
        type="submit"
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : mode === "login" ? <LogIn className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}
        {mode === "login" ? "Sign in" : "Create account"}
      </button>
    </form>
  );
}
