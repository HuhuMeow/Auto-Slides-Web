import { Navigate } from "react-router-dom";
import { LoginForm } from "../components/auth/LoginForm";
import { useAuthStore } from "../store/authStore";

export function LoginPage() {
  const user = useAuthStore((state) => state.user);

  if (user) return <Navigate to="/" replace />;

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f7f7f8] p-4">
      <LoginForm />
    </div>
  );
}
