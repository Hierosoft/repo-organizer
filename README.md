# repo-organizer
Maintain a local copy of all repos for specified user(s) and/or organization(s).

## Example configuration:
~/.config/repo-organizer/settings.json example:
```json
{
  "sources": {
    "github": {
	  "orgs": ["traincontrolsystems"],
	  "users": ["TCSDCC"]
    }
  }
}
```