# CodeFuse DB Diff (auto-generated)

- linux DB: `dataset/codefuse-db-linux/coref_java_src.db`
- mac DB:   `dataset/codefuse-db-mac/coref_java_src.db`

## Table set
- linux tables: 130, mac tables: 130
- table sets identical

## Tables with differing row counts
| table | linux | mac | delta |
|---|---|---|---|
| constructor_invocation | 3683 | 5172 | 1489 |
| method_access_expression_with_type | 32371 | 4500 | -27871 |
| method_access_expression_without_type | 39455 | 67326 | 27871 |
| new_expression | 6026 | 4537 | -1489 |
| reference_type | 1840 | 1111 | -729 |

## reference_type FQN categories
| category | linux | mac | delta |
|---|---|---|---|
| total_nonnull | 1840 | 1111 | -729 |
| java.* | 842 | 38 | -804 |
| javax.* | 32 | 25 | -7 |
| jakarta.* | 0 | 0 | 0 |
| org.owasp.* | 891 | 891 | 0 |
| simple_name | 61 | 144 | 83 |

## Key sink/source/relay FQN presence
| qualified_name | linux | mac |
|---|---|---|
| java.lang.String | 1 | 0 |
| java.lang.StringBuilder | 1 | 0 |
| java.lang.StringBuffer | 1 | 0 |
| java.util.List | 5 | 2 |
| java.lang.Runtime | 1 | 0 |
| java.lang.ProcessBuilder | 1 | 0 |
| java.sql.Statement | 1 | 1 |
| java.sql.Connection | 1 | 1 |
| javax.naming.directory.DirContext | 1 | 1 |
| javax.xml.xpath.XPath | 1 | 1 |

## method_access_expression with_type vs without_type
| build | with_type | without_type | with_type % |
|---|---|---|---|
| linux | 32371 | 39455 | 45.1% |
| mac | 4500 | 67326 | 6.3% |

- linux-only FQN list written to `reports/data/linux_only_fqn.txt` (819 entries)

## Verdict
- mac with_type / linux with_type = 13.9% (threshold >= 95%) -> FAIL
- mac java.* reference types = 38 (threshold >= 200) -> FAIL
- **FAIL**
- ACTION: mac build lost the JDK type model; DO NOT use it for evaluation. Rebuild with JAVA_HOME/JDK on the type-resolution path.
