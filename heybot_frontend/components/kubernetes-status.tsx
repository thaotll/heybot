import { CheckCircle, AlertCircle, Container, Server } from "lucide-react"
import type { CodeAnalysis } from "./code-analysis-dashboard"

interface KubernetesStatusProps {
  analysis: CodeAnalysis
}

export function KubernetesStatus({ analysis }: KubernetesStatusProps) {
  const { pods, deployments, services } = analysis.kubernetesStatus
  const allPodsRunning = pods.running === pods.total
  const allDeploymentsAvailable = deployments.available === deployments.total

  return (
    <div className="p-4 space-y-4">
      <div className="p-4 rounded-md bg-[#0d1117] border border-[#30363d]">
        <div className="flex items-start gap-3">
          {allPodsRunning && allDeploymentsAvailable ? (
            <CheckCircle className="h-5 w-5 text-[#3fb950] mt-0.5" />
          ) : (
            <AlertCircle className="h-5 w-5 text-[#f85149] mt-0.5" />
          )}
          <div>
            <h3 className="font-medium text-[#c9d1d9]">
              {allPodsRunning && allDeploymentsAvailable
                ? "Kubernetes-Cluster läuft optimal"
                : "Probleme im Kubernetes-Cluster erkannt"}
            </h3>
            <p className="text-[#8b949e] mt-1">
              {allPodsRunning && allDeploymentsAvailable
                ? "Alle Pods und Deployments sind verfügbar und laufen wie erwartet."
                : "Einige Pods oder Deployments sind nicht verfügbar. Überprüfen Sie die Details unten."}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="flex flex-col items-center">
            <Container className="h-8 w-8 text-[#58a6ff] mb-2" />
            <div className="text-2xl font-bold text-[#c9d1d9]">
              {pods.running}/{pods.total}
            </div>
            <p className="text-xs text-[#8b949e] mt-1">Pods laufen</p>
            {pods.failed > 0 && <span className="mt-2 text-xs text-[#f85149]">{pods.failed} fehlgeschlagen</span>}
            {pods.pending > 0 && <span className="mt-2 text-xs text-[#d29922]">{pods.pending} ausstehend</span>}
          </div>
        </div>
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="flex flex-col items-center">
            <Server className="h-8 w-8 text-[#58a6ff] mb-2" />
            <div className="text-2xl font-bold text-[#c9d1d9]">
              {deployments.available}/{deployments.total}
            </div>
            <p className="text-xs text-[#8b949e] mt-1">Deployments verfügbar</p>
            {deployments.unavailable > 0 && (
              <span className="mt-2 text-xs text-[#f85149]">{deployments.unavailable} nicht verfügbar</span>
            )}
          </div>
        </div>
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="flex flex-col items-center">
            <svg
              className="h-8 w-8 text-[#58a6ff] mb-2"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path d="M2 12H22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path
                d="M12 2C14.5013 4.73835 15.9228 8.29203 16 12C15.9228 15.708 14.5013 19.2616 12 22C9.49872 19.2616 8.07725 15.708 8 12C8.07725 8.29203 9.49872 4.73835 12 2Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div className="text-2xl font-bold text-[#c9d1d9]">{services}</div>
            <p className="text-xs text-[#8b949e] mt-1">Services aktiv</p>
          </div>
        </div>
      </div>

      <h3 className="text-[#c9d1d9] font-medium mt-2">Cluster-Details</h3>
      <div className="border border-[#30363d] rounded-md overflow-hidden">
        <div className="bg-[#0d1117] p-3 border-b border-[#30363d]">
          <span className="font-medium text-[#c9d1d9]">Ressourcenübersicht</span>
        </div>
        <div className="p-4">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-[#8b949e]">Pod-Status</span>
                <span className="text-sm text-[#c9d1d9]">
                  {pods.running}/{pods.total} laufen
                </span>
              </div>
              <div className="w-full bg-[#0d1117] rounded-full h-2.5">
                <div
                  className="bg-[#3fb950] h-2.5 rounded-full"
                  style={{ width: `${(pods.running / pods.total) * 100}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-[#8b949e]">Deployment-Status</span>
                <span className="text-sm text-[#c9d1d9]">
                  {deployments.available}/{deployments.total} verfügbar
                </span>
              </div>
              <div className="w-full bg-[#0d1117] rounded-full h-2.5">
                <div
                  className="bg-[#3fb950] h-2.5 rounded-full"
                  style={{ width: `${(deployments.available / deployments.total) * 100}%` }}
                ></div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d]">
                <div className="text-xs text-[#8b949e] mb-1">Namespace</div>
                <div className="text-sm text-[#c9d1d9] font-mono">default</div>
              </div>
              <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d]">
                <div className="text-xs text-[#8b949e] mb-1">Kubernetes-Version</div>
                <div className="text-sm text-[#c9d1d9] font-mono">v1.26.1</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
