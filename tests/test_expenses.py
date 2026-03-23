"""Integration tests for expense management (Phase 14)."""
import pytest


class TestExpenseRecurringCRUD:
    """EXP-01, EXP-03: Recurring expense CRUD."""

    def test_create_recurring_expense(self, authenticated_client):
        res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Czynsz", "amount": 2500, "recurring": True},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["name"] == "Czynsz"
        assert data["amount"] == 2500.0
        assert data["month"] == 0
        assert data["recurring"] is True

    def test_get_recurring_expenses(self, authenticated_client):
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Czynsz", "amount": 2500, "recurring": True},
        )
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Internet", "amount": 80, "recurring": True},
        )
        res = authenticated_client.get("/api/budget/expenses?year=2026")
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data["recurring_expenses"]) == 2
        names = {e["name"] for e in data["recurring_expenses"]}
        assert names == {"Czynsz", "Internet"}

    def test_update_recurring_expense(self, authenticated_client):
        create = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Czynsz", "amount": 2500, "recurring": True},
        )
        eid = create.json()["data"]["id"]
        res = authenticated_client.put(
            f"/api/budget/expenses/{eid}",
            json={"name": "Czynsz + media", "amount": 2800},
        )
        assert res.status_code == 200
        assert res.json()["data"]["name"] == "Czynsz + media"
        assert res.json()["data"]["amount"] == 2800.0

    def test_delete_recurring_expense(self, authenticated_client):
        create = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Czynsz", "amount": 2500, "recurring": True},
        )
        eid = create.json()["data"]["id"]
        res = authenticated_client.delete(f"/api/budget/expenses/{eid}")
        assert res.status_code == 200
        assert res.json()["ok"] is True
        # Verify gone
        get = authenticated_client.get("/api/budget/expenses?year=2026")
        assert len(get.json()["data"]["recurring_expenses"]) == 0


class TestExpenseOnetimeCRUD:
    """EXP-02, EXP-03: One-time expense CRUD."""

    def test_create_onetime_expense(self, authenticated_client):
        res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 3, "name": "Ubezpieczenie", "amount": 1200},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["name"] == "Ubezpieczenie"
        assert data["amount"] == 1200.0
        assert data["month"] == 3
        assert data["recurring"] is False

    def test_get_onetime_expenses_by_year(self, authenticated_client):
        for month, name, amount in [(1, "Serwis", 500), (6, "Wakacje", 5000), (12, "Święta", 2000)]:
            authenticated_client.post(
                "/api/budget/expenses",
                json={"year": 2026, "month": month, "name": name, "amount": amount},
            )
        res = authenticated_client.get("/api/budget/expenses?year=2026")
        data = res.json()["data"]
        assert len(data["onetime_expenses"]) == 3

    def test_update_onetime_expense_month(self, authenticated_client):
        create = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 3, "name": "Ubezpieczenie", "amount": 1200},
        )
        eid = create.json()["data"]["id"]
        res = authenticated_client.put(
            f"/api/budget/expenses/{eid}",
            json={"month": 5},
        )
        assert res.status_code == 200
        assert res.json()["data"]["month"] == 5

    def test_delete_onetime_expense(self, authenticated_client):
        create = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 7, "name": "Wakacje", "amount": 5000},
        )
        eid = create.json()["data"]["id"]
        res = authenticated_client.delete(f"/api/budget/expenses/{eid}")
        assert res.status_code == 200
        get = authenticated_client.get("/api/budget/expenses?year=2026")
        assert len(get.json()["data"]["onetime_expenses"]) == 0


class TestExpenseAutoRecurring:
    """EXP-04: Recurring expenses applied to every month."""

    def test_recurring_in_year_data(self, authenticated_client):
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Czynsz", "amount": 2500, "recurring": True},
        )
        res = authenticated_client.get("/api/budget/expenses?year=2026")
        data = res.json()["data"]
        assert len(data["recurring_expenses"]) == 1
        assert data["recurring_expenses"][0]["name"] == "Czynsz"

    def test_month_zero_auto_recurring(self, authenticated_client):
        """Creating with month=0 automatically sets recurring=True."""
        res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Test", "amount": 100},
        )
        assert res.json()["data"]["recurring"] is True


