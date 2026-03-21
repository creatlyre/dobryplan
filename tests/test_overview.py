"""Integration tests for year overview dashboard (Phase 15)."""
import uuid

import pytest

from app.database.models import BudgetSettings


def _seed_settings(test_db, calendar_id, rate_1=100, rate_2=50, rate_3=0, zus=1000, acc=200, balance=10000):
    s = BudgetSettings(
        id=str(uuid.uuid4()),
        calendar_id=calendar_id,
        rate_1=rate_1,
        rate_2=rate_2,
        rate_3=rate_3,
        zus_costs=zus,
        accounting_costs=acc,
        initial_balance=balance,
    )
    test_db.add(s)
    return s


class TestOverviewCalculation:
    """YOV-01, YOV-02: Year overview calculation tests."""

    def test_overview_returns_12_months(self, authenticated_client, test_db, test_user_a):
        _seed_settings(test_db, test_user_a.calendar_id)
        res = authenticated_client.get("/api/budget/overview?year=2026")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["year"] == 2026
        assert len(data["months"]) == 12

    def test_overview_net_income_calculation(self, authenticated_client, test_db, test_user_a):
        """YOV-02: Net = (rate*hours)*0.88 - costs for each rate."""
        _seed_settings(test_db, test_user_a.calendar_id)
        # rate_1=100, rate_2=50, rate_3=0, default hours=160
        # net = (100*160)*0.88 + (50*160)*0.88 + (0*160)*0.88 - (1000+200)
        # = 14080 + 7040 + 0 - 1200 = 19920
        res = authenticated_client.get("/api/budget/overview?year=2026")
        data = res.json()["data"]
        assert data["months"][0]["net"] == 19920.0

    def test_overview_monthly_balance_formula(self, authenticated_client, test_db, test_user_a):
        """YOV-02: +/- = Net + Additional - Recurring Expenses - One-time Expenses."""
        _seed_settings(test_db, test_user_a.calendar_id)
        cid = test_user_a.calendar_id
        # Add recurring expense and one-time expense
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Rent", "amount": 5000, "recurring": True},
        )
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 1, "name": "Insurance", "amount": 1200},
        )
        # Add additional earning for month 1
        authenticated_client.post(
            "/api/budget/income/earnings",
            json={"year": 2026, "month": 1, "name": "Bonus", "amount": 3000},
        )
        res = authenticated_client.get("/api/budget/overview?year=2026")
        m1 = res.json()["data"]["months"][0]
        # balance = net(19920) + additional(3000) - recurring(5000) - onetime(1200) = 16720
        assert m1["monthly_balance"] == 16720.0
        # Month 2: no additional, no one-time
        m2 = res.json()["data"]["months"][1]
        assert m2["monthly_balance"] == 19920.0 - 5000.0  # 14920

    def test_overview_with_recurring_earnings(self, authenticated_client, test_db, test_user_a):
        """Recurring earnings (month=0) added to every month."""
        _seed_settings(test_db, test_user_a.calendar_id)
        authenticated_client.post(
            "/api/budget/income/earnings",
            json={"year": 2026, "month": 0, "name": "Partner salary", "amount": 4000},
        )
        res = authenticated_client.get("/api/budget/overview?year=2026")
        # Every month should have 4000 in additional_earnings
        for m in res.json()["data"]["months"]:
            assert m["additional_earnings"] == 4000.0


class TestOverviewRunningBalance:
    """YOV-03, YOV-04: Running balance starting from initial_balance."""

    def test_january_starts_from_initial_balance(self, authenticated_client, test_db, test_user_a):
        """YOV-04: Jan account = initial_balance + Jan balance."""
        _seed_settings(test_db, test_user_a.calendar_id, rate_1=100, rate_2=0, rate_3=0, zus=0, acc=0, balance=50000)
        res = authenticated_client.get("/api/budget/overview?year=2026")
        data = res.json()["data"]
        assert data["initial_balance"] == 50000.0
        jan = data["months"][0]
        # net = (100*160)*0.88 = 14080, no expenses
        assert jan["account_balance"] == 50000.0 + jan["monthly_balance"]

    def test_running_balance_accumulates(self, authenticated_client, test_db, test_user_a):
        """YOV-03: Each month accumulates from previous."""
        _seed_settings(test_db, test_user_a.calendar_id, rate_1=100, rate_2=0, rate_3=0, zus=0, acc=0, balance=50000)
        res = authenticated_client.get("/api/budget/overview?year=2026")
        data = res.json()["data"]
        running = data["initial_balance"]
        for m in data["months"]:
            running += m["monthly_balance"]
            assert abs(m["account_balance"] - running) < 0.01

    def test_running_balance_with_expenses(self, authenticated_client, test_db, test_user_a):
        """Mixed recurring + one-time expenses show correct running total."""
        _seed_settings(test_db, test_user_a.calendar_id, rate_1=100, rate_2=0, rate_3=0, zus=0, acc=0, balance=50000)
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Fixed", "amount": 2000, "recurring": True},
        )
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 6, "name": "Vacation", "amount": 10000},
        )
        res = authenticated_client.get("/api/budget/overview?year=2026")
        data = res.json()["data"]
        running = data["initial_balance"]
        for m in data["months"]:
            running += m["monthly_balance"]
            assert abs(m["account_balance"] - running) < 0.01
        # June should have bigger dip
        june_bal = data["months"][5]["monthly_balance"]
        may_bal = data["months"][4]["monthly_balance"]
        assert june_bal < may_bal  # vacation makes June worse


