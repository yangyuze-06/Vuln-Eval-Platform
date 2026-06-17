# CodeFuse/Sparrow macOS JDK Setup

## Why this matters

Sparrow database creation needs more than a runnable `java` command. It also
needs the JDK runtime module image to build the JDK type model. If `JAVA_HOME`
points to a Homebrew keg prefix instead of the real JDK `Contents/Home`,
Sparrow can run but cannot find `lib/modules` or `jmods`.

That failure causes:

- missing `java.*` fully qualified names in `reference_type`;
- `method_access_expression_with_type` degrading into
  `method_access_expression_without_type`;
- false negatives in taint rules that depend on JDK receiver types or sinks.

## Correct JAVA_HOME

BAD:

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@17
```

GOOD:

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
```

GOOD:

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
```

## Recommended setup

```bash
./scripts/setup_macos_codefuse_jdk.sh --version 21 --print-env
```

Then export the printed values in the shell used for `sparrow database create`:

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"
```

## Optional system registration

Homebrew recommends registering its JDK bundle with macOS system Java wrappers:

```bash
sudo ln -sfn /opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk \
  /Library/Java/JavaVirtualMachines/openjdk-21.jdk
```

Notes:

- `sudo` requires explicit user confirmation.
- Project scripts do not run `sudo` unless `--apply-symlink` is passed.
- The symlink is optional for CodeFuse as long as `JAVA_HOME` points to
  `Contents/Home`.

## Pre-build gate

Run this before every macOS CodeFuse DB build:

```bash
python3 scripts/check_codefuse_java_env.py --require-version 21 --require-modules
```

The command must PASS before building a DB for evaluation.

## Mini probe

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"
sparrow database create -s reports/data/repro -lang java -o /tmp/vep-mini-db-jdk21
sqlite3 /tmp/vep-mini-db-jdk21/coref_java_src.db \
  "SELECT qualified_name FROM reference_type WHERE qualified_name LIKE 'java.%' ORDER BY qualified_name;"
```

Expected evidence includes JDK FQNs such as:

```text
java.lang.String
java.lang.StringBuilder
java.lang.Runtime
java.util.List
```

Depending on generic rendering, `java.util.List` may appear as
`java.util.List<java.lang.String>`.

## Full DB rebuild policy

Full macOS DB rebuilds must be a separate phase. After rebuilding, run:

```bash
python3 scripts/diagnose_codefuse_db_diff.py \
  --linux dataset/codefuse-db-linux/coref_java_src.db \
  --mac dataset/codefuse-db-mac-fixed/coref_java_src.db \
  --out docs/reports_for_java_database/codefuse-db-diff-mac-fixed.md
```

Do not use the rebuilt DB for evaluation until it passes the DB gate and the
JDK `java.*` counts are reviewed.
