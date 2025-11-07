#!/usr/bin/env python3
import os
import json
from github import Github

def get_github_stats():
    token = os.getenv('GH_TOKEN')
    if not token:
        print("Error: GH_TOKEN environment variable not set")
        return None
    
    try:
        g = Github(token)
        user = g.get_user('A4GOD-AMHG')
        
        stats = {
            'followers': user.followers,
            'following': user.following,
            'public_repos': user.public_repos,
            'total_repos': 0,
            'total_commits': 0,
            'top_languages': {},
            'total_stars': 0,
            'total_forks': 0
        }
        
        languages = {}
        total_repos = 0
        total_commits = 0
        total_stars = 0
        total_forks = 0
        
        for repo in user.get_repos():
            total_repos += 1
            total_stars += repo.stargazers_count
            total_forks += repo.forks_count
            
            try:
                commits = repo.get_commits().totalCount
                total_commits += commits
            except Exception as e:
                print(f"Warning: Could not get commits for {repo.name}: {e}")
            
            if repo.language:
                languages[repo.language] = languages.get(repo.language, 0) + 1
        
        sorted_langs = dict(sorted(languages.items(), key=lambda x: x[1], reverse=True)[:8])
        
        stats['total_repos'] = total_repos
        stats['total_commits'] = total_commits
        stats['total_stars'] = total_stars
        stats['total_forks'] = total_forks
        stats['top_languages'] = sorted_langs
        
        return stats
    
    except Exception as e:
        print(f"Error: {e}")
        return None

def generate_markdown(stats):
    if not stats:
        return ""
    
    markdown = f"""
### 📈 GitHub Statistics
<div align="center">

![Followers](https://img.shields.io/badge/Followers-{stats['followers']}-blue?style=for-the-badge&logo=github)
![Following](https://img.shields.io/badge/Following-{stats['following']}-blue?style=for-the-badge&logo=github)
![Total Repos](https://img.shields.io/badge/Total%20Repos-{stats['total_repos']}-brightgreen?style=for-the-badge&logo=github)
![Total Stars](https://img.shields.io/badge/Total%20Stars-{stats['total_stars']}-yellow?style=for-the-badge&logo=github)
![Total Forks](https://img.shields.io/badge/Total%20Forks-{stats['total_forks']}-orange?style=for-the-badge&logo=github)
![Total Commits](https://img.shields.io/badge/Total%20Commits-{stats['total_commits']}-purple?style=for-the-badge&logo=git)

#### Most Used Languages
"""
    
    for lang, count in stats['top_languages'].items():
        markdown += f"![{lang}](https://img.shields.io/badge/{lang}-{count}%20repos-green?style=for-the-badge)\n"
    
    markdown += "\n</div>\n"
    
    return markdown

if __name__ == "__main__":
    stats = get_github_stats()
    if stats:
        print(json.dumps(stats, indent=2))
        markdown = generate_markdown(stats)
        print("\n--- Generated Markdown ---")
        print(markdown)
    else:
        print("Failed to generate stats")
