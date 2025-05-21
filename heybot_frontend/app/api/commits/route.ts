import { NextResponse } from "next/server"
import { NextRequest } from "next/server"

const GITHUB_OWNER = "thaotll"
const GITHUB_REPO = "heybot"
const BRANCH = "main"

// Fetch last 2 commits
const GITHUB_API_URL = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/commits?sha=${BRANCH}&per_page=2`

// URL for fetching a specific commit (for file details - kept for potential future use or if needed by formattedFiles)
const COMMIT_DETAILS_URL = (sha: string) => `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/commits/${sha}`

// Cache duration for GitHub API responses (e.g., 5 minutes)
// Set to 0 to disable caching during development if preferred
const CACHE_DURATION = 5 * 60 * 1000; 
let cachedData: any = null;
let cacheTime: number = 0;

// Track remaining rate limit from GitHub
let commitDetailsCache = new Map<string, any>() // This was for commit file details, might still be useful
let remainingRateLimit: number = 5000 // Default assumption
let rateLimitResetTime: number = 0

// Backend API URL
const BACKEND_API_BASE_URL = "http://localhost:8081"; // Port-forwarded backend

export async function GET(request: NextRequest) {
  try {
    const now = Date.now()
    const forceRefresh = request.nextUrl.searchParams.get("refresh") === "true"

    if (!forceRefresh && cachedData && now - cacheTime < CACHE_DURATION) {
      return NextResponse.json({
        data: cachedData,
        source: "cache",
        remainingRequests: remainingRateLimit,
        cacheExpiresIn: Math.floor((cacheTime + CACHE_DURATION - now) / 1000),
      })
    }
    
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

    const cacheBuster = forceRefresh ? `&_=${Date.now()}` : ""
    console.log(`[api/commits] Fetching from GitHub: ${GITHUB_API_URL}${cacheBuster}`);
    const res = await fetch(`${GITHUB_API_URL}${cacheBuster}`, {
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${process.env.GITHUB_TOKEN || ""}`, // Ensure GITHUB_TOKEN is in .env.local
      },
      next: { revalidate: 0 }, // Disable Next.js fetch caching for this API call
    })

    const rateLimit = res.headers.get("x-ratelimit-remaining")
    const rateLimitReset = res.headers.get("x-ratelimit-reset")
    if (rateLimit) remainingRateLimit = parseInt(rateLimit, 10)
    if (rateLimitReset) rateLimitResetTime = parseInt(rateLimitReset, 10) * 1000
    console.log(`[api/commits] GitHub Rate Limit: Remaining ${remainingRateLimit}, Resets at ${new Date(rateLimitResetTime).toISOString()}`);


    if (!res.ok) {
      const errorText = await res.text()
      console.error(`[api/commits] GitHub API Error: ${res.status}`, errorText);
      // Return cached data if available when GitHub API fails
      if (cachedData) {
        return NextResponse.json({
          data: cachedData,
          source: "cache",
          error: "GitHub API Error, serving cached data",
          status: res.status,
          message: errorText,
          remainingRequests: remainingRateLimit,
        })
      }
      return NextResponse.json(
        { error: "GitHub API Error", status: res.status, message: errorText, remainingRequests: remainingRateLimit },
        { status: res.status }
      )
    }

    const githubCommits = await res.json()
    if (!Array.isArray(githubCommits)) {
      console.error("[api/commits] GitHub API did not return an array for commits:", githubCommits);
      return NextResponse.json({ error: "Invalid response from GitHub API for commits" }, { status: 500 });
    }


    const analyses = await Promise.all(
      githubCommits.map(async (commit: any) => {
        const sha = commit.sha
        const message = commit.commit.message
        const timestamp = commit.commit.author.date
        const author = commit.commit.author.name

        // Fetch commit details (files) - kept for now, can be removed if `formattedFiles` is not used
        let commitFiles: any[] = []
        if (commitDetailsCache.has(sha)) {
          commitFiles = commitDetailsCache.get(sha)
        } else {
          try {
            // Ensure GITHUB_TOKEN is also used for this call if it's a private repo or for higher rate limits
            const commitDetailsRes = await fetch(COMMIT_DETAILS_URL(sha), {
              headers: { Accept: "application/vnd.github+json", Authorization: `Bearer ${process.env.GITHUB_TOKEN || ""}` },
              next: { revalidate: 0 },
            })
            if (commitDetailsRes.ok) {
              const commitDetailsData = await commitDetailsRes.json()
              commitFiles = commitDetailsData.files || []
              commitDetailsCache.set(sha, commitFiles) // Cache commit file details
            }
          } catch (error) {
            console.error(`[api/commits] Error fetching commit details for ${sha}:`, error)
          }
        }
        const formattedFiles = commitFiles.map((file: any) => ({
          name: file.filename,
          status: file.status === "removed" ? "error" : "success", // Example status
          issues: 0, // Placeholder
        }))

        // --- Fetch analysis from backend API ---
        let humorMessage: string | undefined = "Analysis data not fetched yet."
        let securityScansFromAPI: any[] = []
        let analysisStatusFromAPI: string = "pending"; // Default status

        try {
          const backendAnalysisUrl = `${BACKEND_API_BASE_URL}/security-analysis/${sha}`;
          console.log(`[api/commits] Fetching analysis for ${sha} from backend: ${backendAnalysisUrl}`);
          const analysisRes = await fetch(backendAnalysisUrl, { cache: 'no-store' });
          
          console.log(`[api/commits] Backend response status for ${sha}: ${analysisRes.status}`);

          if (analysisRes.ok) {
            const analysisData = await analysisRes.json();
            console.log(`[api/commits] Backend response data for ${sha} (summary):`, analysisData?.deepseek_summary?.substring(0,100) + "...");
            humorMessage = analysisData.deepseek_summary || "DeepSeek summary not available.";
            securityScansFromAPI = analysisData.securityScansSummary || [];
            analysisStatusFromAPI = analysisData.status || "success"; // Use status from backend summary
          } else {
            const errorText = await analysisRes.text();
            console.warn(`[api/commits] No analysis found or error for commit ${sha} from backend (${analysisRes.status}): ${errorText.substring(0,100)}...`);
            humorMessage = analysisRes.status === 404 ? "No analysis found for this commit." : `Error fetching analysis: ${analysisRes.status}`;
            analysisStatusFromAPI = "error"; // Or "nodata", "warning"
            securityScansFromAPI = [
              { tool: "trivy", status: "nodata", vulnerabilities: { critical: 0, high: 0, medium: 0, low: 0 }, details: humorMessage },
              { tool: "owasp", status: "nodata", vulnerabilities: { critical: 0, high: 0, medium: 0, low: 0 }, details: "" }
            ];
          }
        } catch (err: any) {
          console.error(`[api/commits] Exception fetching analysis for ${sha}:`, err.message);
          humorMessage = `Exception fetching analysis: ${err.message ? err.message.substring(0,50) : "Unknown Error"}`;
          analysisStatusFromAPI = "error";
           securityScansFromAPI = [
              { tool: "trivy", status: "error", vulnerabilities: { critical: 0, high: 0, medium: 0, low: 0 }, details: "Error fetching analysis data." },
              { tool: "owasp", status: "error", vulnerabilities: { critical: 0, high: 0, medium: 0, low: 0 }, details: "" }
            ];
        }
        // --- End fetching analysis from backend API ---

        return {
          id: sha,
          commitId: sha,
          repository: `${GITHUB_OWNER}/${GITHUB_REPO}`,
          branch: BRANCH,
          timestamp,
          status: analysisStatusFromAPI, // Use status from backend analysis
          feedback: message, // GitHub commit message
          author,
          issues: [], // Placeholder - can be populated if needed later
          files: formattedFiles, // From GitHub commit details - can be removed if not used
          securityScans: securityScansFromAPI, // From backend _summary.json
          humorMessage: humorMessage, // From backend _summary.json (deepseek_summary)
          memeUrl: undefined, // memeUrl was from old local files, not in new _summary.json
          kubernetesStatus: { // Placeholder
            pods: { total: 0, running: 0, pending: 0, failed: 0 },
            deployments: { total: 0, available: 0, unavailable: 0 },
            services: 0,
          },
        }
      })
    )

    // Update GitHub API call cache
    cachedData = analyses
    cacheTime = now

    console.log(`[api/commits] Successfully processed ${analyses.length} commits.`);
    return NextResponse.json({
      data: analyses,
      source: forceRefresh ? "refresh" : "api",
      remainingRequests: remainingRateLimit,
      cacheExpiresIn: Math.floor((cacheTime + CACHE_DURATION - now) / 1000),
    })

  } catch (error: any) {
    console.error("[api/commits] Unhandled error in GET handler:", error.message, error.stack);
    // Set cache-control headers for the CLIENT (browser) even on error
    const response = NextResponse.json(
      { error: "Internal Server Error in /api/commits", details: error.message },
      { status: 500 }
    );
    response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate');
    response.headers.set('Pragma', 'no-cache');
    response.headers.set('Expires', '0');
    return response;
  }
}
