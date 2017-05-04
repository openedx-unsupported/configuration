Configuration Pull Request
---

Make sure that the following steps are done before merging:

  - [ ] A DevOps team member has approved the PR.
  - [ ] Are you adding any new default values that need to be overridden when this change goes live? If so:
    - [ ] Update the appropriate internal repo (be sure to update for all our environments)
    - [ ] If you are updating a secure value rather than an internal one, file a DEVOPS ticket with details.
    - [ ] Add an entry to the CHANGELOG.
  - [ ] Have you performed the proper testing specified on the [Ops Ansible Testing Checklist](https://openedx.atlassian.net/wiki/display/EdxOps/Ops+Ansible+Testing+Checklist)?
