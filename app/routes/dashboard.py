from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app import db
from app.models import Organization, Grower, ControlPoint, SetupWizard, Notification
import json

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    org = current_user.organization if current_user.organization else None

    # --- Setup progress ---
    wizard = SetupWizard.query.filter_by(user_id=current_user.id).order_by(SetupWizard.id.desc()).first()
    setup_complete = wizard.completed if wizard else False
    setup_step = wizard.current_step if wizard else 0

    setup_tasks = [
        {'label': _('Business type & audit scope'), 'done': setup_step > 1 or setup_complete},
        {'label': _('Packhouse details'), 'done': setup_step > 2 or setup_complete},
        {'label': _('Farm & field details'), 'done': setup_step > 3 or setup_complete},
        {'label': _('Environment & compliance'), 'done': setup_step > 4 or setup_complete},
        {'label': _('GLOBALG.A.P. analysis'), 'done': setup_step > 5 or setup_complete},
        {'label': _('Policy generation'), 'done': setup_step > 6 or setup_complete},
        {'label': _('Review & complete'), 'done': setup_complete},
    ]

    # --- Growers ---
    growers = []
    grower_count = 0
    if org:
        growers = Grower.query.filter_by(organization_id=org.id, is_active=True).all()
        grower_count = len(growers)

    # --- Control point compliance ---
    control_points = []
    cp_total = 0
    cp_compliant = 0
    cp_non_compliant = 0
    cp_not_addressed = 0
    compliance_percent = 0

    outstanding_major = []
    outstanding_minor = []
    recently_completed = []

    if org:
        control_points = ControlPoint.query.filter_by(organization_id=org.id).all()
        cp_total = len(control_points)

        for cp in control_points:
            if cp.compliance_status == 'Compliant':
                cp_compliant += 1
                recently_completed.append(cp)
            elif cp.compliance_status == 'Non-compliant':
                cp_non_compliant += 1
                if 'Major' in (cp.criticality or ''):
                    outstanding_major.append(cp)
                else:
                    outstanding_minor.append(cp)
            else:
                cp_not_addressed += 1
                if 'Major' in (cp.criticality or ''):
                    outstanding_major.append(cp)
                else:
                    outstanding_minor.append(cp)

        if cp_total > 0:
            compliance_percent = int((cp_compliant / cp_total) * 100)

    # Sort recently completed by updated_at descending, limit to 10
    recently_completed.sort(key=lambda c: c.updated_at or c.created_at, reverse=True)
    recently_completed = recently_completed[:10]

    # Limit outstanding lists
    outstanding_major = outstanding_major[:15]
    outstanding_minor = outstanding_minor[:15]

    # --- To-do items (actionable next steps) ---
    todo_items = []
    if not setup_complete:
        todo_items.append({
            'text': _('Complete Setup Wizard (currently on step %(step)d)', step=setup_step),
            'link': f'/wizard/step{setup_step}',
            'priority': 'high'
        })
    if setup_complete and grower_count == 0 and org and org.org_type != 'grower':
        todo_items.append({
            'text': _('Add your first grower'),
            'link': '/setup/settings#growers',
            'priority': 'high'
        })
    if cp_total > 0 and cp_not_addressed > 0:
        todo_items.append({
            'text': _('Address %(count)d unreviewed control points', count=cp_not_addressed),
            'link': '/setup/settings#globalgap',
            'priority': 'high' if cp_not_addressed > cp_total * 0.5 else 'medium'
        })
    if cp_non_compliant > 0:
        todo_items.append({
            'text': _('Resolve %(count)d non-compliant control points', count=cp_non_compliant),
            'link': '/setup/settings#globalgap',
            'priority': 'high'
        })
    if setup_complete and cp_total == 0:
        todo_items.append({
            'text': _('Import GLOBALG.A.P. control points checklist'),
            'link': '/setup/settings#globalgap',
            'priority': 'medium'
        })

    # --- Auto-generate notifications for reminders ---
    _generate_reminders(current_user, org, setup_complete, setup_step, cp_non_compliant, cp_not_addressed)

    # --- Map data ---
    map_data = {
        'packhouse': None,
        'growers': []
    }

    if org and org.latitude and org.longitude:
        crops = json.loads(org.crops_packed) if org.crops_packed else []
        map_data['packhouse'] = {
            'name': org.name,
            'lat': org.latitude,
            'lng': org.longitude,
            'ggn': org.ggn_number or 'N/A',
            'crops': ', '.join([c.title() for c in crops]) if crops else 'Various',
            'compliance': f"{compliance_percent}%" if cp_total > 0 else 'N/A'
        }

    for grower in growers:
        if grower.gps_coordinates:
            try:
                lat, lng = grower.gps_coordinates.split(',')
                map_data['growers'].append({
                    'name': grower.grower_name,
                    'code': grower.grower_code,
                    'lat': float(lat.strip()),
                    'lng': float(lng.strip()),
                    'crop': grower.crop_type or 'N/A',
                    'size': grower.size_hectares or 0
                })
            except (ValueError, AttributeError):
                pass

    return render_template('dashboard/dashboard.html',
        org=org,
        setup_complete=setup_complete,
        setup_step=setup_step,
        setup_tasks=setup_tasks,
        todo_items=todo_items,
        grower_count=grower_count,
        cp_total=cp_total,
        cp_compliant=cp_compliant,
        cp_non_compliant=cp_non_compliant,
        cp_not_addressed=cp_not_addressed,
        compliance_percent=compliance_percent,
        outstanding_major=outstanding_major,
        outstanding_minor=outstanding_minor,
        recently_completed=recently_completed,
        map_data=json.dumps(map_data)
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

@dashboard_bp.route('/notifications')
@login_required
def notifications():
    """View all notifications"""
    page = request.args.get('page', 1, type=int)
    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    # Mark all as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()

    return render_template('dashboard/notifications.html', notifications=notifs)


@dashboard_bp.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    """Clear all notifications"""
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash(_('All notifications cleared.'), 'info')
    return redirect(url_for('dashboard.notifications'))


def _generate_reminders(user, org, setup_complete, setup_step, non_compliant_count, not_addressed_count):
    """Generate automatic reminder notifications (idempotent - checks for duplicates)"""
    from datetime import datetime, timedelta

    if not org:
        return

    today = datetime.utcnow().date()

    def _create_if_not_exists(title, message, category='info', link=None):
        """Create notification only if no similar one exists today"""
        existing = Notification.query.filter(
            Notification.user_id == user.id,
            Notification.title == title,
            Notification.created_at >= datetime(today.year, today.month, today.day)
        ).first()
        if not existing:
            notif = Notification(
                user_id=user.id,
                organization_id=org.id,
                title=title,
                message=message,
                category=category,
                link=link
            )
            db.session.add(notif)

    # Reminder: Complete setup wizard
    if not setup_complete:
        _create_if_not_exists(
            _('Complete Setup Wizard'),
            _('You are on step %(step)d of 7. Complete the wizard to unlock all features.', step=setup_step),
            category='warning',
            link=f'/wizard/step{setup_step}'
        )

    # Reminder: Non-compliant control points
    if non_compliant_count > 0:
        _create_if_not_exists(
            _('Non-Compliant Control Points'),
            _('You have %(count)d non-compliant control points that need attention.', count=non_compliant_count),
            category='danger',
            link='/setup/settings#globalgap'
        )

    # Reminder: Unreviewed control points
    if not_addressed_count > 20:
        _create_if_not_exists(
            _('Unreviewed Control Points'),
            _('%(count)d control points have not been reviewed yet.', count=not_addressed_count),
            category='warning',
            link='/setup/settings#globalgap'
        )

    db.session.commit()
