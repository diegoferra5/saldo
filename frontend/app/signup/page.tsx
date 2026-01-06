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
  return data?.message || `Error (${status}) al crear la cuenta`;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Validar si el botón debe estar deshabilitado
  const isDisabled =
    isLoading ||
    !email.trim() ||
    password.length < 8 ||
    confirmPassword.length < 8 ||
    password !== confirmPassword;

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

    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }

    // Llamada al backend
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: normalizedEmail,
          password,
          full_name: fullName || undefined, // Solo envía si hay valor
        }),
      });

      // Parse seguro del JSON (puede fallar si el backend responde HTML o vacío)
      let data: any = null;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        // Error del backend (400, 500, etc.)
        const errorMsg = getErrorMessage(data, response.status);
        setError(errorMsg);
        return;
      }

      // Registro exitoso (status 201)
      console.log("Usuario registrado:", data);

      // Validar y guardar token
      const token = data?.access_token;
      if (typeof token === "string" && token.length > 0) {
        setToken(token);
        // Redirigir a dashboard
        router.push("/dashboard");
      } else {
        // Token no válido, redirigir a login
        console.warn("Token no recibido del backend, redirigiendo a login");
        setError("Cuenta creada. Por favor inicia sesión.");
        setTimeout(() => router.push("/login"), 2000);
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
          <h1 className="text-3xl font-bold">Crear cuenta</h1>
          <p className="mt-2 text-muted-foreground">
            Decide mejor con tu dinero
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Registro</CardTitle>
            <CardDescription>
              Ingresa tus datos para crear una cuenta
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full Name */}
              <div className="space-y-2">
                <Label htmlFor="fullName">¿Cómo te debemos llamar?</Label>
                <Input
                  id="fullName"
                  type="text"
                  placeholder="Tu nombre"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={isLoading}
                />
                <p className="text-xs text-muted-foreground">Opcional</p>
              </div>

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
                  placeholder="Mínimo 8 caracteres"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>

              {/* Confirm Password */}
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirmar contraseña</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Repite tu contraseña"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
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
                {isLoading ? "Creando cuenta..." : "Crear cuenta"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
