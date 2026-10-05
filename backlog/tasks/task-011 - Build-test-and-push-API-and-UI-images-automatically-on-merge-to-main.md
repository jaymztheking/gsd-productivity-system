---
id: TASK-011
title: 'Build, test and push API and UI images automatically on merge to main'
status: To Do
assignee: []
created_date: '2026-10-05 03:56'
labels:
  - ci
  - infra
dependencies: []
references:
  - k8s/api/deployment.yaml
  - k8s/ui/deployment.yaml
  - api/Dockerfile
  - ui/Dockerfile
  - README.md
priority: medium
type: chore
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
There is no CI/CD: merging to main changes nothing on the cluster. Deploying today means someone remembers to build ARM64 images by hand with docker buildx, push them to Docker Hub as jaymztheking/gsd-api:latest and jaymztheking/gsd-ui:latest, and restart the deployments. This surfaced after TASK-009 merged (2026-10-04) and was assumed to be live when it was not. Every image is a mutable :latest tag, so there is also no record of which commit is running and no clean way to roll back.

This task covers the build half: every merge to main should produce tested, pushed images traceable to a commit. Rolling them out to the cluster automatically is a separate task, because the k3s cluster (Raspberry Pi, ARM64) is on the home network and GitHub-hosted runners cannot reach it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A GitHub Actions workflow runs on every push to main and on pull requests targeting main
- [ ] #2 The workflow runs the API unit tests that need no live services (test_auth, test_next_action_tags, test_routine and any later ones of that kind) and a UI production build; a failure fails the workflow and stops any image push
- [ ] #3 On main only, linux/arm64 images for api and ui are built and pushed to Docker Hub, each tagged with the commit SHA and with latest
- [ ] #4 Pull request runs build the images to prove they build but never push
- [ ] #5 Docker Hub credentials come from GitHub repository secrets and never appear in the workflow file or logs
- [ ] #6 The README deployment section describes the workflow, the required secrets, and how to roll back by pointing a deployment at an earlier SHA tag
<!-- AC:END -->
