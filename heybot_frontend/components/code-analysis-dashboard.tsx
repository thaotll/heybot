"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  AlertCircle,
  CheckCircle,
  Clock,
  GitMerge,
  GitBranch,
  Shield,
  FileCode,
  Server,
  Container,
  Bot,
} from "lucide-react"
import { fetchLatestAnalyses } from "@/lib/actions"
import { CodeAnalysisDetails } from "@/components/code-analysis-details"
import { SecurityScanResults } from "@/components/security-scan-results"
import { KubernetesStatus } from "@/components/kubernetes-status"
import { SystemMetrics } from "@/components/system-metrics"

export interface CodeAnalysis {
  id: string
  commitId: string
  repository: string
  branch: string
  timestamp: string
  status: "success" | "error" | "pending"
  feedback: string
  issues: {
    type: "warning" | "error" | "info"
    message: string
    file?: string
    line?: number
  }[]
  files: {
    name: string
    status: "success" | "error" | "warning"
    issues: number
  }[]
  securityScans: {
    tool: "trivy" | "owasp" | "renovate"
    status: "success" | "error" | "warning"
    vulnerabilities: {
      critical: number
      high: number
      medium: number
      low: number
    }
    details: string
  }[]
  kubernetesStatus: {
    pods: {
      total: number
      running: number
      pending: number
      failed: number
    }
    deployments: {
      total: number
      available: number
      unavailable: number
    }
    services: number
  }
  memeUrl?: string
  humorMessage?: string
}

