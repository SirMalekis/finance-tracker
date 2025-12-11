from flask import Flask, render_template
from models import db, User
from routes import api_bp
from config import Config

def create_app():
    """Фабрика приложений"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация расширений
    db.init_app(app)

    # Регистрация API Blueprint
    app.register_blueprint(api_bp)

    # Главный маршрут, отдает HTML-файл
    @app.route('/')
    def index():
        return render_template('index.html')

    # Команда для инициализации БД и создания админа
    @app.cli.command("init-db")
    def init_db_command():
        """Создает таблицы в базе данных и админа по умолчанию."""
        with app.app_context():
            db.create_all()
            if User.query.filter_by(email='admin@example.com').first() is None:
                admin = User(username='admin', email='admin@example.com', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print('База данных инициализирована. Создан администратор: admin@example.com / admin123')
            else:
                print('База данных уже инициализирована.')
        return 0

    return app

# --- ЭТО ГЛАВНОЕ ИЗМЕНЕНИЕ ---
# Создаем экземпляр приложения на уровне модуля, чтобы его нашел Gunicorn
app = create_app()

# Этот блок оставляем для локального запуска без Docker
if __name__ == '__main__':
    app.run(debug=True)