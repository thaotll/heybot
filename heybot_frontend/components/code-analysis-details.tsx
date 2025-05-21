import { AlertCircle, AlertTriangle, Info, FileCode, CheckCircle, Clock } from "lucide-react"
import type { CodeAnalysis } from "./code-analysis-dashboard"

interface CodeAnalysisDetailsProps {
  analysis: CodeAnalysis
}

function CodeAnalysisDetailsComponent({ analysis }: CodeAnalysisDetailsProps) {
  // Display meme if there are issues and a meme URL is available
  const showMeme = analysis.issues.length > 0 && analysis.memeUrl

  return (
    <div className="p-4 space-y-4">
      <div className="p-4 rounded-md bg-[#0d1117] border border-[#30363d]">
        <div className="flex items-start gap-3">
          {analysis.status === "success" ? (
            <CheckCircle className="h-5 w-5 text-[#3fb950] mt-0.5" />
          ) : (
            <AlertCircle className="h-5 w-5 text-[#f85149] mt-0.5" />
          )}
          <div className="flex-1">
            {/* The above section displaying humorMessage is now commented out */}
            {/* We can add other details here later if needed, like commit author and timestamp if not elsewhere */}
            {/* Removed old commit, author, date paragraphs */}

            {analysis.status === 'error' && (
              <div className="flex items-start gap-3">
                <div>
                  <h3 className="font-semibold text-lg text-[#c9d1d9]">Probleme erkannt</h3>
                  <p className="text-sm text-[#8b949e] mt-1">
                    Mehrere Sicherheitsprobleme und Code-Qualitätsprobleme gefunden. Bitte überprüfen Sie die Details unten.
                  </p>
                </div>
              </div>
            )}
            {analysis.status === 'success' && (
              <div className="flex items-start gap-3">
                <CheckCircle className="h-6 w-6 text-[#3fb950] mt-0.5" />
                <div>
                  <h3 className="font-semibold text-lg text-[#c9d1d9]">Code-Analyse bestanden</h3>
                  <p className="text-sm text-[#8b949e] mt-1">
                    Code-Analyse erfolgreich abgeschlossen. Keine kritischen Probleme gefunden.
                  </p>
                </div>
              </div>
            )}
            {analysis.status === 'pending' && (
              <div className="flex items-start gap-3">
                <Clock className="h-6 w-6 text-[#8b949e] mt-0.5" />
                <div>
                  <h3 className="font-semibold text-lg text-[#c9d1d9]">Analyse ausstehend</h3>
                  <p className="text-sm text-[#8b949e] mt-1">
                    Die Code-Analyse für diesen Commit wird derzeit durchgeführt oder die Daten sind noch nicht verfügbar.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Meme display for humor component */}
          {showMeme && (
            <div className="ml-4 flex-shrink-0">
              <img
                src={analysis.memeUrl || "/placeholder.svg"}
                alt="Humor-Reaktion"
                className="w-32 h-32 object-cover rounded-md border border-[#30363d]"
              />
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-[#c9d1d9]">{analysis.files.length}</div>
            <p className="text-xs text-[#8b949e] mt-1">Analysierte Dateien</p>
          </div>
        </div>
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-[#c9d1d9]">{analysis.issues.length}</div>
            <p className="text-xs text-[#8b949e] mt-1">Gefundene Probleme</p>
          </div>
        </div>
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-[#3fb950]">
              {analysis.files.filter((f) => f.status === "success").length}
            </div>
            <p className="text-xs text-[#8b949e] mt-1">Erfolgreiche Dateien</p>
          </div>
        </div>
      </div>

      <h3 className="text-[#c9d1d9] font-medium mt-2">Probleme</h3>
      {analysis.issues.length === 0 ? (
        <div className="text-center py-6 border border-[#30363d] rounded-md bg-[#0d1117]">
          <CheckCircle className="h-8 w-8 mx-auto text-[#3fb950]" />
          <h3 className="mt-3 font-medium text-[#c9d1d9]">Keine Probleme gefunden</h3>
          <p className="mt-1 text-sm text-[#8b949e]">Dein Code hat alle Prüfungen bestanden. Gut gemacht!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {analysis.issues.map((issue, index) => (
            <div key={index} className="p-4 rounded-md border border-[#30363d] bg-[#0d1117]">
              <div className="flex items-start gap-3">
                {issue.type === "error" ? (
                  <AlertCircle className="h-5 w-5 text-[#f85149] mt-0.5" />
                ) : issue.type === "warning" ? (
                  <AlertCircle className="h-5 w-5 text-[#d29922] mt-0.5" />
                ) : (
                  <Info className="h-5 w-5 text-[#58a6ff] mt-0.5" />
                )}
                <div className="space-y-1">
                  <p className="text-[#c9d1d9]">{issue.message}</p>
                  {issue.file && (
                    <div className="flex items-center gap-1 text-xs text-[#8b949e] font-mono">
                      <FileCode className="h-3.5 w-3.5" />
                      <span>
                        {issue.file}
                        {issue.line ? `:${issue.line}` : ""}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <h3 className="text-[#c9d1d9] font-medium mt-2">Dateien</h3>
      <div className="space-y-2">
        {analysis.files.map((file, index) => (
          <div
            key={index}
            className="p-3 rounded-md border border-[#30363d] bg-[#0d1117] flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <FileCode className="h-4 w-4 text-[#8b949e]" />
              <span className="text-sm text-[#c9d1d9] font-mono">{file.name}</span>
            </div>
            <div className="flex items-center gap-3">
              {file.issues > 0 && (
                <span className="text-xs text-[#8b949e]">
                  {file.issues} Problem{file.issues !== 1 ? "e" : ""}
                </span>
              )}
              {file.status === "success" ? (
                <CheckCircle className="h-4 w-4 text-[#3fb950]" />
              ) : file.status === "error" ? (
                <AlertCircle className="h-4 w-4 text-[#f85149]" />
              ) : (
                <AlertCircle className="h-4 w-4 text-[#d29922]" />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Export both ways
export default CodeAnalysisDetailsComponent;
export { CodeAnalysisDetailsComponent as CodeAnalysisDetails };
