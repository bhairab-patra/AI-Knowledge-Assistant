 
const fs = require('fs');
const path = require('path');

// Get BUILD_ENV from command line
const args = process.argv.slice(2);
const envArg = args.find(arg => arg.startsWith('--env='));
const env = envArg ? envArg.split('=')[1] : 'dev';

console.log(`\n=== Build Info Script ===`);
console.log(`Environment: ${env}`);

const version = require('../package.json').version;
const date = new Date().toLocaleString();

// Read from .env file based on env
const envFile = `.env.${env}`;
let apiUrl = 'not set';
let cdnUrl = 'not set';

try {
  const envFilePath = path.join(__dirname, '..', envFile);
  console.log(`Reading: ${envFilePath}`);
  
  const envContent = fs.readFileSync(envFilePath, 'utf8');
  
  // Extract API URL
  const apiMatch = envContent.match(/VITE_API_BASE_URL=(.*)/);
  if (apiMatch) {
    apiUrl = apiMatch[1].trim();
  }
  
  // Extract CDN URL
  const cdnMatch = envContent.match(/VITE_CDN_URL=(.*)/);
  if (cdnMatch) {
    cdnUrl = cdnMatch[1].trim();
  }
} catch (e) {
  console.error(`Could not read ${envFile}:`, e.message);
}

// 1. Create BUILD_INFO.txt
const content = `
Environment: ${env.toUpperCase()}
Version: ${version}
Build Date: ${date}
API URL: ${apiUrl}
CDN URL: ${cdnUrl}
`;

const distPath = path.join(__dirname, '../dist');
const buildInfoPath = path.join(distPath, 'BUILD_INFO.txt');

// Check if dist folder exists
if (!fs.existsSync(distPath)) {
  console.log('Creating dist folder...');
  fs.mkdirSync(distPath, { recursive: true });
}

try {
  fs.writeFileSync(buildInfoPath, content.trim());
  console.log(`BUILD_INFO.txt created successfully`);
  console.log(`   API URL: ${apiUrl}`);
  console.log(`   CDN URL: ${cdnUrl}`);
} catch (e) {
  console.error(` Failed to write BUILD_INFO.txt:`, e.message);
  process.exit(1);
}

// 2. Replace __CDN_URL__ in dist/index.html
const indexHtmlPath = path.join(distPath, 'index.html');

if (fs.existsSync(indexHtmlPath)) {
  try {
    let htmlContent = fs.readFileSync(indexHtmlPath, 'utf8');
    
    // Replace placeholder with actual CDN URL
    if (htmlContent.includes('__CDN_URL__')) {
      htmlContent = htmlContent.replace(/__CDN_URL__/g, cdnUrl);
      fs.writeFileSync(indexHtmlPath, htmlContent);
      console.log(`Replaced __CDN_URL__ with: ${cdnUrl}`);
    } else {
      console.warn(`Placeholder __CDN_URL__ not found in index.html`);
    }
  } catch (e) {
    console.error(`Failed to update index.html:`, e.message);
  }
} else {
  console.error(`index.html not found`);
}

console.log(`=== Build Info Complete ===\n`);