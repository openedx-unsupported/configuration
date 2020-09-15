Configuration Pull Request
---

Make sure that the following steps are done before merging:

  - [ ] A DevOps team member has approved the PR if it is code shared across multiple services and you don't own all of the services.
  - [ ] Are you adding any new default values that need to be overridden when this change goes live? If so:
    - [ ] Update the appropriate internal repo (be sure to update for all our environments)
    - [ ] If you are updating a secure value rather than an internal one, file a DEVOPS ticket with details.
    - [ ] Add an entry to the CHANGELOG.
  - [ ] If you are making a complicated change, have you performed the proper testing specified on the [Ops Ansible Testing Checklist](https://openedx.atlassian.net/wiki/display/EdxOps/Ops+Ansible+Testing+Checklist)?  Adding a new variable does not require the full list (although testing on a sandbox is a great idea to ensure it links with your downstream code changes).
  - [ ] Think about how this change will affect Open edX operators.  Have you updated the wiki page for the next Open edX release?
