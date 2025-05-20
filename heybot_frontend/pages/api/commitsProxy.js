export default async function handler(req, res) {
  // Add a cache-busting timestamp to the backend request
  const backendUrl = `http://localhost:8080/security-analysis/latest?proxybust=${new Date().getTime()}`;
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

    // Wrap the single object in the structure expected by lib/actions.ts
    const responseToFrontend = {
      data: singleAnalysisObject ? [singleAnalysisObject] : [], // Array containing the single object, or empty if null
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