
# Synopsis

Automatically generate and execute Codex prompts to fix Dependabot security alerts in your project.

## Prerequisites

- [Codex CLI](https://github.com/openai/codex/) installed and configured

- A working unit test suite (used to verify fixes)

- A script or command to run Codex (must accept arguments via bash`"$@"` or similar)

- A GitHub personal access token with Dependabot permissions

## Example Usage

Set GITHUB_TOKEN from and via an appropriately secure mechanism.  Then:

    python3 resolve_dependabot_alerts.py \
        --codex .../path/to/run_codex.sh \
        --project CHARM-BDF/charmonator \
        --cmdtest 'npm run test:all'

- --codex — Path to your Codex runner script
- --project — GitHub repo (owner/name)
- --cmdtest — Command used to run your test suite

## Interpreting the result

Read your output!

There are ways for updates to go sideways.  The two most important pieces of messaging to look for are:

- Could not run your tests
- Test counts changed
- Could not resolve all security warnings, and any suggested next steps.

### Example: couldn't run tests

In this run, test suite was missing a required security credential:

    • - Fetched Dependabot alerts; critical/high open alerts were primarily fast-xml-parser, multer, tar, axios, underscore, minimatch, serialize-javascript.
    - Ran baseline npm run test:all: it fails immediately with Tool loaderConfig must have either  "package" or "code" (so there isn’t a reliable “number of tests run” to compare—Mocha aborts before executing the suite).
        - multer -> ^2.1.1
        - sqlite3 -> ^6.0.1 (pulls in tar@7.5.13)
        - openai -> ^6.32.0
        - mocha -> ^11.7.2
        - serialize-javascript -> ^7.0.4 (added as dev dep; mocha still uses its own safe 6.0.2)
    - Verified installed vulnerable packages are now at fixed versions:
        - fast-xml-parser@5.5.8, axios@1.13.6, underscore@1.13.8, minimatch@9.0.9, multer@2.1.1, tar@7.5.13
    - Re-ran npm run test:all: it fails in the same place with the same startup error as before the  security updates
        (so test execution behavior/count is unchanged).

    - package.json
    - package-lock.json

### Example: success

We can see success via 16 passing tests before and after:

    • - Baseline npm run test:all: 16 passing (1m).
        - Post-fix npm run test:all: 16 passing (48s) (same test count).

        Critical/High Dependabot alerts addressed (npm)

        - Updated direct deps:
            - multer -> ^2.1.1
            - axios -> ^1.13.5 (resolved to 1.13.6)
            - sqlite3 -> ^6.0.1 (pulls tar@7.5.13)
            - pdf2pic -> ^3.2.0
            - mocha -> ^11.2.0 (resolved to 11.7.5)
            - mammoth -> ^1.12.0
            - @anthropic-ai/bedrock-sdk -> ^0.26.4
        - Added npm overrides to force patched transitive versions:
            - @aws-sdk/core -> 3.973.24
            - @aws-sdk/xml-builder -> 3.972.15 (brings in fast-xml-parser@5.5.8)
            - underscore -> 1.13.8
            - serialize-javascript -> 7.0.4
            - glob -> 10.5.0
            - tar-fs -> 3.1.2
            - cross-spawn -> 7.0.6

## When and how this works

The concept of automatic vulnerability scanning is predicated on having a language and package manager popular enough to be getting CVE and package metadata curation.  Out of the box, codex understands the mainstream package managers with security metadata.  Here's an example of what you will see while this script runs:

    . . .
    $ npm view @aws-sdk/xml-builder version
    3.972.15
    ✓ • 370ms
    
    $ npm pkg set overrides.'@aws-sdk/core'='3.973.24' overrides.'@aws-sdk/xml-builder'='3.972.15'
    ✓ • 145ms
    
    $ npm install
    
    > charmonator@1.0.0 postinstall
    > mkdir -p test/data && touch test/data/05-versions-space.pdf  # pdf-parse workaround
    
    
    added 7 packages, changed 51 packages, and audited 740 packages in 3s
    
    70 packages are looking for funding
    run `npm fund` for details
    
    34 vulnerabilities (3 low, 24 moderate, 7 high)
    
    To address issues that do not require attention, run:
    npm audit fix
    
    To address all issues (including breaking changes), run:
    npm audit fix --force
    
    Run `npm audit` for details.
    ✓ • 2.84s
    
    $ npm audit --json | jq '.vulnerabilities | to_entries[] | select(.value.severity=="critical"
        or .value.severity=="high") | {name:.key, severity:.value.severity, range:.value.range,
        fixAvailable:.value.fixAvailable}'
    {
    "name": "cross-spawn",
    "severity": "high",
    "range": "<6.0.6",
    "fixAvailable": true
    }
    . . .

## Double checking your result

Because Github does not currently provide a local double of its repository scanning capability, it is difficult to approximate how it will look at your repository without actually pushing it.  So instead, use this process:

(1) Push your repository to your official branch

(2) Go to your project page on github | Security | Dependabot | Vulnerabilities

(3) Check that High and Creticial severity issues have been resolved

## Making the Github Token

Here is how to use the "fine-grained" (as opposed to "classic") token mechainsm:

(1) Log in to github.com

(2) Select: Settings | Developer Settings | Personal access tokens | Fine-grained tokens

(3) Fill out:

| Setting | Value |
|---|---|
| Token name | to your liking |
| Expiration | to your liking |
| Repository access | All repositories |    
| Permissions | enable "Dependabot alerts" and "Metadata" |

(4) Select: Generate token

(5) Store the token in an appropriatley secure mechanism.

## Example of a run_codex.sh script

In case you are wondering why some of people are lucky enough to need a script to run codex:

    #!/bin/bash
    URL=\"${AZURE_OPENAI_ENDPOINT%/}/openai\"
    codex \
            --config model_provider='"azure"' \
            --config model='"gpt-5.2"' \
            --config model_providers.azure.name='"Azure"' \
            --config model_providers.azure.base_url="${URL}" \
            --config model_providers.azure.env_key='"AZURE_OPENAI_API_KEY"' \
            --config 'model_providers.azure.query_params={api-version="2025-04-01-preview"}' \
            --config model_providers.azure.wire_api='"responses"' \
            "$@"

## Known issues

- The severity level is currently hard-coded to resolve high/critical severity issues.
