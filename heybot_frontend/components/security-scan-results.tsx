import { AlertCircle, CheckCircle, Shield } from "lucide-react"
import type { CodeAnalysis } from "./code-analysis-dashboard"

interface SecurityScanResultsProps {
  analysis: CodeAnalysis
}

export function SecurityScanResults({ analysis }: SecurityScanResultsProps) {
  // Calculate total vulnerabilities
  const totalVulnerabilities = analysis.securityScans.reduce(
    (acc, scan) => {
      acc.critical += scan.vulnerabilities.critical
      acc.high += scan.vulnerabilities.high
      acc.medium += scan.vulnerabilities.medium
      acc.low += scan.vulnerabilities.low
      return acc
    },
    { critical: 0, high: 0, medium: 0, low: 0 },
  )

  const hasCriticalIssues = totalVulnerabilities.critical > 0 || totalVulnerabilities.high > 0

  return (
    <div className="p-4 space-y-4">
      <div className="p-4 rounded-md bg-[#0d1117] border border-[#30363d]">
        <div className="flex items-start gap-3">
          {!hasCriticalIssues ? (
            <CheckCircle className="h-5 w-5 text-[#3fb950] mt-0.5" />
          ) : (
            <AlertCircle className="h-5 w-5 text-[#f85149] mt-0.5" />
          )}
          <div>
            <h3 className="font-medium text-[#c9d1d9]">
              {!hasCriticalIssues ? "Sicherheits-Scans bestanden" : "Sicherheitsprobleme erkannt"}
            </h3>
            <p className="text-[#8b949e] mt-1">
              {!hasCriticalIssues
                ? "Keine kritischen Sicherheitsprobleme gefunden."
                : "Kritische Sicherheitsprobleme wurden erkannt. Bitte beheben Sie diese Probleme vor dem Deployment."}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div
              className={`text-2xl font-bold ${totalVulnerabilities.critical > 0 ? "text-[#f85149]" : "text-[#c9d1d9]"}`}
            >
              {totalVulnerabilities.critical}
            </div>
            <p className="text-xs text-[#8b949e] mt-1">Kritisch</p>
          </div>
        </div>
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div
              className={`text-2xl font-bold ${totalVulnerabilities.high > 0 ? "text-[#f85149]" : "text-[#c9d1d9]"}`}
            >
              {totalVulnerabilities.high}
            </div>
            <p className="text-xs text-[#8b949e] mt-1">Hoch</p>
          </div>
        </div>
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div
              className={`text-2xl font-bold ${totalVulnerabilities.medium > 0 ? "text-[#d29922]" : "text-[#c9d1d9]"}`}
            >
              {totalVulnerabilities.medium}
            </div>
            <p className="text-xs text-[#8b949e] mt-1">Mittel</p>
          </div>
        </div>
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-[#c9d1d9]">{totalVulnerabilities.low}</div>
            <p className="text-xs text-[#8b949e] mt-1">Niedrig</p>
          </div>
        </div>
      </div>

      <h3 className="text-[#c9d1d9] font-medium mt-2">Scan-Ergebnisse</h3>
      <div className="space-y-4">
        {analysis.securityScans.map((scan, index) => (
          <div key={index} className="border border-[#30363d] rounded-md overflow-hidden">
            <div className="bg-[#0d1117] p-3 border-b border-[#30363d] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-[#8b949e]" />
                <span className="font-medium text-[#c9d1d9]">
                  {scan.tool === "trivy" ? "Trivy" : scan.tool === "owasp" ? "OWASP Dependency Check" : "Renovate"}
                </span>
              </div>
              <div>
                {scan.status === "success" ? (
                  <span className="px-2 py-1 text-xs rounded-full bg-[#3fb950]/20 text-[#3fb950] border border-[#3fb950]/30">
                    Bestanden
                  </span>
                ) : scan.status === "warning" ? (
                  <span className="px-2 py-1 text-xs rounded-full bg-[#d29922]/20 text-[#d29922] border border-[#d29922]/30">
                    Warnungen
                  </span>
                ) : (
                  <span className="px-2 py-1 text-xs rounded-full bg-[#f85149]/20 text-[#f85149] border border-[#f85149]/30">
                    Fehler
                  </span>
                )}
              </div>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-4 gap-3 mb-4">
                <div className="text-center p-2 rounded-md bg-[#0d1117] border border-[#30363d]">
                  <div
                    className={`text-lg font-bold ${scan.vulnerabilities.critical > 0 ? "text-[#f85149]" : "text-[#c9d1d9]"}`}
                  >
                    {scan.vulnerabilities.critical}
                  </div>
                  <p className="text-xs text-[#8b949e]">Kritisch</p>
                </div>
                <div className="text-center p-2 rounded-md bg-[#0d1117] border border-[#30363d]">
                  <div
                    className={`text-lg font-bold ${scan.vulnerabilities.high > 0 ? "text-[#f85149]" : "text-[#c9d1d9]"}`}
                  >
                    {scan.vulnerabilities.high}
                  </div>
                  <p className="text-xs text-[#8b949e]">Hoch</p>
                </div>
                <div className="text-center p-2 rounded-md bg-[#0d1117] border border-[#30363d]">
                  <div
                    className={`text-lg font-bold ${scan.vulnerabilities.medium > 0 ? "text-[#d29922]" : "text-[#c9d1d9]"}`}
                  >
                    {scan.vulnerabilities.medium}
                  </div>
                  <p className="text-xs text-[#8b949e]">Mittel</p>
                </div>
                <div className="text-center p-2 rounded-md bg-[#0d1117] border border-[#30363d]">
                  <div className="text-lg font-bold text-[#c9d1d9]">{scan.vulnerabilities.low}</div>
                  <p className="text-xs text-[#8b949e]">Niedrig</p>
                </div>
              </div>
              <p className="text-sm text-[#8b949e]">{scan.details}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
