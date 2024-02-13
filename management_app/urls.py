# urls.py

from fastapi import APIRouter
from . import views

router = APIRouter()

router.add_api_route("/profiles/{user_id}", views.read_profile, methods=["GET"])
router.add_api_route("/profiles/{user_id}", views.update_profile, methods=["PUT"])
router.add_api_route("/profiles/{user_id}", views.delete_profile, methods=["DELETE"])