class TestExpenseValidation:
    """Validation edge cases."""

    def test_expense_name_required(self, authenticated_client):
        res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 1, "name": "  ", "amount": 100},
        )
        assert res.status_code == 422

    def test_expense_amount_zero_rejected(self, authenticated_client):
        res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 1, "name": "Test", "amount": 0},
        )
        assert res.status_code == 422

    def test_onetime_expense_negative_amount_ok(self, authenticated_client):
        """Negative one-time expense acts as a correction/patch."""
        res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 1, "name": "Poprawka styczen", "amount": -5400},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["amount"] == -5400.0
        assert data["recurring"] is False

    def test_recurring_expense_negative_rejected(self, authenticated_client):
        """Recurring expenses must stay positive."""
        res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Bad recurring", "amount": -100, "recurring": True},
        )
        assert res.status_code == 422

    def test_expense_month_range(self, authenticated_client):
        res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 13, "name": "Test", "amount": 100},
        )
        assert res.status_code == 422

    def test_update_nonexistent(self, authenticated_client):
        res = authenticated_client.put(
            "/api/budget/expenses/nonexistent-id",
            json={"name": "New name"},
        )
        assert res.status_code == 404

    def test_delete_nonexistent(self, authenticated_client):
        res = authenticated_client.delete("/api/budget/expenses/nonexistent-id")
        assert res.status_code == 404


class TestExpenseBulk:
    """Bulk create endpoint."""

    def test_bulk_create_recurring(self, authenticated_client):
        res = authenticated_client.post(
            "/api/budget/expenses/bulk",
            json={"expenses": [
                {"year": 2026, "month": 0, "name": "Czynsz", "amount": 6300, "recurring": True},
                {"year": 2026, "month": 0, "name": "Internet", "amount": 80, "recurring": True},
                {"year": 2026, "month": 0, "name": "Netflix", "amount": 30, "recurring": True},
            ]},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) == 3
        assert {e["name"] for e in data} == {"Czynsz", "Internet", "Netflix"}

    def test_bulk_create_onetime(self, authenticated_client):
        res = authenticated_client.post(
            "/api/budget/expenses/bulk",
            json={"expenses": [
                {"year": 2026, "month": 1, "name": "Wiertla", "amount": 65},
                {"year": 2026, "month": 3, "name": "Robot szyby", "amount": 3000},
            ]},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) == 2
        assert data[0]["month"] == 1
        assert data[1]["month"] == 3

    def test_bulk_create_empty_list(self, authenticated_client):
        res = authenticated_client.post(
            "/api/budget/expenses/bulk",
            json={"expenses": []},
        )
        assert res.status_code == 200
        assert res.json()["data"] == []

    def test_bulk_validation_rejects_invalid(self, authenticated_client):
        res = authenticated_client.post(
            "/api/budget/expenses/bulk",
            json={"expenses": [
                {"year": 2026, "month": 1, "name": "", "amount": 100},
            ]},
        )
        assert res.status_code == 422

    def test_bulk_delete_recurring(self, authenticated_client):
        # Create 3 recurring expenses for 2026
        for name in ["Rent", "Insurance", "Phone"]:
            authenticated_client.post(
                "/api/budget/expenses",
                json={"year": 2026, "month": 0, "name": name, "amount": 1000, "recurring": True},
            )
        # Also create one onetime
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 3, "name": "Gift", "amount": 200},
        )
        # Delete all recurring for 2026
        res = authenticated_client.delete("/api/budget/expenses/bulk?year=2026&type=recurring")
        assert res.status_code == 200
        assert res.json()["deleted"] == 3
        # Onetime still exists
        data = authenticated_client.get("/api/budget/expenses?year=2026").json()["data"]
        assert len(data["recurring_expenses"]) == 0
        assert len(data["onetime_expenses"]) == 1

    def test_bulk_delete_onetime(self, authenticated_client):
        # Create recurring + onetime
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Rent", "amount": 1000, "recurring": True},
        )
        for m in [1, 5]:
            authenticated_client.post(
                "/api/budget/expenses",
                json={"year": 2026, "month": m, "name": f"Item {m}", "amount": 100},
            )
        # Delete all onetime for 2026
        res = authenticated_client.delete("/api/budget/expenses/bulk?year=2026&type=onetime")
        assert res.status_code == 200
        assert res.json()["deleted"] == 2
        # Recurring still exists
        data = authenticated_client.get("/api/budget/expenses?year=2026").json()["data"]
        assert len(data["recurring_expenses"]) == 1
        assert len(data["onetime_expenses"]) == 0


