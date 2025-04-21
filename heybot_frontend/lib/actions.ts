"use client"

import type { CodeAnalysis } from "@/components/code-analysis-dashboard"

export async function fetchLatestAnalyses(): Promise<CodeAnalysis[]> {
  try {
    const res = await fetch("/api/commits", {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    })

    if (!res.ok) {
      throw new Error("Fehler beim Abrufen der Commits")
    }

    const data = await res.json()
    return data as CodeAnalysis[]
  } catch (error) {
    console.error("Fehler in fetchLatestAnalyses:", error)
    return []
  }
}