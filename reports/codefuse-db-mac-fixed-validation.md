# CodeFuse macOS Fixed DB Validation

## 1. Goal

Rebuild the macOS CodeFuse/Sparrow Java database with a correct JDK `Contents/Home`, then verify the JDK type model, DB parity against Linux, and VEP regression behavior.

## 2. Environment

- HEAD: `877f5c0 fix(codefuse): prevent macOS builds with invalid JAVA_HOME`
- JAVA_HOME: `/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home`
- Java: OpenJDK 21.0.11
- Sparrow: 2.1.0
- `/usr/libexec/java_home`: still not registered; treated as discovery evidence only
- DB output: `dataset/codefuse-db-mac-fixed/coref_java_src.db`

## 3. Mini Probe Final Check

| metric | value |
|---|---:|
| reference_type `java.*` | 6 |
| method_access_expression_with_type | 6 |
| method_access_expression_without_type | 1 |
| java.lang.String | 1 |
| java.lang.StringBuilder | 1 |
| java.lang.Runtime | 1 |
| java.util.List | 1 |

## 4. Full DB Rebuild Command

```bash
JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
PATH="$JAVA_HOME/bin:$PATH"
sparrow database create -s dataset/benchmark/src/main/java -lang java -o dataset/codefuse-db-mac-fixed
```

- Build start: `2026-06-18 00:52:56 CST`
- Build end: `2026-06-18 00:55:29 CST`
- Extractor status: success
- Files analyzed: 2766 Java files

## 5. DB Sanity Gate Results

- Single DB gate: PASS (`reports/codefuse-db-mac-fixed-gate.md`)
- Linux vs fixed Mac diff: PASS (`reports/codefuse-db-diff-mac-fixed.md`)
- Table sets: identical, 130 tables each
- Differing table row counts: none

## 6. Linux vs Old Mac vs Fixed Mac Comparison

| metric | Linux | Old Mac | Fixed Mac |
|---|---:|---:|---:|
| reference_type java.* | 842 | 38 | 842 |
| reference_type org.owasp.* | 891 | 891 | 891 |
| reference_type javax.* | 32 | 25 | 32 |
| method_access_with_type | 32371 | 4500 | 32371 |
| method_access_without_type | 39455 | 67326 | 39455 |

## 7. Key Type Recovery

| type | Linux | Old Mac | Fixed Mac |
|---|---:|---:|---:|
| java.lang.String | 1 | 0 | 1 |
| java.lang.StringBuilder | 1 | 0 | 1 |
| java.lang.StringBuffer | 1 | 0 | 1 |
| java.lang.Runtime | 1 | 0 | 1 |
| java.lang.ProcessBuilder | 1 | 0 | 1 |
| java.util.List | 5 | 2 | 5 |

`java.util.List` is counted with generic renderings such as `java.util.List<java.lang.String>`.

## 8. VEP Regression Result

| build | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Linux | 1414 | 553 | 0 | 0.7189 | 1.0000 | 0.8364 |
| Old Mac | 1347 | 545 | 67 | 0.7119 | 0.9526 | 0.8149 |
| Fixed Mac | 1414 | 553 | 0 | 0.7189 | 1.0000 | 0.8364 |

Old Mac FN distribution from existing experiment outputs: CWE-022=13, CWE-078=25, CWE-079=18, CWE-089=5, CWE-501=5, CWE-643=1. Fixed Mac has FN=0 for all 11 CWE runs.

## 9. Conclusion

Confirmed:

- Fixed Mac DB restores the JDK type model: `java.*` is 842, matching Linux exactly.
- Fixed Mac `method_access_expression_with_type` is 32371, matching Linux exactly.
- The old Mac 67 FN regression disappears: fixed Mac FN total is 0 and recall is 1.0000.
- The fixed Mac DB can be used for non-formal local validation and cross-checking.

Likely:

- The 6/12 old Mac DB regression was caused by the same invalid Homebrew keg-prefix `JAVA_HOME`, because fixed JDK discovery restores DB and VEP metrics to Linux parity.

Possible:

- Future macOS/JDK/Sparrow version changes could reintroduce discovery drift if the environment is not locked and gated.

Ruled out:

- Apple Silicon/module-image parsing is not the cause in this environment; the same Sparrow build reads JDK21 modules correctly once `JAVA_HOME` is correct.

Unknown:

- Whether every future macOS developer machine has the same Homebrew path layout without running the setup helper.

Answers:

1. Fixed Mac DB restores the JDK type model: yes.
2. Old Mac 67 FN disappears: yes, fixed Mac FN=0.
3. Fixed Mac DB can be used for non-formal local validation: yes.
4. Formal benchmark reporting should still prefer Linux DB as oracle: yes.
5. Keep old Mac DB as a regression fixture: yes, it is useful as a negative fixture for the DB gate.

## 10. Remaining Risks

- Sparrow version should remain locked; this validation used Sparrow 2.1.0.
- The full DB is intentionally not committed.
- macOS Java symlink registration remains optional; correct `JAVA_HOME` is sufficient.
- Linux remains the formal benchmark oracle even though fixed Mac now matches it.
