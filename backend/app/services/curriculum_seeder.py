from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Course, Expense, User, SchoolEvent, Reward
from app.auth import hash_pin
from app.config import settings

async def seed_initial_data(db_session: AsyncSession):
    # Always sync teacher PIN with current ADMIN_PIN env var
    result = await db_session.execute(select(User).where(User.username == 'dad'))
    existing_dad = result.scalars().first()
    if existing_dad:
        existing_dad.pin_hash = hash_pin(settings.ADMIN_PIN)
        await db_session.commit()

    # Seed default Rewards if none exist
    result = await db_session.execute(select(Reward))
    if not result.scalars().first():
        rewards_data = [
            Reward(title="30 Min Screen Time", description="Play a video game or watch YouTube", xp_cost=50, emoji="🎮", category="Entertainment"),
            Reward(title="1 Hour Screen Time", description="Double the game time", xp_cost=90, emoji="🕹️", category="Entertainment"),
            Reward(title="Pick the Dinner", description="You get to choose what Dad cooks for dinner tonight", xp_cost=150, emoji="🍕", category="Privilege"),
            Reward(title="Stay Up 30 Mins Late", description="Push bedtime back by 30 minutes", xp_cost=100, emoji="🌙", category="Privilege"),
            Reward(title="Skip a Chore", description="Pass one of your daily chores to Dad", xp_cost=200, emoji="🧹", category="Privilege"),
            Reward(title="Special Treat", description="Ice cream or a special snack of your choice", xp_cost=75, emoji="🍦", category="Snack")
        ]
        db_session.add_all(rewards_data)
        await db_session.commit()

    # Check if courses already exist
    result = await db_session.execute(select(Course))
    if result.scalars().first():
        return  # Data already seeded
        
    # Seed Users
    dad = User(username='dad', display_name='Dad', role='teacher', pin_hash=hash_pin(settings.ADMIN_PIN))
    sonny = User(username='sonny', display_name='Sonny', role='student', pin_hash=None)
    db_session.add_all([dad, sonny])
    
    # Seed First Day Event
    first_day = SchoolEvent(
        title="First Day of School",
        event_date=date(2026, 8, 17),
        category="Academic",
        importance="Important"
    )
    db_session.add(first_day)
    
    # Seed Courses
    courses_data = [
        Course(title="Math — Beast Academy", subject_area="Math", platform="Beast Academy", platform_url="https://beastacademy.com/login", emoji="🧮", color_hex="#f59e0b", sort_order=1),
        Course(title="Language Arts — Brave Writer", subject_area="ELA", platform="Brave Writer", platform_url="https://bravewriter.com/", emoji="✍️", color_hex="#a78bfa", sort_order=2),
        Course(title="Social Studies — Tuttle Twins", subject_area="Social Studies", platform="Tuttle Twins", platform_url="https://tuttletwins.com/", emoji="🗺️", color_hex="#34d399", sort_order=3),
        Course(title="Critical Thinking — Critical Thinking Co.", subject_area="Logic", platform="Critical Thinking Co.", platform_url="https://www.criticalthinking.com/", emoji="🧠", color_hex="#f472b6", sort_order=4),
        Course(title="Logic — Brilliant.org", subject_area="Logic", platform="Brilliant.org", platform_url="https://brilliant.org/login", emoji="⚔️", color_hex="#60a5fa", sort_order=5),
        Course(title="Strategy — Synthesis", subject_area="Logic", platform="Synthesis", platform_url="https://www.synthesis.com/", emoji="🤖", color_hex="#c084fc", sort_order=6),
        Course(title="Strategy — Chess.com", subject_area="Logic", platform="Chess.com", platform_url="https://www.chess.com/login", emoji="♟️", color_hex="#fbbf24", sort_order=7),
        Course(title="STEM — CrunchLabs", subject_area="Science", platform="CrunchLabs", platform_url="https://www.crunchlabs.com/", emoji="🧪", color_hex="#fb923c", sort_order=8),
        Course(title="Electives — Outschool", subject_area="Science", platform="Outschool", platform_url="https://outschool.com/", emoji="🏫", color_hex="#38bdf8", sort_order=9)
    ]
    db_session.add_all(courses_data)
    
    # Seed default Expenses
    expenses_data = [
        Expense(item_name="Beast Academy Subscription", cost=150.0, category="Subscriptions", status="Approved & Direct Paid"),
        Expense(item_name="Brave Writer Curriculum", cost=200.0, category="Curriculum & Workbooks", status="Approved & Direct Paid"),
        Expense(item_name="Tuttle Twins Books", cost=90.0, category="Curriculum & Workbooks", status="Approved & Direct Paid"),
        Expense(item_name="Critical Thinking Co. Books", cost=80.0, category="Curriculum & Workbooks", status="Approved & Direct Paid"),
        Expense(item_name="Brilliant.org Subscription", cost=120.0, category="Subscriptions", status="Pending"),
        Expense(item_name="Synthesis Subscription", cost=250.0, category="Subscriptions", status="Pending"),
        Expense(item_name="CrunchLabs Build Box", cost=300.0, category="Supplies & Materials", status="Pending")
    ]
    db_session.add_all(expenses_data)
    
    await db_session.commit()