export function CodeAnalysisDashboard() {
  const [analyses, setAnalyses] = useState<CodeAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedAnalysis, setSelectedAnalysis] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("code")

  useEffect(() => {
    const loadAnalyses = async () => {
      try {
        const data = await fetchLatestAnalyses()
        setAnalyses(data)
        if (data.length > 0) {
          setSelectedAnalysis(data[0].id)
        }
      } catch (error) {
        console.error("Failed to load analyses:", error)
      } finally {
        setLoading(false)
      }
    }

    loadAnalyses()

    // Set up polling to check for new analyses every 30 seconds
    const interval = setInterval(loadAnalyses, 30000)
    return () => clearInterval(interval)
  }, [])

  const selectedAnalysisData = analyses.find((a) => a.id === selectedAnalysis) || null

  return (
    <div className="space-y-6">
      <Card className="border border-[#30363d] bg-[#161b22] shadow-sm rounded-md overflow-hidden">
        <CardHeader className="bg-[#0d1117] border-b border-[#30363d] px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-[#c9d1d9] text-base font-semibold">Neueste GitLab-Commits</CardTitle>
            </div>
            <div className="flex items-center gap-2 text-xs text-[#8b949e]">
              <Clock className="h-3 w-3" />
              <span>Auto-Aktualisierung alle 30 Sekunden</span>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="text-center">
                <div className="animate-spin h-8 w-8 border-4 border-[#58a6ff] border-t-transparent rounded-full mx-auto"></div>
                <p className="mt-2 text-sm text-[#8b949e]">Lade neueste Analysen...</p>
              </div>
            </div>
          ) : analyses.length === 0 ? (
            <div className="text-center py-8 px-4">
              <GitMerge className="h-10 w-10 mx-auto text-[#8b949e]/60" />
              <h3 className="mt-4 text-lg font-medium text-[#c9d1d9]">Keine Commits gefunden</h3>
              <p className="mt-2 text-sm text-[#8b949e] max-w-md mx-auto">
                Pushe Code zu deinem GitLab-Repository, um automatisierte Analysen zu sehen.
              </p>
            </div>
          ) : (
            <div>
              {analyses.map((analysis, index) => (
                <div
                  key={analysis.id}
                  className={`p-4 cursor-pointer transition-colors ${
                    selectedAnalysis === analysis.id ? "bg-[#0d1117]" : "hover:bg-[#0d1117]"
                  } ${index !== analyses.length - 1 ? "border-b border-[#30363d]" : ""}`}
                  onClick={() => setSelectedAnalysis(analysis.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[#0d1117] border border-[#30363d]">
                        <GitBranch className="h-4 w-4 text-[#8b949e]" />
                      </div>
                      <div>
                        <h3 className="font-medium text-[#c9d1d9] flex items-center gap-2">
                          {analysis.repository}/{analysis.branch}{" "}
                          <span className="text-xs text-[#8b949e] font-mono">{analysis.commitId.substring(0, 7)}</span>
                        </h3>
                        <p className="text-xs text-[#8b949e]">{new Date(analysis.timestamp).toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          analysis.status === "success"
                            ? "success"
                            : analysis.status === "error"
                              ? "destructive"
                              : "outline"
                        }
                        className="flex items-center gap-1"
                      >
                        {analysis.status === "success" ? (
                          <CheckCircle className="h-3 w-3" />
                        ) : analysis.status === "error" ? (
                          <AlertCircle className="h-3 w-3" />
                        ) : (
                          <Clock className="h-3 w-3" />
                        )}
                        {analysis.status === "success"
                          ? "Bestanden"
                          : analysis.status === "error"
                            ? "Probleme gefunden"
                            : "Analysiere"}
                      </Badge>

                      {/* Security Badge */}
                      {analysis.securityScans.some(
                        (scan) => scan.vulnerabilities.critical > 0 || scan.vulnerabilities.high > 0,
                      ) ? (
                        <Badge variant="destructive" className="flex items-center gap-1">
                          <Shield className="h-3 w-3" />
                          Sicherheitsprobleme
                        </Badge>
                      ) : (
                        <Badge variant="success" className="flex items-center gap-1">
                          <Shield className="h-3 w-3" />
                          Sicher
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedAnalysisData && (
        <Card className="border border-[#30363d] bg-[#161b22] shadow-sm rounded-md overflow-hidden">
          <CardHeader className="bg-[#0d1117] border-b border-[#30363d] px-4 py-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-[#c9d1d9]">
              Analyse-Details
              <span className="text-xs font-normal text-[#8b949e] font-mono">
                Commit {selectedAnalysisData.commitId.substring(0, 7)}
              </span>
              {/* Humor Message */}
              {selectedAnalysisData.humorMessage && (
                <span className="ml-auto text-xs font-normal text-[#58a6ff] flex items-center">
                  <Bot className="h-3.5 w-3.5 mr-1" />
                  {selectedAnalysisData.humorMessage}
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Tabs defaultValue="code" className="w-full" onValueChange={setActiveTab}>
              <TabsList className="w-full flex border-b border-[#30363d] bg-[#161b22]">
                <TabsTrigger
                  value="code"
                  className="flex-1 py-2 px-4 text-sm text-[#c9d1d9] data-[state=active]:border-b-2 data-[state=active]:border-[#58a6ff] data-[state=active]:text-[#58a6ff] rounded-none"
                >
                  <FileCode className="h-4 w-4 mr-2" />
                  Code-Analyse
                </TabsTrigger>
                <TabsTrigger
                  value="security"
                  className="flex-1 py-2 px-4 text-sm text-[#c9d1d9] data-[state=active]:border-b-2 data-[state=active]:border-[#58a6ff] data-[state=active]:text-[#58a6ff] rounded-none"
                >
                  <Shield className="h-4 w-4 mr-2" />
                  Sicherheits-Scans
                </TabsTrigger>
                <TabsTrigger
                  value="kubernetes"
                  className="flex-1 py-2 px-4 text-sm text-[#c9d1d9] data-[state=active]:border-b-2 data-[state=active]:border-[#58a6ff] data-[state=active]:text-[#58a6ff] rounded-none"
                >
                  <Container className="h-4 w-4 mr-2" />
                  Kubernetes
                </TabsTrigger>
                <TabsTrigger
                  value="metrics"
                  className="flex-1 py-2 px-4 text-sm text-[#c9d1d9] data-[state=active]:border-b-2 data-[state=active]:border-[#58a6ff] data-[state=active]:text-[#58a6ff] rounded-none"
                >
                  <Server className="h-4 w-4 mr-2" />
                  System-Metriken
                </TabsTrigger>
              </TabsList>

              <TabsContent value="code">
                <CodeAnalysisDetails analysis={selectedAnalysisData} />
              </TabsContent>

              <TabsContent value="security">
                <SecurityScanResults analysis={selectedAnalysisData} />
              </TabsContent>

              <TabsContent value="kubernetes">
                <KubernetesStatus analysis={selectedAnalysisData} />
              </TabsContent>

              <TabsContent value="metrics">
                <SystemMetrics analysis={selectedAnalysisData} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
