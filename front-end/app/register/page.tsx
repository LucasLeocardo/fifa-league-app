import Link from "next/link";
import { AuthShell } from "@/components/auth/AuthShell";
import { RegisterForm } from "@/components/auth/RegisterForm";

export default function RegisterPage() {
  return (
    <AuthShell
      title="Sign up"
      subtitle="Crie sua conta e entre em campo na FIFA League."
      footer={
        <>
          Já joga aqui?{" "}
          <Link href="/login" className="text-[var(--lime)] transition-opacity hover:opacity-80">
            Fazer login
          </Link>
        </>
      }
    >
      <RegisterForm />
    </AuthShell>
  );
}
