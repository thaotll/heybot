import { NextResponse } from "next/server"
import { NextRequest } from "next/server"
import fs from "fs"
import path from "path"

const GITHUB_OWNER = "thaotll"
const GITHUB_REPO = "heybot"
const BRANCH = "main"

const GITHUB_API_URL = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/commits?sha=${BRANCH}&per_page=15`

// URL for fetching a specific commit (for file details)
const COMMIT_DETAILS_URL = (sha: string) => `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/commits/${sha}`
const ANALYSIS_PATH = "/app/analysis"

// Increased cache duration to 30 minutes to reduce API calls
let cachedData: any = null;
let cacheTime: number = 0;
const CACHE_DURATION = 30 * 60 * 1000; // 30 minutes

// Track remaining rate limit
let commitDetailsCache = new Map<string, any>()
let remainingRateLimit: number = 5000
let rateLimitResetTime: number = 0

export async function GET(request: NextRequest) {
  try {
    const now = Date.now()
    const forceRefresh = request.nextUrl.searchParams.get("refresh") === "true"

      // Return cached data if available, not expired, and not force refreshing
    if (!forceRefresh && cachedData && now - cacheTime < CACHE_DURATION) {
      return NextResponse.json({
        data: cachedData,
        source: "cache",
        remainingRequests: remainingRateLimit,
        cacheExpiresIn: Math.floor((cacheTime + CACHE_DURATION - now) / 1000),
      })
    }
    
    // Check if we're near rate limit
    if (remainingRateLimit < 20 && now < rateLimitResetTime) {
      return NextResponse.json(
        {
          data: cachedData || [],
          source: "cache",
          error: "Near GitHub API rate limit",
          rateLimitReset: new Date(rateLimitResetTime).toISOString(),
          remainingRequests: remainingRateLimit,
        },
        { status: 429 }
      )
    }

    // Add a cache busting parameter to prevent GitHub from serving cached results
    const cacheBuster = forceRefresh ? `&_=${Date.now()}` : ""

      // Fetch commits with proper authorization
    const res = await fetch(`${GITHUB_API_URL}${cacheBuster}`, {
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${process.env.GITHUB_TOKEN || ""}`,
      },
      next: { revalidate: 0 },
    })

      // Update rate limit info from headers
    const rateLimit = res.headers.get("x-ratelimit-remaining")
    const rateLimitReset = res.headers.get("x-ratelimit-reset")
    if (rateLimit) remainingRateLimit = parseInt(rateLimit, 10)
    if (rateLimitReset) rateLimitResetTime = parseInt(rateLimitReset, 10) * 1000

    if (!res.ok) {
      // Return cached data if available when API fails
      if (cachedData) {
        return NextResponse.json({
          data: cachedData,
          source: "cache",
          error: "GitHub API Error, serving cached data",
          status: res.status,
          remainingRequests: remainingRateLimit,
        })
      }
      
      const errorText = await res.text()
      return NextResponse.json(
        {
          error: "GitHub API Error",
          status: res.status,
          message: errorText,
        },
        { status: res.status }
      )
    }

    const commits = await res.json()

    const analyses = await Promise.all(
      commits.map(async (commit: any) => {
        const sha = commit.sha
        const message = commit.commit.message
        const timestamp = commit.commit.author.date
        const author = commit.commit.author.name

          // Fetch commit details to get file information
        let commitFiles: any[] = []
        if (commitDetailsCache.has(sha)) {
          commitFiles = commitDetailsCache.get(sha)
        } else {
          try {
            const commitDetailsRes = await fetch(COMMIT_DETAILS_URL(sha), {
              headers: {
                Accept: "application/vnd.github+json",
                Authorization: `Bearer ${process.env.GITHUB_TOKEN || ""}`,
              },
              next: { revalidate: 0 },
            })
            if (commitDetailsRes.ok) {
              const commitDetails = await commitDetailsRes.json()
              commitFiles = commitDetails.files || []
              commitDetailsCache.set(sha, commitFiles)
            }
          } catch (error) {
            console.error("Error fetching commit details:", error)
          }
        }

        let formattedFiles = commitFiles.map((file: any) => ({
          name: file.filename,
          status: file.status === "removed" ? "error" : "success",
          issues: 0,
        }))

        // Analyse laden
        let securityScans: any[] = []
        let humorMessage: string | undefined = undefined
        let memeUrl: string | undefined = undefined

        try {
          const analysisFile = path.join(ANALYSIS_PATH, `${sha}.json`)
          if (fs.existsSync(analysisFile)) {
            const data = JSON.parse(fs.readFileSync(analysisFile, "utf-8"))
            if (Array.isArray(data.securityScans)) securityScans = data.securityScans
            if (data.humorMessage) humorMessage = data.humorMessage
            if (data.memeUrl) memeUrl = data.memeUrl
          }
        } catch (err) {
          console.error(`Fehler beim Laden der Analyse für Commit ${sha}:`, err)
        }

        const hasCriticalIssues = securityScans.some(scan => scan.vulnerabilities?.critical > 0 || scan.vulnerabilities?.high > 0)
        const hasFailedScans = securityScans.some(scan => scan.status === "error")
        const status = hasFailedScans || hasCriticalIssues ? "error" : "success"

          // Instead of fetching workflow status for each commit,
      // just return a default status to save API calls
        return {
          id: sha,
          commitId: sha,
          repository: `${GITHUB_OWNER}/${GITHUB_REPO}`,
          branch: BRANCH,
          timestamp,
          status,
          feedback: message,
          author,
          issues: [],
          files: formattedFiles,
          securityScans,
          humorMessage,
          memeUrl,
          kubernetesStatus: {
            pods: { total: 0, running: 0, pending: 0, failed: 0 },
            deployments: { total: 0, available: 0, unavailable: 0 },
            services: 0,
          },
        }
      })
    )

    // Update cache
    cachedData = analyses
    cacheTime = now

    return NextResponse.json({
      data: analyses,
      source: forceRefresh ? "refresh" : "api",
      remainingRequests: remainingRateLimit,
      cacheExpiresIn: Math.floor(CACHE_DURATION / 1000),
    })
  } catch (error) {
    // Return cached data on error if available
    if (cachedData) {
      return NextResponse.json({
        data: cachedData,
        source: "cache",
        error: "Error fetching from GitHub, serving cached data",
        details: error instanceof Error ? error.message : String(error),
      })
    }

    return NextResponse.json(
      {
        error: "Unexpected error",
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
