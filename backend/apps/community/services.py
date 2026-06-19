import uuid

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.paginator import Page, Paginator
from django.db.models import F, QuerySet

from apps.community.api.schemas import CreateSuggestRequest

from .models import ProductionLog, Suggest


def _get_page(queryset: QuerySet[any], page_num: int, per_page: int = 10) -> Page:
    return Paginator(object_list=queryset, per_page=per_page).get_page(number=page_num)


def get_production_logs(page_num: int) -> QuerySet["ProductionLog"] | None:
    if page_num <= 0:
        return None

    queryset = ProductionLog.objects.all().order_by("-created_at")
    page = _get_page(queryset=queryset, page_num=page_num)

    if page_num > page.paginator.num_pages:
        return None
    return page.object_list


def get_suggests(page_num: int, order_by: str) -> QuerySet["Suggest"] | None:
    if page_num <= 0:
        return None

    queryset = Suggest.objects.filter(status__in=["NEW", "PLN", "RVW"])
    match order_by:
        case "new":
            queryset = queryset.order_by("-created_at")
        case "popular":
            queryset = queryset.order_by("-likes")
        case _:
            return None
    page = _get_page(queryset=queryset, page_num=page_num)

    if page_num > page.paginator.num_pages:
        return None
    return page.object_list


def get_liked_suggest_ids(
    user: AbstractBaseUser | AnonymousUser, suggests: QuerySet["Suggest"]
) -> list:
    if not user.is_authenticated or not suggests:
        return []

    suggest_ids = [s.id for s in suggests]

    return list(
        user.liked_suggests.filter(id__in=suggest_ids).values_list("id", flat=True)
    )


async def like_suggest(suggest_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    try:
        suggest = await Suggest.objects.aget(id=suggest_id)
        is_liked = await suggest.liked_by.filter(id=user_id).aexists()

        if is_liked:
            await suggest.liked_by.aremove(user_id)
            await Suggest.objects.filter(id=suggest_id).aupdate(likes=F("likes") - 1)
        else:
            await suggest.liked_by.aadd(user_id)
            await Suggest.objects.filter(id=suggest_id).aupdate(likes=F("likes") + 1)

        return True
    except Exception:
        return False


async def create_suggest(user_id: uuid.UUID, payload: CreateSuggestRequest) -> bool:
    title = payload.title.strip()
    description = payload.description.strip()

    if not title or not description:
        return False

    try:
        await Suggest.objects.acreate(
            status=Suggest.Status.MODERATION,
            author_id=user_id,
            title=title,
            description=description,
        )
        return True
    except Exception:
        return False
