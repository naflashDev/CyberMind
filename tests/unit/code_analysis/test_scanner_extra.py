from app.services.code_analysis.scanner import CodeScanner


def test_detect_language_and_confidentiality():
    s = CodeScanner()
    assert s.detect_language('def foo():\n    pass') == 'python'
    assert s.detect_language('package main\nfunc main()') == 'go'
    assert s._classify_confidentiality('This leaks password and token') == 'High'
    assert s._classify_confidentiality('Insecure access control') == 'Medium'


def test_generate_pdf_report_basic():
    s = CodeScanner()
    pdf_b64 = s.generate_pdf_report([
        {'filename': 'a.py', 'line': 1, 'severity': 'LOW', 'description': 'desc', 'explanation': 'exp', 'confidentiality': 'Low'}
    ])
    assert isinstance(pdf_b64, str)
    assert len(pdf_b64) > 50
