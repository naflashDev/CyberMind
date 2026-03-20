from app.services.code_analysis.scanner import CodeScanner


def test_explain_with_injected_callable():
    s = CodeScanner(llm=lambda text: 'injected callable')
    assert s._explain_with_llm('x') == 'injected callable'


def test_explain_with_injected_object():
    class Provider:
        def explain_vulnerability(self, t):
            return 'object explanation'

    s = CodeScanner(llm=Provider())
    assert s._explain_with_llm('x') == 'object explanation'
