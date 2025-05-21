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
  RefreshCw,
  AlertTriangle,
} from "lucide-react"
import { fetchLatestAnalyses } from "@/lib/actions"
import dynamic from "next/dynamic"

// Lazy load child components
const CodeAnalysisDetails = dynamic(() => import("@/components/code-analysis-details"), {
  loading: () => <div className="animate-pulse h-64 bg-gray-700 rounded w-full"></div>,
  ssr: true,
});

const SecurityScanResults = dynamic(() => import("@/components/security-scan-results"), {
  loading: () => <div className="animate-pulse h-64 bg-gray-700 rounded w-full"></div>,
  ssr: true,
});

const KubernetesStatus = dynamic(() => import("@/components/kubernetes-status"), {
  loading: () => <div className="animate-pulse h-64 bg-gray-700 rounded w-full"></div>,
  ssr: true,
});

const SystemMetrics = dynamic(() => import("@/components/system-metrics"), {
  loading: () => <div className="animate-pulse h-64 bg-gray-700 rounded w-full"></div>,
  ssr: true,
});

export interface CodeAnalysis {
  id: string
  commitId: string
  repository: string
  branch: string
  timestamp: string
  status: "success" | "error" | "pending"
  feedback: string
  author?: string
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

function CodeAnalysisDashboard() {
  const [analyses, setAnalyses] = useState<CodeAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedAnalysis, setSelectedAnalysis] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("code")
  const [currentPage, setCurrentPage] = useState(1)
  const [refreshing, setRefreshing] = useState(false)
  const [rateLimitWarning, setRateLimitWarning] = useState<string | null>(null)
  const [lastRefreshTime, setLastRefreshTime] = useState<string>("")

  const ITEMS_PER_PAGE = 5

  // Filter: nur Commits NACH 2185016 anzeigen
  const referenceCommit = "2185016"
  const indexOfReference = analyses.findIndex((c) => c.commitId.startsWith(referenceCommit))
  const filteredAnalyses = indexOfReference > -1 ? analyses.slice(0, indexOfReference) : analyses

  const totalPages = Math.ceil(filteredAnalyses.length / ITEMS_PER_PAGE)
  const paginatedAnalyses = filteredAnalyses.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  const loadAnalyses = async (forceRefresh = false) => {
    try {
      if (refreshing) return;
      
      setRefreshing(true)
      const result = await fetchLatestAnalyses(forceRefresh)
      console.log("Data received by CodeAnalysisDashboard from fetchLatestAnalyses:", JSON.stringify(result.analyses, null, 2));
      setAnalyses(result.analyses)
      
      setRateLimitWarning(result.rateLimitInfo || null)
      
      if (result.analyses.length > 0 && !selectedAnalysis) {
        setSelectedAnalysis(result.analyses[0].id)
      }
      
      setLastRefreshTime(new Date().toLocaleTimeString())
    } catch (error) {
      console.error("Failed to load analyses:", error)
      setRateLimitWarning("Error refreshing data.")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadAnalyses(false) // Initial load without force refresh
    // Keine automatische Aktualisierung mehr
  }, [])

  const selectedAnalysisData = analyses.find((a) => a.id === selectedAnalysis) || null

