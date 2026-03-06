from app import create_app, db
from app.models import User, Organization

app = create_app()

with app.app_context():
    # Check if demo user already exists
    demo_user = User.query.filter_by(email='demo@fruitqms.com').first()

    if demo_user:
        print("Demo user already exists!")
    else:
        # Create demo organization
        demo_org = Organization(
            name='Demo Packhouse',
            org_type='packhouse',
            ggn_number='4052852123456'
        )
        db.session.add(demo_org)
        db.session.commit()

        # Create demo user
        demo_user = User(
            name='QA Manager Demo',
            username='demo',
            email='demo@fruitqms.com',
            role='qa_manager',
            organization_id=demo_org.id
        )
        demo_user.set_password('demo123')
        db.session.add(demo_user)
        db.session.commit()

        print("✓ Demo user created successfully!")
        print("Email: demo@fruitqms.com")
        print("Password: demo123")
        print("Role: QA Manager")
