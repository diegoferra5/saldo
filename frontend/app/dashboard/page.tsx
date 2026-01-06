"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, clearToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface User {
  id: string;
  email: string;
  full_name: string | null;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const validateToken = async () => {
      const token = getToken();

      // Si no hay token, redirigir a login
      if (!token) {
        router.push("/login");
        return;
      }

      // Validar token con el backend
      try {
        const response = await fetch(`${API_URL}/api/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        });

        // Si 401/403, token inválido
        if (response.status === 401 || response.status === 403) {
          clearToken();
          router.push("/login");
          return;
        }

        if (!response.ok) {
          throw new Error("Failed to fetch user");
        }

        const userData = await response.json();
        setUser(userData);
      } catch (error) {
        // Si fue abortado, no hacer nada (componente desmontado)
        if ((error as any)?.name === "AbortError") return;

        console.error("Error validating token:", error);

        // Detectar error de red de forma más robusta
        const msg = String((error as any)?.message || "");
        const isNetworkError =
          error instanceof TypeError ||
          msg.includes("Failed to fetch") ||
          msg.includes("NetworkError");

        // Si es error de red (backend offline), no borrar token
        if (isNetworkError) {
          console.warn("Backend no disponible, intenta de nuevo más tarde");
          setError("No se pudo conectar con el servidor. Verifica tu conexión.");
          return;
        }

        // Otros errores: token inválido
        clearToken();
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    validateToken();

    return () => controller.abort();
  }, [router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <p className="text-muted-foreground">Cargando...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="text-center">
          <p className="text-destructive">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 text-sm text-muted-foreground hover:underline"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <div className="p-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        {user && (
          <p className="mt-4 text-muted-foreground">
            Bienvenido, {user.full_name || user.email}
          </p>
        )}
      </div>
    </div>
  );
}
