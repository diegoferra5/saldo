import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <main className="text-center space-y-6">
        <h1 className="text-4xl font-bold">
          Saldo 💰
        </h1>
        <p className="text-lg text-muted-foreground">
          Personal finance control for Mexico
        </p>
        <div className="flex gap-4 justify-center">
          <Button>Get Started</Button>
          <Button variant="outline">Learn More</Button>
        </div>
      </main>
    </div>
  );
}
