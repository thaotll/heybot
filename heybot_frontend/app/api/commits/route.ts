import { NextResponse } from "next/server"

const GITHUB_OWNER = "thaotll"
const GITHUB_REPO = "heybot"
const BRANCH = "main"

const GITHUB_API_URL = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/commits?sha=${BRANCH}&per_page=10`

// Increased cache duration to 30 minutes to reduce API calls
let cachedData: any = null;
let cacheTime: number = 0;
const CACHE_DURATION = 30 * 60 * 1000; // 30 minutes

// Track remaining rate limit
let remainingRateLimit: number = 5000; // Default GitHub authenticated rate limit
let rateLimitResetTime: number = 0;

export async function GET() {
  try {
    const now = Date.now();
    
    // Return cached data if available and not expired
    if (cachedData && (now - cacheTime < CACHE_DURATION)) {
      return NextResponse.json({
        data: cachedData,
        source: "cache",
        remainingRequests: remainingRateLimit,
        cacheExpiresIn: Math.floor((cacheTime + CACHE_DURATION - now) / 1000)
      });
    }
    
    // Check if we're near rate limit
    if (remainingRateLimit < 20 && now < rateLimitResetTime) {
      return NextResponse.json({
        data: cachedData || [],
        source: "cache",
        error: "Near GitHub API rate limit",
        rateLimitReset: new Date(rateLimitResetTime).toISOString(),
        remainingRequests: remainingRateLimit
      }, { status: 429 });
    }
    
    // Fetch commits with proper authorization
    const res = await fetch(GITHUB_API_URL, {
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${process.env.GITHUB_TOKEN || ""}`,
      },
      next: { revalidate: 1800 }, // Cache for 30 minutes on the Next.js side
    })

    // Update rate limit info from headers
    const rateLimit = res.headers.get('x-ratelimit-remaining');
    const rateLimitReset = res.headers.get('x-ratelimit-reset');
    
    if (rateLimit) remainingRateLimit = parseInt(rateLimit, 10);
    if (rateLimitReset) rateLimitResetTime = parseInt(rateLimitReset, 10) * 1000;

    if (!res.ok) {
      // Return cached data if available when API fails
      if (cachedData) {
        return NextResponse.json({
          data: cachedData,
          source: "cache",
          error: "GitHub API Error, serving cached data",
          status: res.status,
          remainingRequests: remainingRateLimit
        });
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
    
    // Process only 5 most recent commits (reduced from 10)
    const analyses = await Promise.all(commits.slice(0, 5).map(async (commit: any) => {
      const sha = commit.sha
      const message = commit.commit.message
      const timestamp = commit.commit.author.date
      const author = commit.commit.author.name

      // Instead of fetching workflow status for each commit,
      // just return a default status to save API calls
      return {
        id: sha,
        commitId: sha,
        repository: `${GITHUB_OWNER}/${GITHUB_REPO}`,
        branch: BRANCH,
        timestamp,
        status: "success", // Default status instead of fetching
        feedback: message,
        author: author,
        issues: [],
        files: [],
        securityScans: [],
        kubernetesStatus: {
          pods: { total: 0, running: 0, pending: 0, failed: 0 },
          deployments: { total: 0, available: 0, unavailable: 0 },
          services: 0,
        },
        memeUrl: undefined,
        humorMessage: undefined,
      }
    }))

    // Update cache
    cachedData = analyses;
    cacheTime = now;

    return NextResponse.json({
      data: analyses,
      source: "api",
      remainingRequests: remainingRateLimit,
      cacheExpiresIn: Math.floor(CACHE_DURATION / 1000)
    })
  } catch (error) {
    // Return cached data on error if available
    if (cachedData) {
      return NextResponse.json({
        data: cachedData,
        source: "cache",
        error: "Error fetching from GitHub, serving cached data",
        details: error instanceof Error ? error.message : String(error),
      });
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
