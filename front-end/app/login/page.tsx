import Link from "next/link";
import { AuthShell } from "@/components/auth/AuthShell";
import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <AuthShell
      title="Entrar"
      subtitle="Acesse sua conta e continue a temporada."
      footer={
        <>
          Novo na liga?{" "}
          <Link href="/register" className="text-[var(--lime)] transition-opacity hover:opacity-80">
            Criar conta
          </Link>
        </>
      }
    >
      <LoginForm />
    </AuthShell>
  );
}
