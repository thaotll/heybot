# HeyBot Frontend

This is the frontend for the HeyBot application, which displays GitHub commit data with analysis.

## GitHub API Rate Limits

The application relies on the GitHub API to fetch commit data. GitHub imposes rate limits on API requests:
- For unauthenticated requests: 60 requests per hour
- For authenticated requests: 5,000 requests per hour

To avoid hitting rate limits, the application:
1. Uses a GitHub personal access token for authentication
2. Implements caching at multiple levels
3. Displays warnings when rate limits are low

## Setup

### Environment Variables

Create a `.env.local` file in the `heybot_frontend` directory with:

```
GITHUB_TOKEN=your_github_personal_access_token
```

### Creating a GitHub Personal Access Token

1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token" (classic)
3. Give it a name like "HeyBot"
4. Select the `repo` and `workflow` scopes
5. Click "Generate token"
6. Copy the token and add it to your environment variables

### Checking GitHub Token Setup

Run the token checker script to verify your token is working correctly:

```bash
cd heybot_frontend
node scripts/check-github-token.js
```

## Rate Limit Optimization

The application reduces GitHub API requests by:

1. **Caching commit data**:
   - Server-side: 30-minute cache in the API route
   - Client-side: 5-minute cache in the browser
   
2. **Reduced API calls**:
   - Only fetches 10 commits at a time
   - Displays rate limit warnings when limits are low
   - Gracefully falls back to cached data when limits are reached

3. **Efficient Refresh Strategy**:
   - Manual refresh via "Aktualisieren" button
   - No automatic background refreshes
   - Visual indicator of remaining requests

## Troubleshooting

If you see rate limit error messages:

1. Check that your GitHub token is properly set
2. Wait until your rate limit resets (usually hourly)
3. Consider reducing refreshes to conserve API quota

For persistent issues, check the console for detailed error messages.

## Setup Instructions

Follow these steps to get the frontend running locally:

1. **Install dependencies**:
   ```bash
   npm install --legacy-peer-deps
   ```
   Note: We use `--legacy-peer-deps` to handle some package compatibility issues.

2. **Run the development server**:
   ```bash
   npm run dev
   ```
   The app will be available at [http://localhost:3030](http://localhost:3030) with turbopack enabled.

3. **Build for production**:
   ```bash
   npm run build
   ```

4. **Start production server**:
   ```bash
   npm start
   ```

## Project Structure

- `app/` - Next.js app router files
- `components/` - Reusable UI components
- `hooks/` - Custom React hooks
- `lib/` - Utility functions and shared code
- `public/` - Static assets
- `styles/` - Global styles and CSS modules 