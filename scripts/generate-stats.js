#!/usr/bin/env node

const fs = require('fs');
const https = require('https');

const token = process.env.GITHUBPAT;
const username = 'A4GOD-AMHG';

if (!token) {
    console.error('❌ Error: GITHUBPAT environment variable not set');
    console.error('   Usage: export GITHUBPAT=your_github_token');
    process.exit(1);
}

async function makeGraphQLRequest(query, variables = {}) {
    return new Promise((resolve, reject) => {
        const payload = JSON.stringify({ query, variables });
        
        const options = {
            hostname: 'api.github.com',
            path: '/graphql',
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Content-Length': payload.length,
                'User-Agent': 'GitHub-Stats-Generator'
            }
        };
        
        const req = https.request(options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                if (res.statusCode < 200 || res.statusCode >= 300) {
                    console.error(`❌ HTTP Error: ${res.statusCode}`);
                    console.error('Response body:', data);
                    try {
                        const json = JSON.parse(data);
                        if (json.message) {
                            console.error('API Message:', json.message);
                        }
                    } catch (e) {
                        // Ignore parsing error for error responses
                    }
                    reject(new Error(`HTTP Error: ${res.statusCode}`));
                    return;
                }

                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    console.error('❌ Failed to parse JSON response:', data);
                    reject(e);
                }
            });
        });
        
        req.on('error', reject);
        req.write(payload);
        req.end();
    });
}

async function fetchUserData() {
    const query = `
        query($userName:String!) {
            user(login: $userName) {
                followers {
                    totalCount
                }
                following {
                    totalCount
                }
                repositories(first: 100, affiliations: [OWNER, COLLABORATOR]) {
                    totalCount
                    nodes {
                        isPrivate
                        primaryLanguage {
                            name
                        }
                        stargazerCount
                        forks {
                            totalCount
                        }
                        object(expression: "HEAD") {
                            ... on Commit {
                                history(first: 0) {
                                    totalCount
                                }
                            }
                        }
                    }
                }
            }
        }
    `;
    
    return makeGraphQLRequest(query, { userName: username });
}

async function generateStats() {
    try {
        console.log('🔍 Fetching GitHub stats for', username, '...\n');
        
        const response = await fetchUserData();
        
        if (response.errors) {
            console.error('❌ GraphQL Error:', JSON.stringify(response.errors, null, 2));
            process.exit(1);
        }

        if (!response.data || !response.data.user) {
            console.error('❌ Unexpected response structure:', JSON.stringify(response, null, 2));
            process.exit(1);
        }
        
        const user = response.data.user;
        
        console.log('📦 Processing repositories...');
        
        let totalRepos = 0;
        let publicRepos = 0;
        let privateRepos = 0;
        let totalCommits = 0;
        let totalStars = 0;
        let totalForks = 0;
        const languageStats = {};
        
        user.repositories.nodes.forEach(repo => {
            if (!repo) return;
            
            totalRepos++;
            
            if (repo.isPrivate) {
                privateRepos++;
            } else {
                publicRepos++;
            }
            
            totalStars += repo.stargazerCount || 0;
            totalForks += (repo.forks?.totalCount || 0);
            
            if (repo.object && repo.object.history) {
                totalCommits += repo.object.history.totalCount || 0;
            }
            
            if (repo.primaryLanguage && repo.primaryLanguage.name) {
                const lang = repo.primaryLanguage.name;
                languageStats[lang] = (languageStats[lang] || 0) + 1;
            }
        });
        
        console.log(`✅ Found ${totalRepos} repos (${publicRepos} public, ${privateRepos} private)`);
        console.log(`✅ Total commits: ${totalCommits}`);
        
        const sortedLanguages = Object.entries(languageStats)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8)
            .reduce((obj, [key, val]) => {
                obj[key] = val;
                return obj;
            }, {});
        
        const stats = {
            followers: user.followers.totalCount,
            following: user.following.totalCount,
            public_repos: publicRepos,
            private_repos: privateRepos,
            total_repos: totalRepos,
            total_commits: totalCommits,
            total_stars: totalStars,
            total_forks: totalForks,
            top_languages: sortedLanguages
        };
        
        // Write stats to file
        const statsDir = '.github';
        if (!fs.existsSync(statsDir)) {
            fs.mkdirSync(statsDir, { recursive: true });
        }
        
        fs.writeFileSync(`${statsDir}/stats.json`, JSON.stringify(stats, null, 2));
        
        console.log('\n📈 Top Languages:', sortedLanguages);
        console.log('✨ Stats generated successfully!');
        
        generateSvg(stats);
        
        return stats;
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    }
}

function generateSvg(stats) {
    const template = `
    <svg width="495" height="195" viewBox="0 0 495 195" fill="none" xmlns="http://www.w3.org/2000/svg">
        <style>
            .header {
                font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif;
                fill: #7F7DFF;
            }
            .stat {
                font: 400 14px 'Segoe UI', Ubuntu, "Helvetica Neue", Sans-Serif;
                fill: #FFFFFF;
            }
            .value {
                font: 600 14px 'Segoe UI', Ubuntu, "Helvetica Neue", Sans-Serif;
                fill: #FFFFFF;
            }
            .border {
                stroke: #30363D;
                stroke-width: 1;
            }
        </style>
        <rect x="0.5" y="0.5" width="494" height="194" rx="4.5" fill="#0D1117" class="border"/>
        <g transform="translate(25, 35)">
            <text x="0" y="0" class="header">Alexis's GitHub Stats</text>
        </g>
        <g transform="translate(0, 55)">
            <g transform="translate(25, 20)">
                <text x="0" y="0" class="stat">Total Stars:</text>
                <text x="160" y="0" class="value">${stats.total_stars}</text>
            </g>
            <g transform="translate(25, 45)">
                <text x="0" y="0" class="stat">Total Commits:</text>
                <text x="160" y="0" class="value">${stats.total_commits}</text>
            </g>
            <g transform="translate(25, 70)">
                <text x="0" y="0" class="stat">Total Repos:</text>
                <text x="160" y="0" class="value">${stats.total_repos} (${stats.private_repos} private)</text>
            </g>
            <g transform="translate(25, 95)">
                <text x="0" y="0" class="stat">Followers:</text>
                <text x="160" y="0" class="value">${stats.followers}</text>
            </g>
            <g transform="translate(260, 20)">
                <text x="0" y="0" class="stat">Total Forks:</text>
                <text x="100" y="0" class="value">${stats.total_forks}</text>
            </g>
        </g>
    </svg>
    `;

    const statsDir = '.github';
    if (!fs.existsSync(statsDir)) {
        fs.mkdirSync(statsDir, { recursive: true });
    }
    fs.writeFileSync(`${statsDir}/stats.svg`, template);
    console.log('✨ SVG generated successfully!');
}

generateStats();
