"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { setToken } from "@/lib/auth";

// Helper para extraer mensajes de error de FastAPI
const getErrorMessage = (data: any, status: number): string => {
  const detail = data?.detail;

  // FastAPI a veces devuelve detail como string
  if (typeof detail === "string") return detail;

  // A veces devuelve un array de errores de validación
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;

  // Fallback genérico
  return data?.message || `Error (${status}) al iniciar sesión`;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Validar si el botón debe estar deshabilitado
  const isDisabled = isLoading || !email.trim() || password.length < 8;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Normalizar email
    const normalizedEmail = email.trim().toLowerCase();

    // Validación básica en cliente
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(normalizedEmail)) {
      setError("Email inválido");
      return;
    }

    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres");
      return;
    }

    // Llamada al backend
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: normalizedEmail,
          password,
        }),
      });

      // Parse seguro del JSON
      let data: any = null;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        // Error del backend (401, 400, 500, etc.)
        const errorMsg = getErrorMessage(data, response.status);
        setError(errorMsg);
        return;
      }

      // Login exitoso (status 200)
      console.log("Login exitoso:", data);

      // Validar y guardar token
      const token = data?.access_token;
      if (typeof token === "string" && token.length > 0) {
        setToken(token);
        // Redirigir a dashboard
        router.push("/dashboard");
      } else {
        // Token no válido
        console.error("Token no recibido del backend");
        setError("Error al iniciar sesión. Intenta de nuevo.");
      }
    } catch (err) {
      // Error de red o servidor no disponible
      setError("No se pudo conectar con el servidor. Verifica que el backend esté corriendo.");
      console.error("Error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <div className="w-full max-w-md p-8">
        {/* Botón volver */}
        <div className="mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/">
              ← Volver a inicio
            </Link>
          </Button>
        </div>

        {/* Logo pequeño */}
        <div className="mb-6 flex justify-center">
          <Link href="/">
            <Image
              src="/saldo-wordmark.svg"
              alt="Saldo"
              width={140}
              height={40}
              className="h-10 w-auto"
            />
          </Link>
        </div>

        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold">Iniciar sesión</h1>
          <p className="mt-2 text-muted-foreground">
            Accede a tu cuenta de Saldo
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Bienvenido de nuevo</CardTitle>
            <CardDescription>
              Ingresa tus credenciales para continuar
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="tu@email.com"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>

              {/* Password */}
              <div className="space-y-2">
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Tu contraseña"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>

              {/* Error message */}
              {error && (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              {/* Submit button */}
              <Button type="submit" className="w-full" disabled={isDisabled}>
                {isLoading ? "Iniciando sesión..." : "Iniciar sesión"}
              </Button>

              {/* Link to signup */}
              <div className="text-center text-sm text-muted-foreground">
                ¿No tienes cuenta?{" "}
                <Link href="/signup" className="font-medium text-foreground hover:underline">
                  Crear cuenta
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
