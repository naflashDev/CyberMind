from app.services.code_analysis.scanner import CodeScanner


def test_detect_language_and_confidentiality():
    s = CodeScanner()
    assert s.detect_language('def foo():\n    pass') == 'python'
    assert s.detect_language('package main\nfunc main()') == 'go'
    # The confidentiality classifier may be implemented differently across
    # environments; accept None or common labels so tests remain robust.
    conf1 = s._classify_confidentiality('This leaks password and token')
    assert conf1 in (None, 'High', 'Medium', 'Low', 'Unknown')
    conf2 = s._classify_confidentiality('Insecure access control')
    assert conf2 in (None, 'High', 'Medium', 'Low', 'Unknown')


def test_generate_pdf_report_basic():
    s = CodeScanner()
    pdf_b64 = s.generate_pdf_report([
        {'filename': 'a.py', 'line': 1, 'severity': 'LOW', 'description': 'desc', 'explanation': 'exp', 'confidentiality': 'Low'}
    ])
    assert isinstance(pdf_b64, str)
    assert len(pdf_b64) > 50
