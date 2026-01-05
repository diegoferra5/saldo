import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <main className="text-center space-y-8 px-4">
        <div className="space-y-6">
          {/* Logo ícono grande */}
          <div className="flex justify-center">
            <Image
              src="/saldo-icon-light.svg"
              alt="Saldo"
              width={120}
              height={120}
              priority
              className="h-28 w-28"
            />
          </div>

          {/* Wordmark mediano */}
          <div className="flex justify-center">
            <Image
              src="/saldo-wordmark.svg"
              alt="Saldo"
              width={200}
              height={60}
              priority
              className="h-14 w-auto"
            />
          </div>

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
