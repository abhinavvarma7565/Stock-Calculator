import pytest

from app import app

good = dict(stksymbol='abc', allotment='100', iniprice='10', fnlprice='15',
            buycmm='5', sellcmm='5', cptlgain='15')


@pytest.fixture
def client():
    app.testing = True
    return app.test_client()


def test_form_page(client):
    r = client.get('/')
    assert r.status_code == 200
    assert b'name="allotment"' in r.data


def test_report(client):
    r = client.post('/post', data=good)
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert 'ABC' in html
    assert '$73.50' in html       # tax
    assert '7350' not in html     # the old 100x tax bug
    assert '$416.50' in html      # net profit
    assert '38.44%' in html       # roi
    assert '$10.10' in html       # break even
    assert '$1,083.50' in html    # total cost


def test_decimals_and_commas(client):
    r = client.post('/post', data={**good, 'iniprice': '10.50', 'buycmm': '4.95', 'allotment': '1,000'})
    assert r.status_code == 200


def test_loss(client):
    r = client.post('/post', data={**good, 'iniprice': '15', 'fnlprice': '10'})
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert '-$510.00' in html     # net loss
    assert '$15.10' in html       # break even
    assert 'loss after commissions' in html


@pytest.mark.parametrize('field, value, msg', [
    ('allotment', '', 'Number of shares is required'),
    ('allotment', '0', 'Number of shares must be more than 0'),
    ('allotment', 'abc', 'Number of shares must be a number'),
    ('iniprice', '-3', 'Initial share price must be more than 0'),
    ('fnlprice', 'nan', 'Final share price must be a number'),
    ('buycmm', 'inf', 'Buy commission must be a number'),
    ('sellcmm', '-1', 'Sell commission must be at least 0'),
    ('cptlgain', '101', 'Capital gain tax rate must be 100 or less'),
    ('stksymbol', 'bad symbol!', 'Stock symbol must be'),
    ('stksymbol', '', 'Stock symbol must be'),
])
def test_bad_input(client, field, value, msg):
    r = client.post('/post', data={**good, field: value})
    assert r.status_code == 400
    assert msg in r.get_data(as_text=True)


def test_zero_final_price_is_ok(client):
    # stock went to nothing
    r = client.post('/post', data={**good, 'fnlprice': '0'})
    assert r.status_code == 200


def test_missing_field(client):
    data = {k: v for k, v in good.items() if k != 'cptlgain'}
    r = client.post('/post', data=data)
    assert r.status_code == 400
    assert 'Capital gain tax rate is required' in r.get_data(as_text=True)


def test_all_errors_at_once_and_values_kept(client):
    r = client.post('/post', data={**good, 'allotment': 'x', 'iniprice': '-1'})
    html = r.get_data(as_text=True)
    assert 'Number of shares must be a number' in html
    assert 'Initial share price must be more than 0' in html
    assert 'value="15"' in html   # the good fields are still filled in


def test_input_is_escaped(client):
    r = client.post('/post', data={**good, 'stksymbol': '"><script>alert(1)</script>'})
    assert r.status_code == 400
    assert b'<script>alert(1)</script>' not in r.data


def test_get_on_post_url_goes_home(client):
    r = client.get('/post')
    assert r.status_code == 302
