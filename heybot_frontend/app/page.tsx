import { CodeAnalysisDashboard } from "@/components/code-analysis-dashboard"

export default function Home() {
  return (
    <main className="min-h-screen bg-[#0d1117] text-[#c9d1d9]">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-[#c9d1d9]">KI-gestützte DevOps-Sicherheitsanalyse</h1>
          <p className="text-[#8b949e] mt-1">
            Automatisierte Code-Analyse und Sicherheitsprüfung mit Deepseek, Trivy und OWASP
          </p>
        </header>
        <CodeAnalysisDashboard />
      </div>
    </main>
  )
}
