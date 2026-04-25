from src.services import extract_message_id, extract_text_from_message


def test_extract_text_from_plain_message():
    assert extract_text_from_message({"conversation": "oi"}) == "oi"


def test_extract_text_from_wrapped_message():
    payload = {"ephemeralMessage": {"message": {"extendedTextMessage": {"text": "teste"}}}}
    assert extract_text_from_message(payload) == "teste"


def test_extract_message_id_prefers_key_id():
    message_data = {"key": {"id": "ABC", "remoteJid": "555@s.whatsapp.net"}, "message": {"conversation": "oi"}}
    assert extract_message_id(message_data) == "ABC"
