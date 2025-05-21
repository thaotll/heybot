"use client"

import type { CodeAnalysis } from "@/components/code-analysis-dashboard"

// Client-side cache
let cachedAnalyses: CodeAnalysis[] | null = null;
let lastFetchTime = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5 Minuten

// Rate limit tracking
let remainingRequests: number = 5000;
let lastRateLimitWarning: number = 0;

interface ApiResponse {
  data: CodeAnalysis[];
  source: "cache" | "api";
  error?: string;
  remainingRequests?: number;
  cacheExpiresIn?: number;
  rateLimitReset?: string;
}

export async function fetchLatestAnalyses(forceRefresh = false): Promise<{analyses: CodeAnalysis[], rateLimitInfo?: string}> {
  try {
    // Use cached data if available and not expired, unless forceRefresh is true
    const now = Date.now();
    // RE-ENABLE CLIENT-SIDE CACHE
    if (!forceRefresh && cachedAnalyses && (now - lastFetchTime < CACHE_DURATION)) {
      console.log("[lib/actions] Using client-side cached analyses.");
      return {
        analyses: cachedAnalyses,
        rateLimitInfo: remainingRequests < 100 ? 
          `GitHub API rate limit: ${remainingRequests} requests remaining` : 
          undefined
      };
    }

    // const fetchUrl = `/api/commits${forceRefresh ? '?refresh=true&' : '?'}ts=${new Date().getTime()}`;
    // Let the new proxy handle its own cache busting for the backend call.
    // The forceRefresh param can still be used if the proxy wants to use it for its own client-side caching if any.
    // REMOVE ts=... from here as caching is re-enabled above, and proxy handles its backend cache busting.
    const fetchUrl = `/api/commits${forceRefresh ? '?refresh=true' : ''}`;
    console.log(`[lib/actions] Fetching from frontend: ${fetchUrl}`);

    const res = await fetch(fetchUrl, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      // Don't use Next.js cache to ensure we get latest rate limit info
      cache: "no-store",
    })

    if (res.status === 429) {
      // Rate limit reached - use cached data if available
      lastRateLimitWarning = now;
      const data = await res.json() as ApiResponse;
      
      if (cachedAnalyses) {
        if (data.remainingRequests) remainingRequests = data.remainingRequests;
        return {
          analyses: cachedAnalyses,
          rateLimitInfo: `GitHub API rate limit reached. Reset at ${new Date(data.rateLimitReset || 0).toLocaleTimeString()}.`
        };
      }
      
      // If no cached data, return empty with warning
      return {
        analyses: [],
        rateLimitInfo: `GitHub API rate limit reached. Reset at ${new Date(data.rateLimitReset || 0).toLocaleTimeString()}.`
      };
    }

    if (!res.ok) {
      if (cachedAnalyses) {
        return {
          analyses: cachedAnalyses,
          rateLimitInfo: `Error fetching data. Using cached data.`
        };
      }
      throw new Error("Fehler beim Abrufen der Commits")
    }

    const response = await res.json() as ApiResponse;
    
    // Update rate limit info
    if (response.remainingRequests !== undefined) {
      remainingRequests = response.remainingRequests;
    }
    
    // Daten direkt aus der commits-Route verwenden - keine separate Abfrage für Sicherheitsdaten
    const analyses = response.data;
    
    // Update cache
    cachedAnalyses = analyses;
    lastFetchTime = now;
    
    let rateLimitInfo;
    if (remainingRequests < 100) {
      rateLimitInfo = `GitHub API rate limit: ${remainingRequests} requests remaining`;
    }
    
    return {
      analyses,
      rateLimitInfo
    };
  } catch (error) {
    console.error("Fehler in fetchLatestAnalyses:", error)
    
    if (cachedAnalyses) {
      return {
        analyses: cachedAnalyses,
        rateLimitInfo: "Error fetching data. Using cached data."
      };
    }
    
    return {
      analyses: [],
      rateLimitInfo: "Error fetching data. No cached data available."
    };
  }
}