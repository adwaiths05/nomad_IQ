from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models so metadata includes all tables.
from app.models.auth import AuthSession  # noqa: E402,F401
from app.models.budget import BudgetEstimate  # noqa: E402,F401
from app.models.cost_of_living import CityCostBaseline  # noqa: E402,F401
from app.models.environment import EnvironmentalScore  # noqa: E402,F401
from app.models.event import Event  # noqa: E402,F401
from app.models.explanation import Explanation  # noqa: E402,F401
from app.models.group import GroupMember, TravelGroup  # noqa: E402,F401
from app.models.itinerary import ItineraryDay, ItineraryItem  # noqa: E402,F401
from app.models.memory import MemoryEmbedding  # noqa: E402,F401
from app.models.place import Place, PlaceEmbedding  # noqa: E402,F401
from app.models.profile import TravelerProfile  # noqa: E402,F401
from app.models.replan import Replan  # noqa: E402,F401
from app.models.scoring import ContentScore  # noqa: E402,F401
from app.models.trip import Trip  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401
from app.models.weather import WeatherData  # noqa: E402,F401
