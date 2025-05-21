export default async function handler(req, res) {
  // Add a cache-busting timestamp to the backend request
  const backendUrl = `http://localhost:8081/security-analysis/latest?proxybust=${new Date().getTime()}`;
  console.log(`[commitsProxy] Fetching: ${backendUrl}`);

  try {
    const backendRes = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store', // Ensure fresh fetch TO the backend
    });

    const responseText = await backendRes.text(); // Get text first for debugging
    console.log(`[commitsProxy] Backend status: ${backendRes.status}`);
    console.log(`[commitsProxy] Backend response text: ${responseText.substring(0, 200)}...`);


    if (!backendRes.ok) {
      // Forward the error status and message
      // Attempt to parse as JSON if it's an error structure from our backend, else send text
      let errorData = responseText;
      try {
        errorData = JSON.parse(responseText);
      } catch (e) {
        // Not JSON, send as text
      }
      return res.status(backendRes.status).json(errorData);
    }

    const singleAnalysisObject = JSON.parse(responseText); // Now parse the text as JSON

    // Transform singleAnalysisObject to match the CodeAnalysis interface
    let transformedAnalysis = null;
    if (singleAnalysisObject) {
      transformedAnalysis = {
        id: singleAnalysisObject.id || singleAnalysisObject.commitId,
        commitId: singleAnalysisObject.commitId,
        repository: singleAnalysisObject.repository,
        branch: singleAnalysisObject.branch,
        timestamp: singleAnalysisObject.timestamp,
        status: singleAnalysisObject.status, // Assuming status is "success", "error", or "pending"
        
        feedback: `Analysis for ${singleAnalysisObject.commitId ? singleAnalysisObject.commitId.substring(0,7) : 'N/A'}`, // Placeholder
        author: "N/A", // Not available in new summary

        humorMessage: singleAnalysisObject.deepseek_summary, // Map deepseek_summary

        // Fields not in new summary - provide default/empty values
        issues: [], 
        files: [],
        kubernetesStatus: {
          pods: { total: 0, running: 0, pending: 0, failed: 0 },
          deployments: { total: 0, available: 0, unavailable: 0 },
          services: 0
        },
        memeUrl: null, 

        securityScans: singleAnalysisObject.securityScansSummary ? 
          singleAnalysisObject.securityScansSummary.map(scan => ({
            tool: scan.tool.toLowerCase(), // "trivy" or "owasp"
            // Infer status based on vulnerability counts
            status: (scan.vulnerabilities && (scan.vulnerabilities.critical > 0 || scan.vulnerabilities.high > 0)) ? "error" : 
                    ((scan.vulnerabilities && scan.vulnerabilities.medium > 0) ? "warning" : "success"),
            vulnerabilities: scan.vulnerabilities || { critical: 0, high: 0, medium: 0, low: 0 },
            details: `Scan results for ${scan.tool}. Overall summary provided by DeepSeek.` // Placeholder
          })) : []
      };
    }

    // Wrap the single object in the structure expected by lib/actions.ts
    const responseToFrontend = {
      data: transformedAnalysis ? [transformedAnalysis] : [], // Array containing the single object, or empty if null
      source: "api",
      // You could add dummy values for other ApiResponse fields if strictly needed,
      // but lib/actions.ts primarily cares about `data`.
      remainingRequests: null, // Or fetch from a different source if available
      cacheExpiresIn: null,
      rateLimitReset: null
    };

    // Set cache-control headers for the CLIENT (browser)
    res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');

    return res.status(200).json(responseToFrontend);
  } catch (error) {
    console.error('[commitsProxy] Error:', error);
    // Set cache-control headers for the CLIENT (browser) even on error
    res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');
    return res.status(500).json({ error: 'Proxy request failed', details: error.message });
  }
} 