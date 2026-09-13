import calendar
from datetime import date, timedelta
from decimal import Decimal
from statistics import median
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Component, MaintenanceRecord, MaintenanceRule, Prediction, User
from app.models.enums import PredictionStatus, PredictionUrgency
from app.services.access import require_property_manager


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calculate_predictions(
    session: Session, user: User, property_id: UUID, *, as_of: date | None = None
) -> list[tuple[Prediction, Component]]:
    require_property_manager(session, user, property_id)
    reference_date = as_of or date.today()
    component_rules = session.execute(
        select(Component, MaintenanceRule)
        .join(
            MaintenanceRule,
            MaintenanceRule.category_code == Component.category_code,
        )
        .where(
            Component.property_id == property_id,
            MaintenanceRule.active.is_(True),
        )
        .order_by(Component.name)
    ).all()

    results: list[tuple[Prediction, Component]] = []
    for component, rule in component_rules:
        records = list(
            session.scalars(
                select(MaintenanceRecord)
                .where(MaintenanceRecord.component_id == component.id)
                .order_by(MaintenanceRecord.completed_on.desc())
                .limit(5)
            )
        )
        baseline = records[0].completed_on if records else component.installed_on
        if baseline is None:
            continue

        due_date = add_months(baseline, rule.interval_months)
        urgency = _urgency(due_date, reference_date, rule.warning_days)
        estimated_cost, cost_source = _estimated_cost(records, rule.default_cost)
        explanation = _explanation(
            rule.description,
            due_date,
            reference_date,
            baseline,
            bool(records),
            cost_source,
        )

        prediction = session.scalar(
            select(Prediction)
            .where(
                Prediction.component_id == component.id,
                Prediction.maintenance_rule_id == rule.id,
            )
            .order_by(Prediction.created_at.desc())
        )
        if prediction is None:
            prediction = Prediction(
                component_id=component.id,
                maintenance_rule_id=rule.id,
                status=PredictionStatus.ACTIVE,
            )
            session.add(prediction)

        if prediction.status in {
            PredictionStatus.ACTIVE,
            PredictionStatus.APPROVED,
        }:
            prediction.due_date = due_date
            prediction.urgency = urgency
            prediction.estimated_cost = estimated_cost
            prediction.explanation = explanation
        results.append((prediction, component))

    session.commit()
    for prediction, _ in results:
        session.refresh(prediction)
    return results


def review_prediction(
    session: Session, user: User, prediction_id: UUID, *, approved: bool
) -> Prediction:
    prediction = session.scalar(
        select(Prediction).where(Prediction.id == prediction_id).with_for_update()
    )
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    component = session.get(Component, prediction.component_id)
    if component is None:
        raise HTTPException(status_code=404, detail="Prediction component not found")
    require_property_manager(session, user, component.property_id)
    if prediction.status != PredictionStatus.ACTIVE:
        raise HTTPException(
            status_code=409, detail="Prediction has already been reviewed"
        )

    prediction.status = (
        PredictionStatus.APPROVED if approved else PredictionStatus.DISMISSED
    )
    session.commit()
    session.refresh(prediction)
    return prediction


def prediction_component(session: Session, prediction: Prediction) -> Component:
    component = session.get(Component, prediction.component_id)
    if component is None:
        raise HTTPException(status_code=404, detail="Prediction component not found")
    return component


def _urgency(
    due_date: date, reference_date: date, warning_days: int
) -> PredictionUrgency:
    if due_date < reference_date:
        return PredictionUrgency.OVERDUE
    if due_date <= reference_date + timedelta(days=warning_days):
        return PredictionUrgency.DUE_SOON
    return PredictionUrgency.UPCOMING


def _estimated_cost(
    records: list[MaintenanceRecord], default_cost: Decimal
) -> tuple[Decimal, str]:
    if not records:
        return default_cost, "the configured category default"
    costs = [record.cost for record in records]
    return Decimal(median(costs)).quantize(Decimal("0.01")), (
        f"the median of {len(costs)} recent service record"
        f"{'s' if len(costs) != 1 else ''}"
    )


def _explanation(
    rule_description: str,
    due_date: date,
    reference_date: date,
    baseline: date,
    has_history: bool,
    cost_source: str,
) -> str:
    delta = (due_date - reference_date).days
    if delta < 0:
        timing = f"was due {abs(delta)} days ago"
    elif delta == 0:
        timing = "is due today"
    else:
        timing = f"is due in {delta} days"
    baseline_source = "latest completed service" if has_history else "installation date"
    return (
        f"{rule_description} It {timing}, calculated from the {baseline_source} "
        f"on {baseline.isoformat()}. The estimate uses {cost_source}."
    )
