import config from 'semantic-release-preconfigured-conventional-commits' with { type: "json" };

var dryRun = (process.env.RELEASE_DRY_RUN || "false").toLowerCase() === "true";
var testPypi = (process.env.RELEASE_TEST_PYPI || "false").toLowerCase() === "true";
var pypiUsername = process.env.PYPI_USERNAME;
var pypiPassword = process.env.PYPI_PASSWORD;

var versionCmd = `poetry version ${process.env.NEXT_VERSION}`;
var publishCmd = `poetry publish --build --username ${pypiUsername} --password ${pypiPassword}`;

if (testPypi) {
    // test-pypi repository name is defined in poetry.toml
    publishCmd = publishCmd.replace("--build", "--build --repository pypi-test");
}

if (dryRun) {
    publishCmd = publishCmd.replace("--build", "--build --dry-run");
}

config.plugins.push(
    ["@semantic-release/exec", {
        "prepareCmd" : versionCmd,
        "publishCmd": publishCmd,
    }],
    "@semantic-release/github",
    "@semantic-release/git"
)

if (!dryRun) {
    config.plugins.push(
        ["@semantic-release/github", {
            "assets": [
                { "path": "dist/*" },
            ]
        }],
        ["@semantic-release/git", {
            "assets": [
                "CHANGELOG.md",
                "pyproject.toml"
            ],
            "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
        }]
    );
}

export default config;
