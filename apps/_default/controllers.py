"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and templates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import URL, action, redirect, Condition, HTTP, request
from py4web.utils.grid import Grid, Column
from yatl.helpers import A

from aggregator import Aggregator
from direct_scraper import DirectScraper
from .common import T, auth, db, groups, flash, session, scheduler


@action("index")
@action.uses("index.html", auth, T, db)
def index():
    hackathons = db(db.hackathon).select(limitby=(0, 10))
    return dict(title="Hackathons", hackathons=hackathons)


class GridActionButton:
    def __init__(
        self,
        url,
        text,
        icon,
        additional_classes="",
        additional_styles="",
        override_classes="",
        override_styles="",
        message="",
        append_id=False,
        name=None,
        ignore_attribute_plugin=False,
        **attrs,
    ):
        self.url = url
        self.text = text
        self.icon = icon
        self.additional_classes = additional_classes
        self.additional_styles = additional_styles
        self.override_classes = override_classes
        self.override_styles = override_styles
        self.message = message
        self.append_id = append_id
        self.name = name
        self.ignore_attribute_plugin = ignore_attribute_plugin
        self.attrs = attrs


def unauthorized():
    raise HTTP(403, "unauthorized")


admin_only = action.uses(
    "admin/grid.html",
    db,
    auth.user,
    T,
    Condition(lambda: "admin" in groups.get(auth.user_id), on_false=unauthorized),
)


@action("admin")
@admin_only
def admin_index():
    redirect(URL("admin/hackathons/select"))


@action("admin/hackathons/<path:path>", method=["POST", "GET"])
@admin_only
def hackathon(path=None):
    search_queries = [
        [
            "All",
            lambda value: db.hackathon.name.contains(value)
            | db.hackathon.description.contains(value)
            | db.hackathon.date.contains(value)
            | db.hackathon.location.contains(value),
        ],
        ["By Name", lambda value: db.hackathon.name.contains(value)],
        ["By Description", lambda value: db.hackathon.description.contains(value)],
    ]

    orderby = [db.hackathon.name]
    grid = Grid(
        path,
        db.hackathon,
        search_queries=search_queries,
        orderby=orderby,
        T=T,
    )

    grid.columns[1].represent = lambda row: A(row.url, _href=row.url, _target="_blank")

    return dict(title="Admin Hackathons", grid=grid)


@action("admin/schedule_scraper/<scraper:int>", method=["POST", "GET"])
@admin_only
def schedule_scraper(scraper):
    if request.headers["Sec-Fetch-Site"] not in ["same-origin", "none"]:
        flash.set(T("Evil cross-origin request"), "warning")
        return redirect(URL("admin/scrapers/select"))

    scheduler.enqueue_run(
        "run_scraper",
        "manually",
        inputs={"scraper": scraper},
        timeout=3 * 60,
        priority=-1,
    )
    flash.set(T("Scraper scheduled"))
    return redirect(URL("admin/scrapers/select"))


@action("admin/scrapers/<path:path>", method=["POST", "GET"])
@admin_only
def scrapers(path=None):
    search_queries = [
        ["By URL", lambda value: db.scraper.url.contains(value)],
    ]

    pre_action_buttons = [
        lambda row: GridActionButton(
            f"/admin/schedule_scraper/{row.id}",
            "Schedule",
            "fas fa-play",
            name="grid-edit-button",
        )
    ]

    grid = Grid(
        path,
        db.scraper,
        search_queries=search_queries,
        pre_action_buttons=pre_action_buttons,
        T=T,
    )

    grid.columns[3].represent = lambda row: A(row.url, _href=row.url, _target="_blank")

    return dict(title="Admin Scrapers", grid=grid)


@action("admin/users/<path:path>", method=["POST", "GET"])
@admin_only
def users(path=None):
    search_queries = [
        [
            "By Name",
            lambda value: db.auth_user.username.contains(value)
            | db.auth_user.first_name.contains(value)
            | db.auth_user.last_name.contains(value),
        ],
        ["By Email", lambda value: db.auth_user.email.contains(value)],
        ["By Group", lambda value: db.auth_user_tag_groups.tagpath.contains(value)],
    ]

    grid = Grid(
        path,
        db.auth_user,
        search_queries=search_queries,
        orderby=db.auth_user.username,
        T=T,
    )

    grid.columns.insert(
        2,
        Column(
            T("Groups"),
            lambda row: ", ".join(
                tag.tagpath for tag in db(groups.tag_table.record_id == row.id).select()
            ),
        ),
    )

    return dict(title="Manage Users", grid=grid)


@action("admin/tasks/<path:path>", method=["POST", "GET"])
@admin_only
def tasks(path=None):
    search_queries = [
        [
            "By Name or Description",
            lambda value: db.task_run.name.contains(value)
            | db.task_run.description.contains(value),
        ],
    ]

    grid = Grid(
        path,
        db.task_run,
        search_queries=search_queries,
        T=T,
    )

    return dict(title="Manage Tasks", grid=grid)


@action("admin/suggestions/<path:path>", method=["POST", "GET"])
@admin_only
def suggestion(path=None):
    search_queries = [
        ["By Name", lambda value: db.suggestion.name.contains(value)],
    ]

    pre_action_buttons = [
        lambda row: GridActionButton(
            f"/admin/suggestion/{row.id}",
            "Accept",
            "fas fa-edit",
            name="grid-edit-button",
        )
    ]

    grid = Grid(
        path,
        db.suggestion,
        search_queries=search_queries,
        orderby=db.suggestion.created_at,
        pre_action_buttons=pre_action_buttons,
        details=False,
        editable=False,
        T=T,
    )

    return dict(title="Manage Suggestions", grid=grid)


@action("admin/suggestion/<suggestion_id:int>", method=["GET", "POST"])
@action.uses(
    "admin/suggestion.html",
    db,
    session,
    auth.user,
    T,
    Condition(lambda: "admin" in groups.get(auth.user_id), on_false=unauthorized),
    flash,
)
def suggestion_detail(suggestion_id=None):
    suggestion = db.suggestion[suggestion_id]
    if not suggestion:
        flash.set(T("Suggestion not found"))
        return redirect(URL("admin/suggestions/select"))

    # Get the related hackathon
    hackathon = db.hackathon[suggestion.hackathon_id]
    if not hackathon:
        flash.set(T("Hackathon not found"))
        return redirect(URL("admin/suggestions/select"))

    if request.method == "POST":
        apply_fields = request.forms
        if "name" in apply_fields:
            hackathon.update_record(name=suggestion.name)
        if "image" in apply_fields:
            hackathon.update_record(image=suggestion.image)
        if "description" in apply_fields:
            hackathon.update_record(description=suggestion.description)
        if "date" in apply_fields:
            hackathon.update_record(date=suggestion.date)
        if "location" in apply_fields:
            hackathon.update_record(location=suggestion.location)
        suggestion.delete_record()
        db.commit()
        flash.set(T("Fields applied successfully"))
        return redirect(URL("admin/suggestions/select"))

    scraper_type = suggestion.from_scraper and (
        DirectScraper(suggestion.from_scraper.type)
        if suggestion.from_scraper.direct
        else (Aggregator(suggestion.from_scraper.type))
    )
    return dict(
        title=f"Review Suggestion {suggestion.id}",
        suggestion=suggestion,
        hackathon=hackathon,
        scraper_type=scraper_type,
    )
