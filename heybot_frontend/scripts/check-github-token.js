#!/usr/bin/env node

/**
 * GitHub Token Checker
 * 
 * This script verifies if the GITHUB_TOKEN environment variable is set
 * and checks the current rate limit status with GitHub API.
 * 
 * Run with: node scripts/check-github-token.js
 */

const https = require('https');

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

console.log('\n🔍 GitHub API Token Check\n');

if (!GITHUB_TOKEN) {
  console.error('❌ ERROR: GITHUB_TOKEN environment variable is not set!');
  console.log('\nTo fix this:');
  console.log('1. Create a GitHub personal access token at https://github.com/settings/tokens');
  console.log('2. Set it as an environment variable before starting your app:');
  console.log('   - For development: Add to your .env.local file: GITHUB_TOKEN=your_token_here');
  console.log('   - For production: Set in your deployment environment');
  process.exit(1);
}

console.log('✅ GITHUB_TOKEN is set');

// Check token validity and rate limit
const options = {
  hostname: 'api.github.com',
  path: '/rate_limit',
  method: 'GET',
  headers: {
    'User-Agent': 'HeyBot-Rate-Limit-Checker',
    'Authorization': `Bearer ${GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github+json'
  }
};

const req = https.request(options, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    if (res.statusCode === 200) {
      const rateLimit = JSON.parse(data);
      
      console.log('\n💡 GitHub API Rate Limit Status:');
      console.log(`✅ Token is valid`);
      
      const core = rateLimit.resources.core;
      const remaining = core.remaining;
      const total = core.limit;
      const resetTime = new Date(core.reset * 1000).toLocaleTimeString();
      
      console.log(`📊 Core API: ${remaining}/${total} requests remaining`);
      console.log(`🕒 Rate limit resets at: ${resetTime}\n`);
      
      if (remaining < 100) {
        console.log('⚠️  WARNING: Rate limit is getting low!');
      } else {
        console.log('👍 Rate limit is healthy');
      }
      
      // Check GitHub App authentication if possible
      if (rateLimit.resources.graphql.limit > 5000) {
        console.log('✨ Advanced authentication detected - higher rate limits available');
      }
      
    } else if (res.statusCode === 401) {
      console.error('❌ ERROR: Invalid GitHub token! The provided token was rejected by GitHub.');
      console.log('\nTo fix this:');
      console.log('1. Generate a new token at https://github.com/settings/tokens');
      console.log('2. Update your environment variable with the new token');
    } else {
      console.error(`❌ ERROR: GitHub API returned status code ${res.statusCode}`);
      console.log(`Response: ${data}`);
    }
  });
});

req.on('error', (error) => {
  console.error('❌ ERROR connecting to GitHub API:', error.message);
});

req.end(); 