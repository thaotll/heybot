import { NextResponse } from "next/server"

const GITHUB_OWNER = "thaotll"
const GITHUB_REPO = "heybot"
const BRANCH = "main"

const GITHUB_API_URL = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/commits?sha=${BRANCH}&per_page=100`

export async function GET() {
  try {
    const res = await fetch(GITHUB_API_URL, {
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
      },
      cache: "no-store",
    })

    if (!res.ok) {
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

    // Get the latest workflow run status for each commit
    const analyses = await Promise.all(commits.map(async (commit: any) => {
      const sha = commit.sha
      const message = commit.commit.message
      const timestamp = commit.commit.author.date
      const author = commit.commit.author.name

      // Get the workflow run status for this commit
      const workflowRes = await fetch(
        `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/runs?head_sha=${sha}`,
        {
          headers: {
            Accept: "application/vnd.github+json",
            Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
          },
        }
      )

      let status: "success" | "error" | "pending" = "pending"
      if (workflowRes.ok) {
        const workflowData = await workflowRes.json()
        if (workflowData.workflow_runs.length > 0) {
          const latestRun = workflowData.workflow_runs[0]
          status = latestRun.conclusion === "success" ? "success" : "error"
        }
      }

      return {
        id: sha,
        commitId: sha,
        repository: `${GITHUB_OWNER}/${GITHUB_REPO}`,
        branch: BRANCH,
        timestamp,
        status,
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

    return NextResponse.json(analyses)
  } catch (error) {
    return NextResponse.json(
      {
        error: "Unexpected error",
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