class TestOverviewAutoRecalculate:
    """YOV-05: Recalculates on data change (API-level, no caching)."""

    def test_overview_updates_after_adding_expense(self, authenticated_client, test_db, test_user_a):
        _seed_settings(test_db, test_user_a.calendar_id, rate_1=100, rate_2=0, rate_3=0, zus=0, acc=0, balance=0)
        res1 = authenticated_client.get("/api/budget/overview?year=2026")
        jan1 = res1.json()["data"]["months"][0]["monthly_balance"]

        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 1, "name": "New expense", "amount": 500},
        )
        res2 = authenticated_client.get("/api/budget/overview?year=2026")
        jan2 = res2.json()["data"]["months"][0]["monthly_balance"]
        assert jan2 == jan1 - 500

    def test_overview_updates_after_changing_hours(self, authenticated_client, test_db, test_user_a):
        _seed_settings(test_db, test_user_a.calendar_id, rate_1=100, rate_2=0, rate_3=0, zus=0, acc=0, balance=0)
        res1 = authenticated_client.get("/api/budget/overview?year=2026")
        jan1_net = res1.json()["data"]["months"][0]["net"]

        # Change hours to 80 for January
        authenticated_client.put(
            "/api/budget/income/hours",
            json={"year": 2026, "month": 1, "rate_1_hours": 80},
        )
        res2 = authenticated_client.get("/api/budget/overview?year=2026")
        jan2_net = res2.json()["data"]["months"][0]["net"]
        assert jan2_net < jan1_net  # Less hours = less income


class TestOverviewPage:
    """Page rendering tests."""

    def test_overview_page_renders(self, authenticated_client):
        res = authenticated_client.get("/budget/overview")
        assert res.status_code == 200
        html = res.text
        assert "overview-content" in html
        assert "overview-body" in html

    def test_overview_page_has_sidebar(self, authenticated_client):
        res = authenticated_client.get("/budget/overview")
        html = res.text
        assert "/budget/settings" in html
        assert "/budget/income" in html
        assert "/budget/expenses" in html

    def test_overview_requires_auth(self, test_client):
        res = test_client.get("/budget/overview", follow_redirects=False)
        assert res.status_code in (302, 303, 401)

    def test_overview_api_requires_auth(self, test_client):
        res = test_client.get("/api/budget/overview?year=2026")
        assert res.status_code in (302, 303, 401)