class TestExpensePage:
    """Page rendering tests."""

    def test_expenses_page_renders(self, authenticated_client):
        res = authenticated_client.get("/budget/expenses")
        assert res.status_code == 200
        html = res.text
        assert "expenses-content" in html
        assert "recurring-body" in html
        assert "onetime-body" in html

    def test_expenses_page_has_sidebar(self, authenticated_client):
        res = authenticated_client.get("/budget/expenses")
        html = res.text
        assert "/budget/settings" in html
        assert "/budget/income" in html

    def test_expenses_requires_auth(self, test_client):
        res = test_client.get("/budget/expenses", follow_redirects=False)
        assert res.status_code in (302, 303, 401)

    def test_expense_api_requires_auth(self, test_client):
        res = test_client.get("/api/budget/expenses?year=2026")
        assert res.status_code in (302, 303, 401)


class TestExpenseCategories:
    """XCAT-01, XCAT-02, XCAT-05: Expense category CRUD and breakdown."""

    def test_list_expense_categories_returns_presets(self, authenticated_client):
        res = authenticated_client.get("/api/budget/expenses/categories")
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) == 8
        names = {c["name"] for c in data}
        assert "Groceries" in names
        assert "Rent" in names
        assert "Other" in names
        # All are presets
        assert all(c["is_preset"] for c in data)

    def test_create_custom_expense_category(self, authenticated_client):
        # Trigger preset seeding first
        authenticated_client.get("/api/budget/expenses/categories")
        res = authenticated_client.post(
            "/api/budget/expenses/categories",
            json={"name": "Subscriptions", "color": "#8b5cf6"},
        )
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["name"] == "Subscriptions"
        assert data["color"] == "#8b5cf6"
        assert data["is_preset"] is False

    def test_create_category_invalid_color(self, authenticated_client):
        res = authenticated_client.post(
            "/api/budget/expenses/categories",
            json={"name": "Bad", "color": "red"},
        )
        assert res.status_code == 422

    def test_create_expense_with_category(self, authenticated_client):
        # Get categories (seeds presets)
        cats = authenticated_client.get("/api/budget/expenses/categories").json()["data"]
        cat_id = cats[0]["id"]
        # Create expense with category
        res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 1, "name": "Weekly groceries", "amount": 250, "category_id": cat_id},
        )
        assert res.status_code == 200
        assert res.json()["data"]["category_id"] == cat_id
        # Verify in year data
        year_data = authenticated_client.get("/api/budget/expenses?year=2026").json()["data"]
        ot = year_data["onetime_expenses"]
        assert any(e["category_id"] == cat_id for e in ot)

    def test_update_expense_category(self, authenticated_client):
        cats = authenticated_client.get("/api/budget/expenses/categories").json()["data"]
        cat_id = cats[0]["id"]
        create = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 3, "name": "Test", "amount": 100},
        )
        eid = create.json()["data"]["id"]
        res = authenticated_client.put(
            f"/api/budget/expenses/{eid}",
            json={"category_id": cat_id},
        )
        assert res.status_code == 200
        assert res.json()["data"]["category_id"] == cat_id

    def test_expenses_by_category_breakdown(self, authenticated_client):
        cats = authenticated_client.get("/api/budget/expenses/categories").json()["data"]
        cat_a = cats[0]["id"]
        cat_b = cats[1]["id"]
        # Create expenses with categories
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 1, "name": "Milk", "amount": 50, "category_id": cat_a},
        )
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 2, "name": "Bread", "amount": 30, "category_id": cat_a},
        )
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 1, "name": "Monthly rent", "amount": 2000, "category_id": cat_b},
        )
        # Uncategorized
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 5, "name": "Random", "amount": 100},
        )
        res = authenticated_client.get("/api/budget/expenses/by-category?year=2026")
        assert res.status_code == 200
        data = res.json()["data"]
        # Should have 3 buckets: cat_a, cat_b, uncategorized
        assert len(data) == 3
        totals = {b["category_id"]: b["total_amount"] for b in data}
        assert totals[cat_a] == 80.0
        assert totals[cat_b] == 2000.0
        assert totals[None] == 100.0
