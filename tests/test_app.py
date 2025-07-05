from http import HTTPStatus

from fastapi.testclient import TestClient

from smugmug_photo_selector.app import app


def test_read_root_deve_retornar_mensagem_bem_vindo():
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'Welcome to the SmugMug Photo Selector API!'
    }
