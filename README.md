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
      "tokens": {
        {
          "user_name": "github_pat_**************************************************",
          "org_name": "github_pat_**************************************************"
        }
      }
    }
  }
}
```
- Replace "..." with org or user as necessary to determine which group of repos to download.
- Replace "user_name" with specific user, if any private repos of users need to be listed.
- Replace "org_name" with specific user, if any private repos of orgs need to be listed.
