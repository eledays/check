"""
Script to populate database with test projects of varying staleness for the mock user.
"""
import sys
import datetime
from pathlib import Path

# Add parent directory to path to import app
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models import User, Project, Task, ProjectPeriodicity, TaskStatus

def populate_test_data():
    """Populate database with test projects for mock user."""
    app = create_app()
    
    with app.app_context():
        # Get or create mock user
        mock_telegram_id = 123456789
        user = User.query.filter_by(telegram_id=mock_telegram_id).first()
        
        if not user:
            user = User(telegram_id=mock_telegram_id)
            db.session.add(user)
            db.session.commit()
            print(f"Created mock user with telegram_id: {mock_telegram_id}")
        else:
            print(f"Using existing mock user with telegram_id: {mock_telegram_id}")
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Define test projects with different staleness levels
        test_projects = [
            {
                "name": "Свежий проект",
                "short_name": "fresh",
                "description": "Активность была недавно",
                "periodicity": ProjectPeriodicity.WEEKLY,
                "days_ago": 1,  # Very fresh
                "tasks": [
                    {"title": "Недавняя задача", "completed_days_ago": 1}
                ]
            },
            {
                "name": "Почти свежий",
                "short_name": "almost",
                "description": "Чуть-чуть тускнеет (staleness ~0.4)",
                "periodicity": ProjectPeriodicity.WEEKLY,
                "days_ago": 3,  # 3 days out of 7 = 0.43
                "tasks": [
                    {"title": "Задача 3 дня назад", "completed_days_ago": 3}
                ]
            },
            {
                "name": "На пороге",
                "short_name": "threshold",
                "description": "Ровно на пороге периодичности (staleness ~1.0)",
                "periodicity": ProjectPeriodicity.WEEKLY,
                "days_ago": 7,  # Exactly at threshold
                "tasks": [
                    {"title": "Задача неделю назад", "completed_days_ago": 7}
                ]
            },
            {
                "name": "Слегка просрочен",
                "short_name": "overdue",
                "description": "Немного превысил периодичность (staleness ~1.3)",
                "periodicity": ProjectPeriodicity.WEEKLY,
                "days_ago": 9,
                "tasks": [
                    {"title": "Старая задача", "completed_days_ago": 9}
                ]
            },
            {
                "name": "Сильно просрочен",
                "short_name": "veryold",
                "description": "Давно не было активности (staleness ~2.0)",
                "periodicity": ProjectPeriodicity.WEEKLY,
                "days_ago": 14,
                "tasks": [
                    {"title": "Очень старая задача", "completed_days_ago": 14}
                ]
            },
            {
                "name": "Заброшенный проект",
                "short_name": "abandoned",
                "description": "Критически старый (staleness ~3.0)",
                "periodicity": ProjectPeriodicity.WEEKLY,
                "days_ago": 21,
                "tasks": [
                    {"title": "Древняя задача", "completed_days_ago": 21}
                ]
            },
            {
                "name": "Ежедневный проект",
                "short_name": "daily",
                "description": "Требует ежедневного внимания, не обновлялся 2 дня",
                "periodicity": ProjectPeriodicity.DAILY,
                "days_ago": 2,  # staleness = 2.0 for daily
                "tasks": [
                    {"title": "Вчерашняя задача", "completed_days_ago": 2}
                ]
            },
            {
                "name": "Месячный проект",
                "short_name": "monthly",
                "description": "Обновляется раз в месяц, прошло 15 дней",
                "periodicity": ProjectPeriodicity.MONTHLY,
                "days_ago": 15,  # staleness = 0.5 for monthly
                "tasks": [
                    {"title": "Задача 2 недели назад", "completed_days_ago": 15}
                ]
            },
            {
                "name": "Квартальный проект",
                "short_name": "quarterly",
                "description": "Обновляется раз в квартал, прошло 45 дней",
                "periodicity": ProjectPeriodicity.QUARTERLY,
                "days_ago": 45,  # staleness = 0.5 for quarterly
                "tasks": [
                    {"title": "Задача полтора месяца назад", "completed_days_ago": 45}
                ]
            },
            {
                "name": "Проект без задач",
                "short_name": "notasks",
                "description": "Только создан, задач нет",
                "periodicity": ProjectPeriodicity.WEEKLY,
                "days_ago": 5,
                "tasks": []
            },
        ]
        
        created_count = 0
        for proj_data in test_projects:
            # Check if project already exists
            existing = Project.query.filter_by(
                short_name=proj_data["short_name"],
                creator_id=user.id
            ).first()
            
            if existing:
                print(f"Project '{proj_data['name']}' already exists, skipping...")
                continue
            
            # Create project
            project = Project(
                name=proj_data["name"],
                short_name=proj_data["short_name"],
                description=proj_data["description"],
                periodicity=proj_data["periodicity"],
                creator_id=user.id
            )
            
            # Set created_at and updated_at to simulate old project
            old_date = now - datetime.timedelta(days=proj_data["days_ago"])
            project.created_at = old_date
            project.updated_at = old_date
            
            db.session.add(project)
            db.session.flush()  # Get project.id
            
            # Create tasks
            for task_data in proj_data["tasks"]:
                task = Task(
                    title=task_data["title"],
                    status=TaskStatus.DONE,
                    project_id=project.id,
                    order=0
                )
                
                completed_date = now - datetime.timedelta(days=task_data["completed_days_ago"])
                task.created_at = completed_date
                task.updated_at = completed_date
                task.completed_at = completed_date
                
                db.session.add(task)
            
            created_count += 1
            print(f"✓ Created project: {proj_data['name']} (staleness ~{proj_data['days_ago'] / 7:.1f})")
        
        db.session.commit()
        print(f"\n✅ Successfully created {created_count} test projects!")
        print(f"Total projects for mock user: {Project.query.filter_by(creator_id=user.id).count()}")


if __name__ == "__main__":
    populate_test_data()
