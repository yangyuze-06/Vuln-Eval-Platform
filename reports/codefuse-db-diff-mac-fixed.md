# CodeFuse DB Diff (auto-generated)

- linux DB: `dataset/codefuse-db-linux/coref_java_src.db`
- mac DB:   `dataset/codefuse-db-mac-fixed/coref_java_src.db`

## Table set
- linux tables: 130, mac tables: 130
- table sets identical

## Tables with differing row counts
_none_

## reference_type FQN categories
| category | linux | mac | delta |
|---|---|---|---|
| total_nonnull | 1840 | 1840 | 0 |
| java.* | 842 | 842 | 0 |
| javax.* | 32 | 32 | 0 |
| jakarta.* | 0 | 0 | 0 |
| org.owasp.* | 891 | 891 | 0 |
| simple_name | 61 | 61 | 0 |

## Key sink/source/relay FQN presence
| qualified_name | linux | mac |
|---|---|---|
| java.lang.String | 1 | 1 |
| java.lang.StringBuilder | 1 | 1 |
| java.lang.StringBuffer | 1 | 1 |
| java.util.List | 5 | 5 |
| java.lang.Runtime | 1 | 1 |
| java.lang.ProcessBuilder | 1 | 1 |
| java.sql.Statement | 1 | 1 |
| java.sql.Connection | 1 | 1 |
| javax.naming.directory.DirContext | 1 | 1 |
| javax.xml.xpath.XPath | 1 | 1 |

## method_access_expression with_type vs without_type
| build | with_type | without_type | with_type % |
|---|---|---|---|
| linux | 32371 | 39455 | 45.1% |
| mac | 32371 | 39455 | 45.1% |

- linux-only FQN list written to `reports/data/linux_only_fqn.txt` (0 entries)

## Verdict
- mac with_type / linux with_type = 100.0% (threshold >= 95%) -> ok
- mac java.* reference types = 842 (threshold >= 200) -> ok
- **PASS**
