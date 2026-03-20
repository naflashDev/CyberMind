from src.app.services.code_analysis.scanner import CodeScanner


def test_group_and_sort_vulnerabilities_basic():
    '''
    @brief Unit test: grouping identical vulnerabilities (happy path).

    Happy Path: duplicate vulnerabilities should be grouped into a single entry and ordered by severity.
    '''
    scanner = CodeScanner()
    vulns = [
        {"filename": "a.py", "line": 10, "severity": "HIGH", "cwe": "CWE-79", "description": "XSS found", "explanation": "Exp 1"},
        {"filename": "b.py", "line": 20, "severity": "HIGH", "cwe": "CWE-79", "description": "XSS found", "explanation": "Exp 1"},
        {"filename": "c.py", "line": 5, "severity": "MEDIUM", "cwe": "CWE-89", "description": "SQLi", "explanation": "Exp 2"},
    ]

    grouped = scanner._group_and_sort_vulnerabilities(vulns)

    # Expect two groups: the HIGH XSS group (count 2) and the MEDIUM SQLi (count 1)
    assert isinstance(grouped, list)
    assert len(grouped) == 2

    # First group should be the HIGH one with count 2
    first = grouped[0]
    assert first['severity_rank'] >= grouped[1]['severity_rank']
    assert first['count'] == 2
    assert any('a.py' in loc for loc in [o['filename'] for o in first['occurrences']])

    second = grouped[1]
    assert second['count'] == 1
    assert second['description'].lower().startswith('sqli')
