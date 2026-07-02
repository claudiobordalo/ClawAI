from clawai.chat.intent_classifier import IntentClassifier
from clawai.ai.router import ModelRole


def test_intent_classifier_routes_engineering_requests_to_agent():
    classifier = IntentClassifier()
    decision = classifier.classify("corrija o fluxo de login")

    assert decision.use_agent is True
    assert decision.role == ModelRole.DEFAULT
    assert "engenharia" in decision.reason


def test_intent_classifier_detects_image_file():
    classifier = IntentClassifier()
    decision = classifier.classify("analise a imagem", file="caminho/imagem.png")

    assert decision.use_agent is False
    assert decision.role == ModelRole.VISION
    assert decision.reason == "arquivo visual"