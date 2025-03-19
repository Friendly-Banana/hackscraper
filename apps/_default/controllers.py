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

from py4web import URL, action, redirect, Condition, HTTP
from py4web.utils.grid import Grid, Column
from yatl.helpers import A

from .common import T, auth, db, groups, flash


@action("index")
@action.uses("index.html", auth, T)
def index():
    user = auth.get_user()
    message = T("Hello {first_name}").format(**user) if user else T("Hello")
    return dict(message=message)


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
            **attrs
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
    raise HTTP(404)
    return redirect(URL("index"))


admin_only = action.uses("admin/grid.html", db, auth.user, T, Condition(lambda: 'admin' in groups.get(auth.user_id), on_false=unauthorized))


@action("admin")
@admin_only
def admin_index():
    redirect(URL("admin/hackathon/select"))


@action("admin/hackathon/<path:path>", method=["POST", "GET"])
@admin_only
def hackathon(path=None):
    search_queries = [[
        "All",
        lambda value: db.hackathon.name.contains(value) | (db.hackathon.description.contains(value)) |
                      (db.hackathon.date.contains(value) | (db.hackathon.location.contains(value)))],
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

    return dict(grid=grid)


@action("admin/scraper/<path:path>", method=["POST", "GET"])
@admin_only
def scraper(path=None):
    search_queries = [["By URL", lambda value: db.scraper.url.contains(value)], ]

    grid = Grid(
        path,
        db.scraper,
        search_queries=search_queries,
        orderby=db.scraper.next_scrape,
        T=T,
    )

    grid.columns[3].represent = lambda row: A(row.url, _href=row.url, _target="_blank")

    return dict(grid=grid)


@action("admin/user/<path:path>", method=["POST", "GET"])
@admin_only
def user(path=None):
    search_queries = [["By Name", lambda value: db.auth_user.username.contains(value) | db.auth_user.first_name.contains(
        value) | db.auth_user.last_name.contains(value)],
                      ["By Email", lambda value: db.auth_user.email.contains(value)],
                      ["By Group", lambda value: db.auth_user_tag_groups.tagpath.contains(value)], ]

    grid = Grid(
        path,
        db.auth_user,
        search_queries=search_queries,
        orderby=db.auth_user.username,
        T=T,
    )

    grid.columns.insert(0,
                        Column(T("Groups"),
                               lambda row: ", ".join(tag.tagpath for tag in db(db.auth_user_tag_groups.record_id == row.id).select()))
                        )

    return dict(grid=grid)


@action("admin/suggestions/<suggestion_id:int>", method=["GET", "POST"])
@action.uses("admin/suggestion.html", db, auth. user, T, Condition(lambda: 'admin' in groups. get(auth. user_id), on_false=unauthorized), flash)
def suggestion_detail(suggestion_id=None):
    suggestion = db.suggestion[suggestion_id]
    if not suggestion:
        flash.set(T("Suggestion not found"))
        redirect(URL("admin/suggestion/select"))

    # Get the related hackathon
    hackathon = db.hackathon[suggestion.hackathon_id]
    if not hackathon:
        flash.set(T("Hackathon not found"))
        redirect(URL("admin/suggestion/select"))


    return dict(suggestion=suggestion, hackathon=hackathon)


@action("admin/suggestion/<path:path>", method=["POST", "GET"])
@admin_only
def suggestion(path=None):
    search_queries = [["By Name", lambda value: db.suggestion.name.contains(value)], ]

    pre_action_buttons = [
        lambda row: GridActionButton(
            f"/admin/suggestions/{row.id}",
            "Accept", "fas fa-edit", name="grid-edit-button"
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

    return dict(grid=grid)
