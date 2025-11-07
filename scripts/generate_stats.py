#!/usr/bin/env python3
import os
import json
import requests
from github import Github

def get_github_stats():
    token = os.getenv('GH_TOKEN')
    if not token:
        print("❌ Error: GH_TOKEN environment variable not set")
        print("   Usage: export GH_TOKEN=your_github_token")
        return None
    
    try:
        print("🔍 Fetching GitHub stats for A4GOD-AMHG...\n")
        
        g = Github(token, per_page=100)
        user = g.get_user('A4GOD-AMHG')
        
        stats = {
            'followers': user.followers,
            'following': user.following,
            'public_repos': 0,
            'private_repos': 0,
            'total_repos': 0,
            'total_commits': 0,
            'top_languages': {},
            'total_stars': 0,
            'total_forks': 0
        }
        
        languages = {}
        total_repos = 0
        public_repos = 0
        private_repos = 0
        total_stars = 0
        total_forks = 0
        
        print("📦 Fetching repositories...")
        for repo in user.get_repos(type='all'):
            total_repos += 1
            total_stars += repo.stargazers_count
            total_forks += repo.forks_count
            
            if repo.private:
                private_repos += 1
            else:
                public_repos += 1
            
            if repo.language:
                languages[repo.language] = languages.get(repo.language, 0) + 1
        
        print(f"✅ Found {total_repos} repos ({public_repos} public, {private_repos} private)")
        
        print("📝 Fetching total commits using GraphQL...")
        
        query = """
        query($userName:String!) {
          user(login: $userName) {
            repositories(first: 100, affiliations: [OWNER, COLLABORATOR]) {
              nodes {
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
        """
        
        total_commits = 0
        try:
            url = "https://api.github.com/graphql"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.post(
                url,
                json={"query": query, "variables": {"userName": "A4GOD-AMHG"}},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['user']:
                    repos = data['data']['user']['repositories']['nodes']
                    for repo in repos:
                        if repo and repo.get('object') and repo['object'].get('history'):
                            total_commits += repo['object']['history']['totalCount']
                    print(f"✅ Total commits: {total_commits}")
                else:
                    print("⚠️  Could not parse GraphQL response")
            else:
                print(f"⚠️  GraphQL request failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Could not fetch commits: {e}")
            print("   Continuing with stats...")
        
        sorted_langs = dict(sorted(languages.items(), key=lambda x: x[1], reverse=True)[:8])
        
        stats['public_repos'] = public_repos
        stats['private_repos'] = private_repos
        stats['total_repos'] = total_repos
        stats['total_commits'] = total_commits
        stats['total_stars'] = total_stars
        stats['total_forks'] = total_forks
        stats['top_languages'] = sorted_langs
        
        return stats
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def generate_markdown(stats):
    if not stats:
        return ""
    
    markdown = f"""
### 📈 GitHub Statistics
<div align="center">

![Total Commits](https://img.shields.io/badge/Total%20Commits-{stats['total_commits']}-7F7DFF?style=for-the-badge&logo=git)
![Public Repos](https://img.shields.io/badge/Public%20Repos-{stats['public_repos']}-brightgreen?style=for-the-badge&logo=github)
![Private Repos](https://img.shields.io/badge/Private%20Repos-{stats['private_repos']}-yellow?style=for-the-badge&logo=github)
![Followers](https://img.shields.io/badge/Followers-{stats['followers']}-ff69b4?style=for-the-badge&logo=github)
![Total Stars](https://img.shields.io/badge/Total%20Stars-{stats['total_stars']}-orange?style=for-the-badge&logo=github)
![Total Forks](https://img.shields.io/badge/Total%20Forks-{stats['total_forks']}-blueviolet?style=for-the-badge&logo=github)

#### 🔝 Most Used Languages
"""
    
    for lang, count in stats['top_languages'].items():
        markdown += f"- **{lang}**: {count} repositories\n"
    
    markdown += "\n</div>\n"
    
    return markdown

if __name__ == "__main__":
    stats = get_github_stats()
    if stats:
        print("\n" + "="*50)
        print("📊 STATS SUMMARY")
        print("="*50)
        print(json.dumps(stats, indent=2))
        print("\n" + "="*50)
        print("📝 MARKDOWN OUTPUT")
        print("="*50)
        markdown = generate_markdown(stats)
        print(markdown)
        print("✨ Stats generated successfully!")
    else:
        print("❌ Failed to generate stats")
