"""API tests for portfolio and holding lifecycle."""
import pytest


def test_portfolio_crud_flow(client):
    create_payload = {
        "name": "API Test Portfolio",
        "description": "created by pytest",
        "initial_capital": 10000,
        "holdings": [],
    }
    create_resp = client.post("/api/v1/portfolios/", json=create_payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    portfolio_id = created["id"]
    assert created["name"] == "API Test Portfolio"
    assert created["cash_balance"] == 10000
    assert created["is_active"] is True

    list_resp = client.get("/api/v1/portfolios/")
    assert list_resp.status_code == 200
    portfolios = list_resp.json()
    assert any(item["id"] == portfolio_id for item in portfolios)

    update_payload = {
        "name": "API Test Portfolio Updated",
        "description": "updated by pytest",
        "is_active": False,
    }
    update_resp = client.put(f"/api/v1/portfolios/{portfolio_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["name"] == "API Test Portfolio Updated"
    assert updated["description"] == "updated by pytest"
    assert updated["is_active"] is False

    get_resp = client.get(f"/api/v1/portfolios/{portfolio_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == portfolio_id
    assert fetched["name"] == "API Test Portfolio Updated"

    delete_resp = client.delete(f"/api/v1/portfolios/{portfolio_id}")
    assert delete_resp.status_code == 204

    missing_resp = client.get(f"/api/v1/portfolios/{portfolio_id}")
    assert missing_resp.status_code == 404


def test_holding_lifecycle_and_cash_adjustment(client):
    create_portfolio_resp = client.post(
        "/api/v1/portfolios/",
        json={
            "name": "Holding Lifecycle",
            "description": "holding lifecycle test",
            "initial_capital": 1000,
            "holdings": [],
        },
    )
    assert create_portfolio_resp.status_code == 201
    portfolio = create_portfolio_resp.json()
    portfolio_id = portfolio["id"]
    assert portfolio["cash_balance"] == 1000

    add_holding_resp = client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        json={"symbol": "AAPL", "quantity": 2, "average_cost": 100},
    )
    assert add_holding_resp.status_code == 201
    holding = add_holding_resp.json()
    holding_id = holding["id"]
    assert holding["market_value"] == 200
    assert holding["current_price"] == 100

    portfolio_after_buy = client.get(f"/api/v1/portfolios/{portfolio_id}").json()
    assert portfolio_after_buy["cash_balance"] == 800
    assert portfolio_after_buy["current_value"] == pytest.approx(1000.0)
    assert len(portfolio_after_buy["holdings"]) == 1

    update_holding_resp = client.put(
        f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}",
        json={"symbol": "AAPL", "quantity": 3, "average_cost": 90},
    )
    assert update_holding_resp.status_code == 200
    updated_holding = update_holding_resp.json()
    assert updated_holding["quantity"] == 3
    assert updated_holding["average_cost"] == 90
    assert updated_holding["market_value"] == 270

    # cash diff = new_cost(270) - old_cost(200) = 70
    portfolio_after_update = client.get(f"/api/v1/portfolios/{portfolio_id}").json()
    assert portfolio_after_update["cash_balance"] == 730
    assert portfolio_after_update["current_value"] == pytest.approx(1000.0)

    remove_resp = client.delete(f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}")
    assert remove_resp.status_code == 204

    portfolio_after_remove = client.get(f"/api/v1/portfolios/{portfolio_id}").json()
    assert portfolio_after_remove["cash_balance"] == 1000
    assert portfolio_after_remove["current_value"] == pytest.approx(1000.0)
    assert portfolio_after_remove["holdings"] == []


def test_holding_insufficient_cash_rejected(client):
    create_portfolio_resp = client.post(
        "/api/v1/portfolios/",
        json={
            "name": "Holding Insufficient Cash",
            "description": "insufficient cash test",
            "initial_capital": 100,
            "holdings": [],
        },
    )
    assert create_portfolio_resp.status_code == 201
    portfolio_id = create_portfolio_resp.json()["id"]

    add_holding_resp = client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        json={"symbol": "AAPL", "quantity": 10, "average_cost": 100},
    )
    assert add_holding_resp.status_code == 400
    detail = add_holding_resp.json().get("detail", "")
    assert "Insufficient cash balance" in detail
    portfolio_after_reject = client.get(f"/api/v1/portfolios/{portfolio_id}").json()
    assert portfolio_after_reject["cash_balance"] == pytest.approx(100.0)
    assert portfolio_after_reject["current_value"] == pytest.approx(100.0)
    assert portfolio_after_reject["holdings"] == []


def test_add_holding_merges_duplicate_symbol_rows(client):
    create_portfolio_resp = client.post(
        "/api/v1/portfolios/",
        json={
            "name": "Holding Merge",
            "description": "merge duplicate symbol rows",
            "initial_capital": 1000,
            "holdings": [],
        },
    )
    assert create_portfolio_resp.status_code == 201
    portfolio_id = create_portfolio_resp.json()["id"]

    first_add = client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        json={"symbol": "AAPL", "quantity": 2, "average_cost": 100},
    )
    assert first_add.status_code == 201
    first_id = first_add.json()["id"]

    second_add = client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        json={"symbol": "AAPL", "quantity": 1, "average_cost": 120},
    )
    assert second_add.status_code == 201
    second_payload = second_add.json()
    assert second_payload["id"] == first_id
    assert second_payload["quantity"] == pytest.approx(3.0)
    assert second_payload["average_cost"] == pytest.approx((200.0 + 120.0) / 3.0)

    portfolio_after_merge = client.get(f"/api/v1/portfolios/{portfolio_id}").json()
    assert portfolio_after_merge["cash_balance"] == pytest.approx(680.0)
    assert portfolio_after_merge["current_value"] == pytest.approx(1000.0)
    assert len(portfolio_after_merge["holdings"]) == 1


