name: Docker Compose Actions Workflow
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@master
    - name: Build the stack
      run: docker-compose -f dockerfiles/frameworks/symfony.yml build
