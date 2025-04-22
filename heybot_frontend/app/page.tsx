import dynamic from "next/dynamic"

// Lazy load the CodeAnalysisDashboard component
const CodeAnalysisDashboard = dynamic(
  () => import("@/components/code-analysis-dashboard"),
  {
    loading: () => (
      <div className="animate-pulse flex flex-col gap-4 w-full">
        <div className="h-8 bg-gray-700 rounded w-1/3"></div>
        <div className="h-64 bg-gray-700 rounded w-full"></div>
        <div className="h-32 bg-gray-700 rounded w-full"></div>
      </div>
    ),
  }
)

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