def test_trade_buy_sell_flow_with_weighted_average_cost(client):
    create_portfolio_resp = client.post(
        "/api/v1/portfolios/",
        json={
            "name": "Trade Workflow",
            "description": "trade endpoint test",
            "initial_capital": 1000,
            "holdings": [],
        },
    )
    assert create_portfolio_resp.status_code == 201
    portfolio_id = create_portfolio_resp.json()["id"]

    buy_1_resp = client.post(
        f"/api/v1/portfolios/{portfolio_id}/trades",
        json={
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 2,
            "price": 100,
            "commission": 1,
        },
    )
    assert buy_1_resp.status_code == 201

    buy_2_resp = client.post(
        f"/api/v1/portfolios/{portfolio_id}/trades",
        json={
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 1,
            "price": 120,
            "commission": 0,
        },
    )
    assert buy_2_resp.status_code == 201

    portfolio_after_buys = client.get(f"/api/v1/portfolios/{portfolio_id}").json()
    holding = portfolio_after_buys["holdings"][0]
    assert holding["quantity"] == pytest.approx(3.0)
    # weighted average: ((2*100.5) + (1*120)) / 3 = 107
    assert holding["average_cost"] == pytest.approx(107.0)
    assert portfolio_after_buys["cash_balance"] == pytest.approx(679.0)

    sell_resp = client.post(
        f"/api/v1/portfolios/{portfolio_id}/trades",
        json={
            "symbol": "AAPL",
            "action": "SELL",
            "quantity": 1,
            "price": 130,
            "commission": 1,
        },
    )
    assert sell_resp.status_code == 201
    sell_trade = sell_resp.json()
    assert sell_trade["realized_pnl"] == pytest.approx(22.0)

    portfolio_after_sell = client.get(f"/api/v1/portfolios/{portfolio_id}").json()
    holding_after_sell = portfolio_after_sell["holdings"][0]
    assert holding_after_sell["quantity"] == pytest.approx(2.0)
    assert holding_after_sell["average_cost"] == pytest.approx(107.0)
    assert portfolio_after_sell["cash_balance"] == pytest.approx(808.0)

    trades_resp = client.get(f"/api/v1/portfolios/{portfolio_id}/trades")
    assert trades_resp.status_code == 200
    trades = trades_resp.json()
    assert len(trades) == 3
    assert trades[0]["action"] == "SELL"
    assert trades[0]["symbol"] == "AAPL"
    assert trades[0]["realized_pnl"] == pytest.approx(22.0)


def test_trade_sell_requires_sufficient_quantity(client):
    create_portfolio_resp = client.post(
        "/api/v1/portfolios/",
        json={
            "name": "Trade Quantity Check",
            "description": "sell quantity validation",
            "initial_capital": 1000,
            "holdings": [],
        },
    )
    assert create_portfolio_resp.status_code == 201
    portfolio_id = create_portfolio_resp.json()["id"]

    buy_resp = client.post(
        f"/api/v1/portfolios/{portfolio_id}/trades",
        json={
            "symbol": "MSFT",
            "action": "BUY",
            "quantity": 1,
            "price": 100,
            "commission": 0,
        },
    )
    assert buy_resp.status_code == 201

    sell_resp = client.post(
        f"/api/v1/portfolios/{portfolio_id}/trades",
        json={
            "symbol": "MSFT",
            "action": "SELL",
            "quantity": 2,
            "price": 100,
            "commission": 0,
        },
    )
    assert sell_resp.status_code == 400
    assert "Insufficient holding quantity" in sell_resp.json().get("detail", "")


def test_trade_buy_rejects_invalid_symbol(client):
    create_portfolio_resp = client.post(
        "/api/v1/portfolios/",
        json={
            "name": "Trade Invalid Symbol",
            "description": "buy validation",
            "initial_capital": 1000,
            "holdings": [],
        },
    )
    assert create_portfolio_resp.status_code == 201
    portfolio_id = create_portfolio_resp.json()["id"]

    buy_resp = client.post(
        f"/api/v1/portfolios/{portfolio_id}/trades",
        json={
            "symbol": "INVALID123",
            "action": "BUY",
            "quantity": 1,
            "price": 1,
            "commission": 0,
        },
    )
    assert buy_resp.status_code == 400
    assert "Invalid or unsupported symbol" in buy_resp.json().get("detail", "")

    portfolio_after_reject = client.get(f"/api/v1/portfolios/{portfolio_id}").json()
    assert portfolio_after_reject["cash_balance"] == pytest.approx(1000.0)
    assert portfolio_after_reject["current_value"] == pytest.approx(1000.0)
    assert portfolio_after_reject["holdings"] == []


def test_trade_sell_existing_position_does_not_require_quote_validation(client):
    create_portfolio_resp = client.post(
        "/api/v1/portfolios/",
        json={
            "name": "Trade Sell Existing Position",
            "description": "sell should work without quote lookup",
            "initial_capital": 1000,
            "holdings": [],
        },
    )
    assert create_portfolio_resp.status_code == 201
    portfolio_id = create_portfolio_resp.json()["id"]

    add_holding_resp = client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        json={"symbol": "INVALID123", "quantity": 1, "average_cost": 1},
    )
    assert add_holding_resp.status_code == 201

    sell_resp = client.post(
        f"/api/v1/portfolios/{portfolio_id}/trades",
        json={
            "symbol": "INVALID123",
            "action": "SELL",
            "quantity": 1,
            "price": 1,
            "commission": 0,
        },
    )
    assert sell_resp.status_code == 201

    portfolio_after_sell = client.get(f"/api/v1/portfolios/{portfolio_id}").json()
    assert portfolio_after_sell["holdings"] == []