class TestMonthDetail:
    """OMD-01 through OMD-05: Month detail with one-time expense breakdown."""

    def test_overview_includes_onetime_items(self, authenticated_client, test_db, test_user_a):
        """OMD-01, OMD-02: Clicking month shows expense items with id, name, amount."""
        _seed_settings(test_db, test_user_a.calendar_id)
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 3, "name": "Insurance", "amount": 500},
        )
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 3, "name": "Car repair", "amount": 1200},
        )
        res = authenticated_client.get("/api/budget/overview?year=2026")
        march = res.json()["data"]["months"][2]
        items = march["onetime_items"]
        assert len(items) == 2
        names = {i["name"] for i in items}
        assert names == {"Insurance", "Car repair"}
        for item in items:
            assert "id" in item
            assert "name" in item
            assert "amount" in item

    def test_onetime_items_empty_for_no_expenses(self, authenticated_client, test_db, test_user_a):
        """OMD-01: Empty months return empty onetime_items array."""
        _seed_settings(test_db, test_user_a.calendar_id)
        res = authenticated_client.get("/api/budget/overview?year=2026")
        for m in res.json()["data"]["months"]:
            assert m["onetime_items"] == []

    def test_onetime_items_excludes_recurring(self, authenticated_client, test_db, test_user_a):
        """OMD-02: Recurring expenses never appear in onetime_items."""
        _seed_settings(test_db, test_user_a.calendar_id)
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Rent", "amount": 3000, "recurring": True},
        )
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 5, "name": "Gift", "amount": 200},
        )
        res = authenticated_client.get("/api/budget/overview?year=2026")
        data = res.json()["data"]
        may = data["months"][4]
        assert len(may["onetime_items"]) == 1
        assert may["onetime_items"][0]["name"] == "Gift"
        # No month should have Rent in onetime_items
        for m in data["months"]:
            for item in m["onetime_items"]:
                assert item["name"] != "Rent"

    def test_add_expense_from_overview_updates_totals(self, authenticated_client, test_db, test_user_a):
        """OMD-03: Adding expense via API updates both totals and items."""
        _seed_settings(test_db, test_user_a.calendar_id)
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 1, "name": "New item", "amount": 750},
        )
        res = authenticated_client.get("/api/budget/overview?year=2026")
        jan = res.json()["data"]["months"][0]
        assert jan["onetime_expenses"] == 750.0
        assert len(jan["onetime_items"]) == 1
        assert jan["onetime_items"][0]["name"] == "New item"
        assert jan["onetime_items"][0]["amount"] == 750.0

    def test_delete_expense_updates_overview(self, authenticated_client, test_db, test_user_a):
        """OMD-04: Deleting expense removes it from items and recalculates."""
        _seed_settings(test_db, test_user_a.calendar_id)
        create_res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 2, "name": "To delete", "amount": 300},
        )
        expense_id = create_res.json()["data"]["id"]
        del_res = authenticated_client.delete(f"/api/budget/expenses/{expense_id}")
        assert del_res.status_code == 200

        res = authenticated_client.get("/api/budget/overview?year=2026")
        feb = res.json()["data"]["months"][1]
        assert feb["onetime_expenses"] == 0.0
        assert len(feb["onetime_items"]) == 0

    def test_edit_expense_updates_overview(self, authenticated_client, test_db, test_user_a):
        """OMD-04: Editing expense updates amount in items and totals."""
        _seed_settings(test_db, test_user_a.calendar_id)
        create_res = authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 4, "name": "Editable", "amount": 100},
        )
        expense_id = create_res.json()["data"]["id"]
        authenticated_client.put(
            f"/api/budget/expenses/{expense_id}",
            json={"amount": 200},
        )
        res = authenticated_client.get("/api/budget/overview?year=2026")
        april = res.json()["data"]["months"][3]
        assert april["onetime_expenses"] == 200.0
        assert len(april["onetime_items"]) == 1
        assert april["onetime_items"][0]["amount"] == 200.0


