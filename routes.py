import datetime
from functools import wraps
import jwt
from flask import Blueprint, request, jsonify, current_app
from models import db, User, Expense

api_bp = Blueprint('api', __name__, url_prefix='/api')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Токен имеет неверный формат'}), 401

        if not token:
            return jsonify({'message': 'Токен отсутствует!'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'Пользователь не найден'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Срок действия токена истек!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Неверный токен!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password') or not data.get('password_confirm'):
        return jsonify({'message': 'Необходимо указать имя пользователя, пароль и его подтверждение'}), 400

    if data['password'] != data['password_confirm']:
        return jsonify({'message': 'Пароли не совпадают'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Пользователь с таким email уже существует'}), 400

    # Создание пользователя (по дефолту user)
    new_user = User(username=data['username'], email=data['email'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Новый пользователь создан!'}), 201


@api_bp.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Необходимо указать email и пароль'}), 401

    user = User.query.filter_by(email=auth['email']).first()
    if not user or not user.check_password(auth['password']):
        return jsonify({'message': 'Неверные учетные данные'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token, 'user': user.to_dict()})


@api_bp.route('/expenses', methods=['GET'])
@token_required
def get_expenses(current_user):
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return jsonify([e.to_dict() for e in expenses])


@api_bp.route('/expenses', methods=['POST'])
@token_required
def add_expense(current_user):
    data = request.get_json()
    required_fields = ['amount', 'category', 'date', 'transaction_type', 'currency']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'message': f'Отсутствуют необходимые поля: {", ".join(required_fields)}'}), 400

    try:
        date_obj = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Неверный формат даты. Используйте ГГГГ-ММ-ДД'}), 400

    new_expense = Expense(
        amount=data['amount'],
        category=data['category'],
        description=data.get('description', ''),
        date=date_obj,
        transaction_type=data['transaction_type'],
        currency=data['currency'],
        user_id=current_user.id
    )
    db.session.add(new_expense)
    db.session.commit()
    return jsonify({'message': 'Транзакция добавлена!', 'expense': new_expense.to_dict()}), 201


@api_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
@token_required
def update_expense(current_user, expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({'message': 'Транзакция не найдена'}), 404
    if expense.user_id != current_user.id:
        return jsonify({'message': 'Доступ запрещен'}), 403

    data = request.get_json()
    if 'amount' in data: expense.amount = data['amount']
    if 'category' in data: expense.category = data['category']
    if 'date' in data:
        try:
            expense.date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Неверный формат даты. Используйте ГГГГ-ММ-ДД'}), 400
    if 'description' in data: expense.description = data['description']
    if 'transaction_type' in data: expense.transaction_type = data['transaction_type']
    if 'currency' in data: expense.currency = data['currency']

    db.session.commit()
    return jsonify({'message': 'Транзакция обновлена!', 'expense': expense.to_dict()})


@api_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@token_required
def delete_expense(current_user, expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({'message': 'Транзакция не найдена'}), 404
    if expense.user_id != current_user.id:
        return jsonify({'message': 'Доступ запрещен'}), 403

    db.session.delete(expense)
    db.session.commit()
    return jsonify({'message': 'Транзакция удалена'})


@api_bp.route('/admin/users', methods=['GET'])
@token_required
def get_all_users(current_user):
    if not current_user.is_admin():
        return jsonify({'message': 'Доступ запрещен. Требуются права администратора.'}), 403
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@api_bp.route('/admin/expenses', methods=['GET'])
@token_required
def get_all_expenses(current_user):
    if not current_user.is_admin():
        return jsonify({'message': 'Доступ запрещен. Требуются права администратора.'}), 403
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return jsonify([e.to_dict() for e in expenses])


@api_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    if not current_user.is_admin():
        return jsonify({'message': 'Доступ запрещен. Требуются права администратора.'}), 403

    user_to_delete = User.query.get(user_id)
    if not user_to_delete:
        return jsonify({'message': 'Пользователь не найден'}), 404

    if user_to_delete.id == current_user.id:
        return jsonify({'message': 'Вы не можете удалить свой собственный аккаунт.'}), 400

    db.session.delete(user_to_delete)
    db.session.commit()
    return jsonify({'message': f'Пользователь {user_to_delete.username} и все его транзакции удалены.'})