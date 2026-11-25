import pytest


def test_frontend_is_served_without_hiding_api(api):
    response = api("GET", "/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<html lang="bg">' in response.text
    assert "/static/styles.css" in response.text
    assert "/static/app.js" in response.text
    assert api("GET", "/health").json() == {"status": "ok"}
    assert api("GET", "/print-models").json() == []
    assert api("GET", "/docs").status_code == 200


@pytest.mark.parametrize("path, content_type", [
    ("/static/styles.css", "text/css"),
    ("/static/app.js", "javascript"),
])
def test_frontend_assets_are_accessible(api, path, content_type):
    response = api("GET", path)
    assert response.status_code == 200
    assert content_type in response.headers["content-type"]


@pytest.mark.parametrize("path", [
    "/static/../backend/database.py",
    "/static/%2e%2e/backend/database.py",
    "/static/%2e%2e/print_models.db",
    "/static/missing.js",
])
def test_static_files_do_not_expose_backend_or_database(api, path):
    assert api("GET", path).status_code == 404
