import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <main className="text-center space-y-8 px-4">
        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tight">
            Saldo 💰
          </h1>
          <p className="text-xl text-muted-foreground max-w-md mx-auto">
            Decide mejor con tu dinero
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" asChild>
            <Link href="/signup">Crear cuenta</Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/login">Iniciar sesión</Link>
          </Button>
        </div>

        <p className="text-sm text-muted-foreground mt-8">
          Control financiero personal para México
        </p>
      </main>
    </div>
  );
}