class TestMultiYearCarryForward:
    """BUD-01, BUD-02: Carry-forward balance and year navigation bounds."""

    def test_first_year_uses_initial_balance(self, authenticated_client, test_db, test_user_a):
        """First year with data uses global initial_balance."""
        _seed_settings(test_db, test_user_a.calendar_id, balance=50000)
        authenticated_client.put(
            "/api/budget/income/hours",
            json={"year": 2026, "month": 1, "rate_1_hours": 160, "rate_2_hours": 160, "rate_3_hours": 160},
        )
        res = authenticated_client.get("/api/budget/overview?year=2026")
        data = res.json()["data"]
        assert data["carry_forward"]["type"] == "initial"
        assert data["carry_forward"]["amount"] == 50000.0
        assert data["carry_forward"]["source_year"] is None
        assert data["initial_balance"] == 50000.0

    def test_carry_forward_from_prior_year(self, authenticated_client, test_db, test_user_a):
        """Year after first year carries forward December's account_balance."""
        _seed_settings(test_db, test_user_a.calendar_id, rate_1=100, rate_2=0, rate_3=0, zus=0, acc=0, balance=10000)
        authenticated_client.put(
            "/api/budget/income/hours",
            json={"year": 2026, "month": 1, "rate_1_hours": 160, "rate_2_hours": 160, "rate_3_hours": 160},
        )
        # Get 2026 December balance
        res_2026 = authenticated_client.get("/api/budget/overview?year=2026")
        dec_balance_2026 = res_2026.json()["data"]["months"][11]["account_balance"]

        # Seed 2027 data
        authenticated_client.put(
            "/api/budget/income/hours",
            json={"year": 2027, "month": 1, "rate_1_hours": 160, "rate_2_hours": 160, "rate_3_hours": 160},
        )
        res_2027 = authenticated_client.get("/api/budget/overview?year=2027")
        data_2027 = res_2027.json()["data"]
        assert data_2027["carry_forward"]["type"] == "carry_forward"
        assert data_2027["carry_forward"]["amount"] == dec_balance_2026
        assert data_2027["carry_forward"]["source_year"] == 2026
        assert data_2027["initial_balance"] == dec_balance_2026

    def test_no_prior_year_data_starts_from_zero(self, authenticated_client, test_db, test_user_a):
        """Year with no prior data starts from 0."""
        _seed_settings(test_db, test_user_a.calendar_id, balance=50000)
        authenticated_client.put(
            "/api/budget/income/hours",
            json={"year": 2026, "month": 1, "rate_1_hours": 160, "rate_2_hours": 160, "rate_3_hours": 160},
        )
        # Request 2028 — 2027 has no data
        res = authenticated_client.get("/api/budget/overview?year=2028")
        data = res.json()["data"]
        assert data["carry_forward"]["type"] == "no_prior_data"
        assert data["carry_forward"]["amount"] == 0
        assert data["carry_forward"]["source_year"] == 2027

    def test_empty_year_returns_12_months(self, authenticated_client, test_db, test_user_a):
        """Empty year renders 12-month structure with no errors."""
        _seed_settings(test_db, test_user_a.calendar_id, rate_1=0, rate_2=0, rate_3=0, zus=0, acc=0, balance=0)
        res = authenticated_client.get("/api/budget/overview?year=2099")
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data["months"]) == 12

    def test_year_bounds_with_data(self, authenticated_client, test_db, test_user_a):
        """Year bounds reflect actual data range + current year + 1."""
        _seed_settings(test_db, test_user_a.calendar_id)
        authenticated_client.put(
            "/api/budget/income/hours",
            json={"year": 2025, "month": 6, "rate_1_hours": 160, "rate_2_hours": 160, "rate_3_hours": 160},
        )
        authenticated_client.put(
            "/api/budget/income/hours",
            json={"year": 2026, "month": 1, "rate_1_hours": 160, "rate_2_hours": 160, "rate_3_hours": 160},
        )
        res = authenticated_client.get("/api/budget/overview?year=2026")
        bounds = res.json()["year_bounds"]
        assert bounds["min_year"] == 2025
        assert bounds["max_year"] >= 2027

    def test_year_bounds_no_data(self, authenticated_client, test_db, test_user_a):
        """No data returns current year as min, current+1 as max."""
        _seed_settings(test_db, test_user_a.calendar_id)
        res = authenticated_client.get("/api/budget/overview?year=2026")
        bounds = res.json()["year_bounds"]
        assert "min_year" in bounds
        assert "max_year" in bounds
        assert bounds["max_year"] == bounds["min_year"] + 1

    def test_api_response_includes_carry_forward_and_bounds(self, authenticated_client, test_db, test_user_a):
        """API response shape includes carry_forward dict and year_bounds."""
        _seed_settings(test_db, test_user_a.calendar_id)
        res = authenticated_client.get("/api/budget/overview?year=2026")
        json_data = res.json()
        assert "data" in json_data
        assert "year_bounds" in json_data
        assert "carry_forward" in json_data["data"]
        cf = json_data["data"]["carry_forward"]
        assert "type" in cf
        assert "amount" in cf
        assert "source_year" in cf


class TestRecurringExpensesMultiYear:
    """BUD-03: Recurring expenses are scoped to their year."""

    def test_recurring_expense_scoped_to_year(self, authenticated_client, test_db, test_user_a):
        _seed_settings(test_db, test_user_a.calendar_id, rate_1=100, rate_2=0, rate_3=0, zus=0, acc=0, balance=0)
        # Create recurring expense in 2026
        authenticated_client.post(
            "/api/budget/expenses",
            json={"year": 2026, "month": 0, "name": "Rent", "amount": 5000, "recurring": True},
        )
        # Shows in 2026
        res = authenticated_client.get("/api/budget/overview?year=2026")
        assert res.json()["data"]["months"][0]["recurring_expenses"] == 5000.0
        # Does NOT show in 2027
        res = authenticated_client.get("/api/budget/overview?year=2027")
        assert res.json()["data"]["months"][0]["recurring_expenses"] == 0.0


