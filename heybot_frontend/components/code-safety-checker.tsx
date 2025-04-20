"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertCircle, CheckCircle, Github, Loader2 } from "lucide-react"
import { analyzeCode } from "@/lib/actions"

type CheckStatus = "idle" | "loading" | "success" | "error"

interface CheckResult {
  status: "success" | "error"
  feedback: string
  issues: {
    type: "warning" | "error" | "info"
    message: string
  }[]
}

export function CodeSafetyChecker() {
  const [code, setCode] = useState("")
  const [status, setStatus] = useState<CheckStatus>("idle")
  const [result, setResult] = useState<CheckResult | null>(null)

  const handleSubmit = async () => {
    if (!code.trim()) return

    setStatus("loading")

    try {
      const analysisResult = await analyzeCode(code)
      setResult(analysisResult)
      setStatus(analysisResult.status)
    } catch (error) {
      setStatus("error")
      setResult({
        status: "error",
        feedback: "An error occurred while analyzing your code. Please try again.",
        issues: [
          {
            type: "error",
            message: "Service unavailable",
          },
        ],
      })
    }
  }

  const handlePushToGithub = () => {
    // In a real app, this would integrate with GitHub API
    alert("This would push your code to GitHub in a real implementation")
  }

  return (
    <div className="grid gap-8 md:grid-cols-2">
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Code Input</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder="Paste your code here..."
            className="min-h-[300px] font-mono text-sm"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button onClick={handleSubmit} disabled={status === "loading" || !code.trim()}>
            {status === "loading" && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Analyze Code
          </Button>
          <Button variant="outline" onClick={handlePushToGithub} disabled={status !== "success"} className="flex gap-2">
            <Github className="h-4 w-4" />
            Push to GitHub
          </Button>
        </CardFooter>
      </Card>

      {(status === "success" || status === "error") && result && (
        <>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                {status === "success" ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="text-green-700">Safety Check Passed</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-5 w-5 text-red-500" />
                    <span className="text-red-700">Safety Check Failed</span>
                  </>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-4 rounded-md bg-gray-50 border">
                <p className="text-sm whitespace-pre-wrap">{result.feedback}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Issues Found</CardTitle>
            </CardHeader>
            <CardContent>
              {result.issues.length === 0 ? (
                <p className="text-sm text-gray-500">No issues found in your code.</p>
              ) : (
                <ul className="space-y-2">
                  {result.issues.map((issue, index) => (
                    <li key={index} className="p-3 rounded-md border text-sm">
                      <div className="flex items-start gap-2">
                        {issue.type === "error" && <AlertCircle className="h-4 w-4 text-red-500 mt-0.5" />}
                        {issue.type === "warning" && <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5" />}
                        {issue.type === "info" && <AlertCircle className="h-4 w-4 text-blue-500 mt-0.5" />}
                        <span>{issue.message}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
