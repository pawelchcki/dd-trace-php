

target "package" {
    dockerfile = "dockerfiles/packaging/Dockerfile"
    target = "export"
    output = ["build/package"]
}

target "extensions" {
    inherits = ["package"]
    output = ["build/exts/"]
    target = "extensions"
}

target "build-5-4" {
    inherits = ["package"]
    target = "php-5.4-debug"
}
