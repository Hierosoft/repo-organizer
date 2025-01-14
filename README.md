# repo-organizer
Maintain a local copy of all repos for specified user(s) and/or organization(s).

## Example configuration:
You must manually create ~/.config/repo-organizer/settings.json like:
```json
{
  "sources": {
    "github": {
	  "orgs": ["..."],
	  "users": ["..."],
	  "token": "github_pat_**************************************************"
    }
  }
}
```