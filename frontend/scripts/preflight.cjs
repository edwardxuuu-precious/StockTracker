#!/usr/bin/env node

/**
 * Pre-flight validation script
 * Supports runtime VITE_API_URL from process env.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('[preflight] Running checks...\n');

let hasErrors = false;
const envPath = path.join(__dirname, '..', '.env');
let apiUrl = process.env.VITE_API_URL || '';

console.log('[check] .env presence');
if (!fs.existsSync(envPath)) {
  console.error('[error] .env file not found');
  console.error('        Create from .env.example if needed.\n');
  hasErrors = true;
} else {
  console.log('[ok] .env exists\n');
}

console.log('[check] API URL configuration');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf-8');
  const match = envContent.match(/VITE_API_URL=(.+)/);
  if (!apiUrl && match) {
    apiUrl = match[1].trim();
  }
}

if (!apiUrl) {
  console.error('[error] VITE_API_URL missing (.env or process env)\n');
  hasErrors = true;
} else {
  console.log(`[ok] API URL: ${apiUrl}`);
  if (apiUrl.includes(':8000')) {
    console.error('[error] API URL points to :8000, expected active backend port\n');
    hasErrors = true;
  } else {
    console.log('[ok] API URL format looks valid\n');
  }
}

console.log('[check] Backend connectivity');
if (apiUrl) {
  const testUrl = `${apiUrl.replace(/\/$/, '')}/api/v1/portfolios/`;
  try {
    if (process.platform === 'win32') {
      execSync(`curl -s -o nul -w "%{http_code}" ${testUrl}`, { timeout: 3000 });
    } else {
      execSync(`curl -s -o /dev/null -w "%{http_code}" ${testUrl}`, { timeout: 3000 });
    }
    console.log(`[ok] Backend reachable: ${testUrl}\n`);
  } catch (error) {
    console.error(`[error] Cannot reach backend: ${testUrl}`);
    console.error('        Start backend first and retry.\n');
    hasErrors = true;
  }
}

console.log('[check] node_modules');
const nodeModulesPath = path.join(__dirname, '..', 'node_modules');
if (!fs.existsSync(nodeModulesPath)) {
  console.error('[error] node_modules missing (run npm install)\n');
  hasErrors = true;
} else {
  console.log('[ok] Dependencies installed\n');
}

if (hasErrors) {
  console.log('[preflight] FAILED\n');
  process.exit(1);
}

console.log('[preflight] PASSED\n');
process.exit(0);