  return (
    <div className="space-y-6">
      <Card className="border border-[#30363d] bg-[#161b22] shadow-sm rounded-md overflow-hidden">
        <CardHeader className="bg-[#0d1117] border-b border-[#30363d] px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-[#c9d1d9] text-base font-semibold">Neueste GitHub-Commits</CardTitle>
              {lastRefreshTime && (
                <p className="text-xs text-[#8b949e] mt-1">
                  Letztes Update: {lastRefreshTime}
                </p>
              )}
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => loadAnalyses(true)}
                disabled={refreshing}
                className="flex items-center gap-1 px-2 py-1 rounded text-xs bg-[#21262d] text-[#c9d1d9] hover:bg-[#30363d] transition-colors"
              >
                <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? 'Aktualisiere...' : 'Aktualisieren'}
              </button>
            </div>
          </div>
          
          {rateLimitWarning && (
            <div className="mt-2 text-xs text-amber-400 flex items-center">
              <AlertTriangle className="h-3 w-3 mr-1" />
              {rateLimitWarning}
            </div>
          )}
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="text-center">
                <div className="animate-spin h-8 w-8 border-4 border-[#58a6ff] border-t-transparent rounded-full mx-auto" />
                <p className="mt-2 text-sm text-[#8b949e]">Lade neueste Analysen...</p>
              </div>
            </div>
          ) : filteredAnalyses.length === 0 ? (
            <div className="text-center py-8 px-4">
              <GitMerge className="h-10 w-10 mx-auto text-[#8b949e]/60" />
              <h3 className="mt-4 text-lg font-medium text-[#c9d1d9]">Keine Commits gefunden</h3>
              <p className="mt-2 text-sm text-[#8b949e] max-w-md mx-auto">
                Pushe Code zu deinem GitHub-Repository, um automatisierte Analysen zu sehen 
                oder das GitHub API-Limit wurde erreicht. Bitte versuche es später erneut.
              </p>
            </div>
          ) : (
            <div>
              {paginatedAnalyses.map((analysis, index) => (
                <div
                  key={analysis.id}
                  className={`p-4 cursor-pointer transition-colors ${
                    selectedAnalysis === analysis.id ? "bg-[#0d1117]" : "hover:bg-[#0d1117]"
                  } ${index !== paginatedAnalyses.length - 1 ? "border-b border-[#30363d]" : ""}`}
                  onClick={() => setSelectedAnalysis(analysis.id)}
                >
                  <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[#0d1117] border border-[#30363d]">
                              <GitBranch className="h-4 w-4 text-[#8b949e]"/>
                          </div>
                          <div>
                              <a 
                                href={`https://github.com/${analysis.repository}/commit/${analysis.commitId}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-semibold text-[#c9d1d9] hover:underline"
                                onClick={(e) => e.stopPropagation()}
                              >
                                {analysis.feedback}
                              </a>
                              <p className="text-xs text-[#8b949e] mt-1">
                                  {analysis.repository}/{analysis.branch} •{" "}
                                  <span className="font-mono">{analysis.commitId.substring(0, 7)}</span>
                              </p>
                              <p className="text-xs text-[#8b949e]">
                                  {new Date(analysis.timestamp).toLocaleString()} •{" "}
                                  <span className="font-semibold text-[#58a6ff]">{analysis.author}</span>
                              </p>
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
                        (scan) => scan.status === "error" || scan.vulnerabilities.critical > 0 || scan.vulnerabilities.high > 0,
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

              {/* Pagination Buttons */}
              {totalPages > 1 && (
                <div className="flex justify-center gap-2 py-4">
                  {Array.from({ length: totalPages }, (_, i) => (
                    <button
                      key={i}
                      onClick={() => setCurrentPage(i + 1)}
                      className={`text-sm px-3 py-1 rounded ${
                        currentPage === i + 1
                          ? "bg-[#58a6ff] text-black font-semibold"
                          : "bg-[#21262d] text-[#8b949e]"
                      }`}
                    >
                      {i + 1}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analyse-Details */}
      {selectedAnalysisData && (
        <Card className="border border-[#30363d] bg-[#161b22] shadow-sm rounded-md overflow-hidden">
          <CardHeader className="bg-[#0d1117] border-b border-[#30363d] px-4 py-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-[#c9d1d9]">
              Analyse-Details
              <span className="text-xs font-normal text-[#8b949e] font-mono">
                Commit {selectedAnalysisData.commitId.substring(0, 7)}
              </span>
              {/* Truncate humorMessage in the header of Analyse-Details card and make it clickable */}
              {selectedAnalysisData.humorMessage && (
                <div 
                  className="ml-auto text-xs font-normal text-[#58a6ff] flex items-center overflow-hidden cursor-pointer hover:underline" 
                  style={{ maxWidth: '250px' }}
                  onClick={() => {
                    document.getElementById('full-humor-message-card')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                >
                  <Bot className="h-3.5 w-3.5 mr-1 flex-shrink-0" />
                  <span className="truncate"> 
                    {selectedAnalysisData.humorMessage}
                  </span>
                </div>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Tabs defaultValue="code" className="w-full" onValueChange={setActiveTab}>
              <TabsList className="w-full flex border-b border-[#30363d] bg-[#161b22]">
                <TabsTrigger
                  value="code"
                  className="flex-1 py-2 px-4 text-sm text-[#c9d1d9] data-[state=active]:text-[#58a6ff]"
                >
                  <FileCode className="h-4 w-4 mr-2" />
                  Code-Analyse
                </TabsTrigger>
                <TabsTrigger
                  value="security"
                  className="flex-1 py-2 px-4 text-sm text-[#c9d1d9] data-[state=active]:text-[#58a6ff]"
                >
                  <Shield className="h-4 w-4 mr-2" />
                  Sicherheits-Scans
                </TabsTrigger>
                <TabsTrigger
                  value="kubernetes"
                  className="flex-1 py-2 px-4 text-sm text-[#c9d1d9] data-[state=active]:text-[#58a6ff]"
                >
                  <Container className="h-4 w-4 mr-2" />
                  Kubernetes
                </TabsTrigger>
                <TabsTrigger
                  value="metrics"
                  className="flex-1 py-2 px-4 text-sm text-[#c9d1d9] data-[state=active]:text-[#58a6ff]"
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

      {/* New Dedicated Section for Full DeepSeek Message of Selected Commit */}
      {selectedAnalysisData && selectedAnalysisData.humorMessage && (
        <Card id="full-humor-message-card" className="mt-6 border border-[#30363d] bg-[#0d1117] shadow-sm rounded-md overflow-hidden">
          <CardHeader className="bg-[#161b22] border-b border-[#30363d] px-4 py-3">
            <CardTitle className="text-[#c9d1d9] text-base font-semibold flex items-center">
              <Bot className="h-5 w-5 mr-2 text-[#58a6ff]" /> KI-Generierte Analyse (DeepSeek)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <p className="text-[#c9d1d9] whitespace-pre-wrap">{selectedAnalysisData.humorMessage}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Default export for dynamic import compatibility
export default CodeAnalysisDashboard;
// Named export for direct imports
export { CodeAnalysisDashboard };
