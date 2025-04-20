"use server"

// Mock data for the dashboard
export async function fetchLatestAnalyses() {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 1000))

  return [
    {
      id: "1",
      commitId: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
      repository: "backend-service",
      branch: "main",
      timestamp: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
      status: "success",
      feedback: "Code-Analyse erfolgreich abgeschlossen. Keine kritischen Probleme gefunden.",
      issues: [],
      files: [
        { name: "src/main.py", status: "success", issues: 0 },
        { name: "src/utils/helpers.py", status: "success", issues: 0 },
        { name: "src/api/endpoints.py", status: "success", issues: 0 },
        { name: "tests/test_api.py", status: "success", issues: 0 },
        { name: "Dockerfile", status: "success", issues: 0 },
      ],
      securityScans: [
        {
          tool: "trivy",
          status: "success",
          vulnerabilities: {
            critical: 0,
            high: 0,
            medium: 1,
            low: 3,
          },
          details: "Eine mittelschwere Abhängigkeit sollte aktualisiert werden.",
        },
        {
          tool: "owasp",
          status: "success",
          vulnerabilities: {
            critical: 0,
            high: 0,
            medium: 0,
            low: 2,
          },
          details: "Keine kritischen Sicherheitsprobleme gefunden.",
        },
      ],
      kubernetesStatus: {
        pods: {
          total: 5,
          running: 5,
          pending: 0,
          failed: 0,
        },
        deployments: {
          total: 2,
          available: 2,
          unavailable: 0,
        },
        services: 3,
      },
      humorMessage: "Dein Code ist so sauber, selbst Marie Kondo wäre stolz! ✨",
    },
    {
      id: "2",
      commitId: "b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7",
      repository: "ml-pipeline",
      branch: "feature/new-model",
      timestamp: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
      status: "error",
      feedback:
        "Mehrere Sicherheitsprobleme und Code-Qualitätsprobleme gefunden. Bitte überprüfen Sie die Details unten.",
      issues: [
        {
          type: "error",
          message: "Hardcodierte Zugangsdaten in der Datei gefunden. Verwenden Sie stattdessen Umgebungsvariablen.",
          file: "src/config.py",
          line: 42,
        },
        {
          type: "warning",
          message: "Veraltete Bibliothek verwendet. Aktualisieren Sie auf die neueste Version.",
          file: "requirements.txt",
          line: 15,
        },
        {
          type: "error",
          message: "Unsichere Deserialisierung von Benutzereingaben.",
          file: "src/api/input_handler.py",
          line: 78,
        },
      ],
      files: [
        { name: "src/config.py", status: "error", issues: 1 },
        { name: "src/api/input_handler.py", status: "error", issues: 1 },
        { name: "requirements.txt", status: "warning", issues: 1 },
        { name: "src/models/classifier.py", status: "success", issues: 0 },
        { name: "Dockerfile", status: "success", issues: 0 },
      ],
      securityScans: [
        {
          tool: "trivy",
          status: "error",
          vulnerabilities: {
            critical: 1,
            high: 2,
            medium: 3,
            low: 5,
          },
          details: "Kritische Sicherheitslücke in einer Abhängigkeit gefunden. Sofortige Aktualisierung erforderlich.",
        },
        {
          tool: "owasp",
          status: "error",
          vulnerabilities: {
            critical: 0,
            high: 3,
            medium: 2,
            low: 4,
          },
          details: "Mehrere hochriskante Sicherheitsprobleme gefunden.",
        },
      ],
      kubernetesStatus: {
        pods: {
          total: 4,
          running: 3,
          pending: 0,
          failed: 1,
        },
        deployments: {
          total: 2,
          available: 1,
          unavailable: 1,
        },
        services: 2,
      },
      memeUrl: "https://i.imgflip.com/7zq8qh.jpg",
      humorMessage: "Dein Code hat mehr Lecks als die Titanic! 🚢💦",
    },
    {
      id: "3",
      commitId: "c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8",
      repository: "frontend-app",
      branch: "develop",
      timestamp: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
      status: "success",
      feedback: "Code-Analyse erfolgreich. Einige kleinere Verbesserungsvorschläge wurden identifiziert.",
      issues: [
        {
          type: "info",
          message: "Erwägen Sie die Verwendung von TypeScript für bessere Typsicherheit.",
          file: "src/components/UserProfile.js",
        },
        {
          type: "info",
          message: "Kommentare für komplexe Funktionen hinzufügen.",
          file: "src/utils/dataTransformers.js",
        },
      ],
      files: [
        { name: "src/components/UserProfile.js", status: "success", issues: 1 },
        { name: "src/utils/dataTransformers.js", status: "success", issues: 1 },
        { name: "src/App.js", status: "success", issues: 0 },
        { name: "public/index.html", status: "success", issues: 0 },
        { name: "Dockerfile", status: "success", issues: 0 },
      ],
      securityScans: [
        {
          tool: "trivy",
          status: "success",
          vulnerabilities: {
            critical: 0,
            high: 0,
            medium: 2,
            low: 4,
          },
          details: "Keine kritischen Sicherheitsprobleme gefunden.",
        },
        {
          tool: "renovate",
          status: "warning",
          vulnerabilities: {
            critical: 0,
            high: 0,
            medium: 1,
            low: 3,
          },
          details: "Einige Abhängigkeiten sollten aktualisiert werden.",
        },
      ],
      kubernetesStatus: {
        pods: {
          total: 3,
          running: 3,
          pending: 0,
          failed: 0,
        },
        deployments: {
          total: 1,
          available: 1,
          unavailable: 0,
        },
        services: 1,
      },
      humorMessage: "Dein Code ist wie ein guter Witz - gut strukturiert und leicht zu verstehen! 😄",
    },
  ]
}

interface CheckResult {
  status: "success" | "error"
  feedback: string
  issues: {
    type: "warning" | "error" | "info"
    message: string
  }[]
}

export async function analyzeCode(code: string): Promise<CheckResult> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 500))

  // Basic checks (replace with actual analysis logic)
  if (code.includes("eval(")) {
    return {
      status: "error",
      feedback: "Potentially unsafe 'eval()' function detected.",
      issues: [
        {
          type: "error",
          message: "Avoid using 'eval()' due to security risks.",
        },
      ],
    }
  }

  if (code.includes("http://")) {
    return {
      status: "warning",
      feedback: "Non-HTTPS URL detected. Consider using HTTPS for secure connections.",
      issues: [
        {
          type: "warning",
          message: "Use HTTPS instead of HTTP.",
        },
      ],
    }
  }

  // If no issues found, return a success result
  return {
    status: "success",
    feedback: "No immediate safety concerns found.",
    issues: [],
  }
}
