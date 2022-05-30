Usage
#####

Create image:

   -  This must be run from the root of the configuration repository
   -  ``docker build -f docker/build/github-actions-runner/Dockerfile . -t openedx/github-actions-runner``

Start the container with this:

``docker run -ti -v /var/lib/docker.sock:/var/lib/docker.sock -e GITHUB_ACCESS_TOKEN=xxxxxxxx -e GITHUB_ORGANIZATION=abc openedx/github-actions-runner``
