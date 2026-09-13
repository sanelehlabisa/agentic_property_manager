from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.prediction import PredictionRead
from app.services import predictions as service

router = APIRouter(tags=["maintenance predictions"])


def prediction_response(prediction, component) -> PredictionRead:
    return PredictionRead.model_validate(prediction).model_copy(
        update={
            "component_name": component.name,
            "category_code": component.category_code,
        }
    )


@router.get(
    "/properties/{property_id}/predictions", response_model=list[PredictionRead]
)
def get_predictions(
    property_id: UUID, session: DatabaseSession, user: CurrentUser
) -> list[PredictionRead]:
    return [
        prediction_response(prediction, component)
        for prediction, component in service.calculate_predictions(
            session, user, property_id
        )
    ]


@router.post("/predictions/{prediction_id}/approve", response_model=PredictionRead)
def approve_prediction(
    prediction_id: UUID, session: DatabaseSession, user: CurrentUser
) -> PredictionRead:
    prediction = service.review_prediction(session, user, prediction_id, approved=True)
    return prediction_response(
        prediction, service.prediction_component(session, prediction)
    )


@router.post("/predictions/{prediction_id}/dismiss", response_model=PredictionRead)
def dismiss_prediction(
    prediction_id: UUID, session: DatabaseSession, user: CurrentUser
) -> PredictionRead:
    prediction = service.review_prediction(session, user, prediction_id, approved=False)
    return prediction_response(
        prediction, service.prediction_component(session, prediction)
    )
