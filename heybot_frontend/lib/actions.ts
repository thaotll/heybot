"use client"

import type { CodeAnalysis } from "@/components/code-analysis-dashboard"

// Client-side cache
let cachedAnalyses: CodeAnalysis[] | null = null;
let lastFetchTime = 0;
const CACHE_DURATION = 5 * 60 * 1000; // Increased to 5 minutes

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
    if (!forceRefresh && cachedAnalyses && (now - lastFetchTime < CACHE_DURATION)) {
      return {
        analyses: cachedAnalyses,
        rateLimitInfo: remainingRequests < 100 ? 
          `GitHub API rate limit: ${remainingRequests} requests remaining` : 
          undefined
      };
    }

    const res = await fetch(`/api/commits${forceRefresh ? '?refresh=true' : ''}`, {
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
    
    // Update cache
    cachedAnalyses = response.data as CodeAnalysis[];
    lastFetchTime = now;
    
    let rateLimitInfo;
    if (remainingRequests < 100) {
      rateLimitInfo = `GitHub API rate limit: ${remainingRequests} requests remaining`;
    }
    
    return {
      analyses: cachedAnalyses,
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