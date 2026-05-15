from flask import Blueprint, request
from app.utils import success, created, error, not_found
from app.utils.auth_decorators import login_required, admin_required, current_user
from app.models import Course, CourseModule, CourseSession, CourseEnrollment, ModuleProgress
from app.extensions import db

formation_bp = Blueprint("formation", __name__, url_prefix="/api/v1/formation")


@formation_bp.route("", methods=["GET"])
def get_formation_page():
    course = Course.query.filter_by(is_active=True).first()
    if not course:
        return not_found("Aucun cours disponible.")
    modules = course.modules.all()
    testimonials = course.testimonials.filter_by(is_published=True).limit(10).all()
    next_session = (
        CourseSession.query
        .filter_by(course_id=course.id, status="open")
        .order_by(CourseSession.start_date)
        .first()
    )
    return success({
        "course": course.to_dict(),
        "modules": [m.to_dict() for m in modules],
        "testimonials": [t.to_dict() for t in testimonials],
        "next_session": next_session.to_dict() if next_session else None,
    })


@formation_bp.route("/modules/<int:module_id>/preview", methods=["GET"])
def module_preview(module_id):
    module = CourseModule.query.get_or_404(module_id)
    if not module.is_preview:
        return error("Ce module n'est pas en accès libre.", 403)
    return success(module.to_dict(include_content=True))


@formation_bp.route("/sessions/active", methods=["GET"])
def active_sessions():
    sessions = CourseSession.query.filter_by(status="open").order_by(CourseSession.start_date).all()
    return success([s.to_dict() for s in sessions])


@formation_bp.route("/sessions/<int:session_id>/enroll", methods=["POST"])
@login_required
def enroll(session_id):
    session = CourseSession.query.get_or_404(session_id)
    if session.status not in ("open",):
        return error("Cette session n'accepte plus d'inscriptions.")
    data = request.get_json(silent=True) or {}
    u = current_user()
    existing = CourseEnrollment.query.filter_by(course_session_id=session_id, user_id=u.id).first()
    if existing:
        return error("Vous êtes déjà inscrit à cette session.", 409)
    enrollment = CourseEnrollment(
        course_session_id=session_id,
        user_id=u.id,
        full_name=data.get("full_name", u.full_name),
        email=data.get("email", u.email),
        whatsapp=data.get("whatsapp", u.whatsapp),
        country_code=data.get("country_code", getattr(u, "country_code", None)),
        city=data.get("city", u.city),
        objective=data.get("objective"),
    )
    db.session.add(enrollment)
    session.current_seats += 1
    if session.max_seats and session.current_seats >= session.max_seats:
        session.status = "full"
    db.session.commit()
    return created(enrollment.to_dict(), "Inscription enregistrée.")


@formation_bp.route("/me", methods=["GET"])
@login_required
def my_dashboard():
    u = current_user()
    enrollment = (
        CourseEnrollment.query
        .filter_by(user_id=u.id)
        .order_by(CourseEnrollment.enrolled_at.desc())
        .first()
    )
    if not enrollment:
        return success({"enrolled": False})
    progress = enrollment.progress.all()
    session_obj = CourseSession.query.get(enrollment.course_session_id)
    return success({
        "enrollment": enrollment.to_dict(),
        "session": session_obj.to_dict() if session_obj else None,
        "progress": [p.to_dict() for p in progress],
    })


@formation_bp.route("/me/modules", methods=["GET"])
@login_required
def my_modules():
    u = current_user()
    enrollment = CourseEnrollment.query.filter_by(user_id=u.id).order_by(CourseEnrollment.enrolled_at.desc()).first()
    if not enrollment:
        return error("Aucune inscription trouvée.", 404)
    progress = {p.module_id: p for p in enrollment.progress.all()}
    course = CourseSession.query.get(enrollment.course_session_id).course
    modules = course.modules.all()
    result = []
    for m in modules:
        d = m.to_dict()
        p = progress.get(m.id)
        d["status"] = p.status if p else "todo"
        result.append(d)
    return success(result)


@formation_bp.route("/me/modules/<int:module_id>/start", methods=["POST"])
@login_required
def start_module(module_id):
    from datetime import datetime
    u = current_user()
    enrollment = CourseEnrollment.query.filter_by(user_id=u.id).order_by(CourseEnrollment.enrolled_at.desc()).first()
    if not enrollment:
        return error("Aucune inscription trouvée.", 404)
    prog = ModuleProgress.query.filter_by(enrollment_id=enrollment.id, module_id=module_id).first()
    if not prog:
        prog = ModuleProgress(enrollment_id=enrollment.id, module_id=module_id)
        db.session.add(prog)
    prog.status = "in_progress"
    prog.started_at = prog.started_at or datetime.utcnow()
    db.session.commit()
    return success(prog.to_dict(), "Module démarré.")


@formation_bp.route("/me/modules/<int:module_id>/complete", methods=["POST"])
@login_required
def complete_module(module_id):
    from datetime import datetime
    u = current_user()
    enrollment = CourseEnrollment.query.filter_by(user_id=u.id).order_by(CourseEnrollment.enrolled_at.desc()).first()
    if not enrollment:
        return error("Aucune inscription trouvée.", 404)
    prog = ModuleProgress.query.filter_by(enrollment_id=enrollment.id, module_id=module_id).first()
    if not prog:
        prog = ModuleProgress(enrollment_id=enrollment.id, module_id=module_id)
        db.session.add(prog)
    prog.status = "done"
    prog.completed_at = datetime.utcnow()
    db.session.commit()
    return success(prog.to_dict(), "Module complété.")


@formation_bp.route("/admin/enrollments", methods=["GET"])
@admin_required
def admin_enrollments():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    paginated = CourseEnrollment.query.order_by(CourseEnrollment.enrolled_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return success({
        "items": [e.to_dict() for e in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages,
    })
