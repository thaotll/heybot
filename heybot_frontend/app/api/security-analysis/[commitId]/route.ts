import { NextResponse } from "next/server"
import fs from "fs"
import path from "path"

// Festgelegter Pfad für die Analysedateien
const ANALYSIS_PATH = "/Users/thaostein/heybot/app/analysis"

export async function GET(
  request: Request,
  { params }: { params: { commitId: string } }
) {
  const commitId = params.commitId
  const url = new URL(request.url)
  const format = url.searchParams.get('format')
  
  try {
    // Bei format=detailed geben wir die Rohdaten zurück
    if (format === 'detailed') {
      // Pfade zu den Dateien
      const trivyPath = path.join(ANALYSIS_PATH, `trivy-${commitId}.json`)
      const owaspPath = path.join(ANALYSIS_PATH, `owasp-${commitId}.json`)
      
      // Standardwerte
      let trivyData = { Results: [] }
      let owaspData = { dependencies: [] }
      
      // Lade Trivy-Daten, wenn vorhanden
      if (fs.existsSync(trivyPath)) {
        try {
          trivyData = JSON.parse(fs.readFileSync(trivyPath, "utf-8"))
          console.log(`Loaded Trivy data from ${trivyPath}`)
        } catch (e) {
          console.error(`Error loading Trivy data: ${e}`)
        }
      } else {
        console.warn(`No Trivy data found for commit ${commitId}`)
      }
      
      // Ladet OWASP-Daten, wenn vorhanden
      if (fs.existsSync(owaspPath)) {
        try {
          owaspData = JSON.parse(fs.readFileSync(owaspPath, "utf-8"))
          console.log(`Loaded OWASP data from ${owaspPath}`)
        } catch (e) {
          console.error(`Error loading OWASP data: ${e}`)
        }
      } else {
        console.warn(`No OWASP data found for commit ${commitId}`)
      }
      
      // Rückgabe der Daten im erwarteten Format
      return NextResponse.json({
        trivy: trivyData,
        owasp: owaspData
      })
    }
    
    // Standardfall: Zusammengefasste Analyse zurückgeben
    const filePath = path.join(ANALYSIS_PATH, `${commitId}.json`)
    
    // Prüft ob die Datei existiert
    if (!fs.existsSync(filePath)) {
      // Versucht es mit Trivy-Datei
      const trivyPath = path.join(ANALYSIS_PATH, `trivy-${commitId}.json`)
      if (!fs.existsSync(trivyPath)) {
        return NextResponse.json(
          { error: `Keine Analysedaten für Commit ${commitId} gefunden.` },
          { status: 404 }
        )
      }
      
      const trivyData = JSON.parse(fs.readFileSync(trivyPath, "utf-8"))
      
      // Erstellt ein leeres Analyse-Objekt mit Trivy-Daten
      const data = {
        securityScans: [
          {
            tool: "trivy",
            status: "success",
            vulnerabilities: summarizeVulnerabilities(trivyData.Results),
            details: "Ergebnisse des Trivy-Scans."
          },
          {
            tool: "owasp",
            status: "success",
            vulnerabilities: { critical: 0, high: 0, medium: 0, low: 0 },
            details: "Keine OWASP-Daten verfügbar."
          }
        ]
      }
      
      return NextResponse.json(data)
    }
    
    // Analysedatei gefunden, verwende diese
    const data = JSON.parse(fs.readFileSync(filePath, "utf-8"))
    return NextResponse.json(data)
    
  } catch (error) {
    console.error(`Fehler beim Laden der Analyse für Commit ${commitId}:`, error)
    return NextResponse.json(
      { error: `Fehler beim Laden der Analyse für Commit ${commitId}` },
      { status: 500 }
    )
  }
}

// Hilfsfunktion zum Zusammenfassen der Vulnerabilitäten
function summarizeVulnerabilities(results: any[] = []) {
  const summary = { critical: 0, high: 0, medium: 0, low: 0 }
  
  for (const result of results) {
    // Zählt Vulnerabilities
    if (result.Vulnerabilities) {
      for (const vuln of result.Vulnerabilities) {
        const severity = vuln.Severity.toLowerCase()
        if (severity in summary) {
          summary[severity as keyof typeof summary]++
        }
      }
    }
    
    // Zählt auch Misconfigurations
    if (result.Misconfigurations) {
      for (const misc of result.Misconfigurations) {
        const severity = misc.Severity.toLowerCase()
        if (severity in summary) {
          summary[severity as keyof typeof summary]++
        }
      }
    }
  }
  
  return summary
} 