class TestYearOverYearComparison:
    """BUD-04: Year-over-year comparison."""

    def test_comparison_returns_both_years(self, authenticated_client, test_db, test_user_a):
        _seed_settings(test_db, test_user_a.calendar_id)
        res = authenticated_client.get("/api/budget/overview/comparison?year=2026")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["selected_year"] == 2026
        assert data["previous_year"] == 2025

    def test_comparison_has_required_keys(self, authenticated_client, test_db, test_user_a):
        _seed_settings(test_db, test_user_a.calendar_id)
        res = authenticated_client.get("/api/budget/overview/comparison?year=2026")
        data = res.json()["data"]
        required_keys = {"total_net", "total_additional", "total_recurring", "total_onetime", "total_balance", "final_account_balance"}
        assert required_keys.issubset(set(data["selected"].keys()))
        assert required_keys.issubset(set(data["previous"].keys()))
        assert required_keys.issubset(set(data["delta"].keys()))

    def test_comparison_delta_is_selected_minus_previous(self, authenticated_client, test_db, test_user_a):
        _seed_settings(test_db, test_user_a.calendar_id)
        authenticated_client.post("/api/budget/expenses", json={"year": 2026, "month": 1, "name": "Test", "amount": 500})
        res = authenticated_client.get("/api/budget/overview/comparison?year=2026")
        data = res.json()["data"]
        for key in ["total_net", "total_additional", "total_recurring", "total_onetime", "total_balance", "final_account_balance"]:
            assert abs(data["delta"][key] - (data["selected"][key] - data["previous"][key])) < 0.01

    def test_comparison_previous_year_has_valid_data(self, authenticated_client, test_db, test_user_a):
        """Previous year with no year-specific data still returns computed values."""
        _seed_settings(test_db, test_user_a.calendar_id)
        res = authenticated_client.get("/api/budget/overview/comparison?year=2026")
        data = res.json()["data"]
        assert data["previous"]["total_net"] is not None
        assert isinstance(data["previous"]["final_account_balance"], (int, float))

    def test_comparison_requires_auth(self, test_client):
        res = test_client.get("/api/budget/overview/comparison?year=2026")
        assert res.status_code in (302, 303, 401)


class TestCarryForwardOverride:
    """Manual carry-forward override tests."""

    def test_set_override_changes_carry_forward(self, authenticated_client, test_db, test_user_a):
        """PUT override makes overview return type=override with custom amount."""
        _seed_settings(test_db, test_user_a.calendar_id, balance=10000)
        authenticated_client.put(
            "/api/budget/income/hours",
            json={"year": 2026, "month": 1, "rate_1_hours": 160, "rate_2_hours": 160, "rate_3_hours": 160},
        )
        # Set manual override
        res = authenticated_client.put(
            "/api/budget/overview/carry-forward",
            json={"year": 2026, "amount": 25000},
        )
        assert res.status_code == 200

        # Verify overview uses override
        res = authenticated_client.get("/api/budget/overview?year=2026")
        cf = res.json()["data"]["carry_forward"]
        assert cf["type"] == "override"
        assert cf["amount"] == 25000.0
        assert res.json()["data"]["initial_balance"] == 25000.0

    def test_delete_override_restores_computed(self, authenticated_client, test_db, test_user_a):
        """DELETE override restores the computed carry-forward."""
        _seed_settings(test_db, test_user_a.calendar_id, balance=10000)
        authenticated_client.put(
            "/api/budget/income/hours",
            json={"year": 2026, "month": 1, "rate_1_hours": 160, "rate_2_hours": 160, "rate_3_hours": 160},
        )
        # Set and then delete override
        authenticated_client.put(
            "/api/budget/overview/carry-forward",
            json={"year": 2026, "amount": 99999},
        )
        res = authenticated_client.delete("/api/budget/overview/carry-forward?year=2026")
        assert res.status_code == 200

        # Should be back to initial type
        res = authenticated_client.get("/api/budget/overview?year=2026")
        cf = res.json()["data"]["carry_forward"]
        assert cf["type"] == "initial"
        assert cf["amount"] == 10000.0

    def test_delete_nonexistent_override_returns_404(self, authenticated_client, test_db, test_user_a):
        _seed_settings(test_db, test_user_a.calendar_id)
        res = authenticated_client.delete("/api/budget/overview/carry-forward?year=2026")
        assert res.status_code == 404
